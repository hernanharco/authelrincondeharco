"""
Tests para endpoints de autenticación.
Cubren login tradicional, Google OAuth y gestión de tokens.
Async: usa httpx.AsyncClient + SQLAlchemy async.

Deriva vs la suite original (Fase 1):
- `test_google_callback_success` (issue #8) reescrito contra el flujo actual:
  el callback responde redirect 307 al frontend con cookie httpOnly
  `access_token` para usuarios existentes activos (sin postMessage); los
  usuarios NUEVOS quedan PENDING (sin auto-aprobación) y se redirigen a
  /login?status=pending SIN cookie (nuevo test con la misma fixture mock).
- El fixture viejo `mock_google_oauth` parcheaba `GoogleOAuthService.get_user_info`
  (firma muerta: ahora `get_user_info(token)`); ahora se parchea
  `exchange_code(code, redirect_uri)` — Authorization Code Flow, sin red.
- Comportamiento real de /login: responde JSON con `access_token` y NO setea
  cookie (la cookie httpOnly solo la pone el callback de Google). Se codifica
  el JSON; la cookie se valida en el callback.
- Nuevo test de rate limit: /login es 10/minute (slowapi); el override de
  conftest (`disable_rate_limiter`) debe impedir el 429 en la suite.
"""
import re
import pytest
from datetime import timedelta
from fastapi import status
from sqlalchemy import select
# Importamos la herramienta de hashing real para evitar hardcoding de hashes
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.schemas.auth import LoginRequest
from app.models.user import User, UserRole, UserStatus

pytestmark = pytest.mark.asyncio


class TestAuthEndpoints:
    """Tests para endpoints de autenticación"""

    async def test_login_success(self, client, db_session, test_user):
        """Test login exitoso con credenciales válidas"""
        db_session.add(test_user)
        await db_session.commit()

        login_data = LoginRequest(username="testuser", password="testpass")
        response = await client.post("/api/v1/auth/login", json=login_data.model_dump())

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "testuser"

    async def test_login_invalid_credentials(self, client, db_session, test_user):
        """Test login con credenciales inválidas"""
        db_session.add(test_user)
        await db_session.commit()

        login_data = LoginRequest(username="testuser", password="wrongpass")
        response = await client.post("/api/v1/auth/login", json=login_data.model_dump())

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Credenciales incorrectas"

    async def test_login_user_not_found(self, client):
        """Test login con usuario que no existe"""
        login_data = LoginRequest(username="nonexistent", password="anypass")
        response = await client.post("/api/v1/auth/login", json=login_data.model_dump())

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_repeated_logins_do_not_rate_limit(self, client, db_session, test_user):
        """/login está limitado a 10/minute (slowapi).

        El fixture autouse `disable_rate_limiter` de conftest desactiva el
        limiter en tests: más de 10 logins seguidos NO deben responder 429.
        """
        db_session.add(test_user)
        await db_session.commit()

        login_data = LoginRequest(username="testuser", password="testpass")
        for _ in range(12):
            response = await client.post(
                "/api/v1/auth/login", json=login_data.model_dump()
            )
            assert response.status_code == status.HTTP_200_OK, response.text

    async def test_google_oauth_redirect(self, client):
        """Test que Google OAuth redirige correctamente"""
        response = await client.get("/api/v1/auth/google", follow_redirects=False)

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert "accounts.google.com" in response.headers["location"]

    async def test_google_callback_success(
        self, client, db_session, test_user, mock_google_exchange
    ):
        """Callback de Google con usuario existente y ACTIVO (issue #8, flujo nuevo).

        Flujo actual: 307 al frontend (usuario normal → /select-tenant) con
        cookie httpOnly `access_token` (Max-Age = expires_in del token JWT).
        """
        mock_google_exchange(
            {"email": "test@example.com", "name": "Test User"}
        )
        db_session.add(test_user)
        await db_session.commit()

        response = await client.get("/api/v1/auth/callback?code=test_code")

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        # Usuario NO superadmin en authCore frontend → select-tenant
        assert response.headers["location"].endswith("/select-tenant")

        set_cookie = response.headers.get("set-cookie", "")
        assert "access_token=" in set_cookie
        assert "httponly" in set_cookie.lower()
        match = re.search(r"max-age=(\d+)", set_cookie, re.IGNORECASE)
        assert match is not None
        # max_age = expires_in del token (ACCESS_TOKEN_EXPIRE_MINUTES, 120 min)
        assert 0 < int(match.group(1)) <= settings.access_token_expire_minutes * 60

    async def test_google_callback_new_user_pending(
        self, client, db_session, mock_google_exchange
    ):
        """Usuario nuevo vía Google → PENDING sin auto-aprobación.

        El usuario se crea con role=NONE, status=PENDING, is_active=False,
        NO se emite token ni cookie, y se redirige a /login?status=pending.
        """
        mock_google_exchange(
            {"email": "newuser@example.com", "name": "New User"}
        )

        response = await client.get("/api/v1/auth/callback?code=new_code")

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert response.headers["location"].endswith("/login?status=pending")
        # Sin cookie de sesión para usuarios pendientes
        assert "access_token" not in response.headers.get("set-cookie", "")

        # El usuario queda persistido como pendiente (no aprobado)
        result = await db_session.execute(
            select(User).where(User.email == "newuser@example.com")
        )
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.status == UserStatus.PENDING
        assert user.role == UserRole.NONE
        assert user.is_active is False

    async def test_protected_endpoint_without_token(self, client):
        """Test acceso a endpoint protegido sin token"""
        response = await client.get("/api/v1/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_protected_endpoint_with_expired_token(self, client, db_session, test_user):
        """Test acceso con token expirado"""
        db_session.add(test_user)
        await db_session.commit()

        # Creamos un token con tiempo en el pasado
        expired_token = create_access_token(
            subject=str(test_user.id),
            expires_delta=timedelta(hours=-1)
        )
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = await client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- FIXTURES ---

@pytest.fixture
def test_user():
    """
    Usuario de prueba. 
    Usamos get_password_hash para que GitGuardian no detecte un hash hardcodeado.
    """
    return User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        # Generamos el hash de "testpass" dinámicamente
        password_hash=get_password_hash("testpass"),
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        is_active=True,
        is_locked=False
    )


@pytest.fixture
def mock_google_exchange(monkeypatch):
    """Instala un mock de GoogleOAuthService.exchange_code (sin red).

    Uso: `mock_google_exchange({"email": ..., "name": ...})`.
    Se parcha la CLASE con un método que recibe `self` (binding normal).
    """
    from app.services.auth.GoogleOAuthService import GoogleOAuthService

    def _install(userinfo: dict):
        async def _exchange(self, code, redirect_uri):
            return userinfo

        monkeypatch.setattr(GoogleOAuthService, "exchange_code", _exchange)

    return _install
