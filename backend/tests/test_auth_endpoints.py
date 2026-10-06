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

Cobertura extra (Fase 1, gate 80%): ramas del callback sin probar —
origin extraído del state (redirect_to absoluto), redirect cross-origin
con token por query param, SUPERADMIN → /dashboard, error de exchange,
email ausente, cuenta bloqueada, cuenta inactiva (comportamiento real,
bug reportado), excepción genérica y state con JSON inválido. Más tests
unitarios directos de `_get_frontend_redirect`.
"""
import json
import re
import pytest
from datetime import timedelta
from urllib.parse import unquote_plus
from fastapi import status
from sqlalchemy import select
# Importamos la herramienta de hashing real para evitar hardcoding de hashes
from app.main import app
from app.api.v1.dependencies import get_auth_service
from app.api.v1.endpoints.auth.google import FRONTEND_URL, _get_frontend_redirect
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

    async def test_google_callback_superadmin_goes_to_dashboard(
        self, client, db_session, mock_google_exchange
    ):
        """SUPERADMIN en el frontend de authCore → redirect directo a /dashboard."""
        mock_google_exchange({"email": "root@example.com", "name": "Root"})
        db_session.add(
            User(
                username="root",
                email="root@example.com",
                full_name="Root",
                password_hash=get_password_hash("testpass"),
                role=UserRole.SUPERADMIN,
                status=UserStatus.ACTIVE,
                is_active=True,
                is_locked=False,
            )
        )
        await db_session.commit()

        response = await client.get("/api/v1/auth/callback?code=test_code")

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert response.headers["location"] == f"{FRONTEND_URL}/dashboard"
        assert "access_token=" in response.headers.get("set-cookie", "")

    async def test_google_callback_cross_origin_keeps_redirect_and_updates_origin(
        self, client, db_session, test_user, mock_google_exchange
    ):
        """redirect_to absoluto de otro dominio → se conserva y el token viaja
        por query param; el origin extraído del host ("www.rincom.es" →
        "rincom") se persiste en el usuario.
        """
        mock_google_exchange({"email": "test@example.com", "name": "Test User"})
        db_session.add(test_user)
        await db_session.commit()

        state = json.dumps({"redirect_to": "https://www.rincom.es/ofertas"})
        response = await client.get(
            "/api/v1/auth/callback", params={"code": "test_code", "state": state}
        )

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        location = response.headers["location"]
        assert location.startswith("https://www.rincom.es/ofertas?token=")
        assert "access_token=" in response.headers.get("set-cookie", "")

        # AuthService actualiza user.origin con el dominio de origen
        result = await db_session.execute(
            select(User).where(User.email == "test@example.com")
        )
        user = result.scalar_one()
        await db_session.refresh(user)
        assert user.origin == "rincom"

    async def test_google_callback_userinfo_without_email(
        self, client, mock_google_exchange
    ):
        """Google devuelve userinfo sin email → 400 → /login?error=..."""
        mock_google_exchange({"name": "Sin Email"})

        response = await client.get("/api/v1/auth/callback?code=test_code")

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        location = response.headers["location"]
        assert location.startswith(f"{FRONTEND_URL}/login?error=")
        assert "No se pudo obtener email de Google" in unquote_plus(location)

    async def test_google_callback_locked_user(
        self, client, db_session, mock_google_exchange
    ):
        """Usuario existente bloqueado → 403 del servicio → /login?error=."""
        mock_google_exchange({"email": "locked@example.com", "name": "Locked"})
        db_session.add(
            User(
                username="locked",
                email="locked@example.com",
                full_name="Locked",
                password_hash=get_password_hash("testpass"),
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                is_active=True,
                is_locked=True,
            )
        )
        await db_session.commit()

        response = await client.get("/api/v1/auth/callback?code=test_code")

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        location = response.headers["location"]
        assert location.startswith(f"{FRONTEND_URL}/login?error=")
        assert "Cuenta bloqueada" in unquote_plus(location)
        assert "access_token" not in response.headers.get("set-cookie", "")

    async def test_google_callback_inactive_user_still_gets_token(
        self, client, db_session, mock_google_exchange
    ):
        """Documenta el comportamiento REAL (bug de prod reportado, no fixeado):
        `process_google_login` solo valida status==PENDING e is_locked — un
        usuario desactivado (is_active=False, status=INACTIVE) recibe token
        igual que uno activo.
        """
        mock_google_exchange({"email": "inactive@example.com", "name": "Inactivo"})
        db_session.add(
            User(
                username="inactive",
                email="inactive@example.com",
                full_name="Inactivo",
                password_hash=get_password_hash("testpass"),
                role=UserRole.USER,
                status=UserStatus.INACTIVE,
                is_active=False,
                is_locked=False,
            )
        )
        await db_session.commit()

        response = await client.get("/api/v1/auth/callback?code=test_code")

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert response.headers["location"].endswith("/select-tenant")
        assert "access_token=" in response.headers.get("set-cookie", "")

    async def test_google_callback_exchange_failure(self, client, monkeypatch):
        """exchange_code revienta → AuthService lo envuelve en 400 → error redirect."""
        from app.services.auth.GoogleOAuthService import GoogleOAuthService

        async def _boom(self, code, redirect_uri):
            raise RuntimeError("sin red")

        monkeypatch.setattr(GoogleOAuthService, "exchange_code", _boom)

        response = await client.get("/api/v1/auth/callback?code=test_code")

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        location = response.headers["location"]
        assert location.startswith(f"{FRONTEND_URL}/login?error=")
        assert "Error en Google OAuth" in unquote_plus(location)

    async def test_google_callback_unexpected_error(self, client):
        """Excepción NO-HTTPException fuera del servicio → el handler genérico
        del callback responde /login?error=Error técnico..."""
        class _BoomAuthService:
            async def process_google_login(self, code, redirect_uri, origin=None):
                raise ValueError("boom")

        app.dependency_overrides[get_auth_service] = lambda: _BoomAuthService()
        try:
            response = await client.get("/api/v1/auth/callback?code=test_code")
        finally:
            app.dependency_overrides.pop(get_auth_service, None)

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        location = response.headers["location"]
        assert location.startswith(f"{FRONTEND_URL}/login?error=")
        assert "Error técnico al procesar el login" in unquote_plus(location)

    async def test_google_callback_invalid_state_json(
        self, client, db_session, test_user, mock_google_exchange
    ):
        """state con JSON inválido → origin ignorado y destino por defecto
        (usuario normal en authCore → /select-tenant)."""
        mock_google_exchange({"email": "test@example.com", "name": "Test User"})
        db_session.add(test_user)
        await db_session.commit()

        response = await client.get(
            "/api/v1/auth/callback",
            params={"code": "test_code", "state": "not-json"},
        )

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert response.headers["location"].endswith("/select-tenant")

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


class TestGetFrontendRedirect:
    """Tests unitarios de `_get_frontend_redirect` (destino post-login)."""

    async def test_empty_state_uses_default(self):
        assert _get_frontend_redirect("") == f"{FRONTEND_URL}/dashboard"

    async def test_missing_redirect_to_uses_default(self):
        assert _get_frontend_redirect(json.dumps({})) == (
            f"{FRONTEND_URL}/dashboard"
        )

    async def test_empty_redirect_to_uses_default(self):
        state = json.dumps({"redirect_to": ""})
        assert _get_frontend_redirect(state) == f"{FRONTEND_URL}/dashboard"

    async def test_relative_redirect_is_prefixed(self):
        state = json.dumps({"redirect_to": "/settings"})
        assert _get_frontend_redirect(state) == f"{FRONTEND_URL}/settings"

    async def test_absolute_https_redirect_kept(self):
        state = json.dumps({"redirect_to": "https://otro.es/pagina"})
        assert _get_frontend_redirect(state) == "https://otro.es/pagina"

    async def test_absolute_http_redirect_kept(self):
        state = json.dumps({"redirect_to": "http://otro.es/pagina"})
        assert _get_frontend_redirect(state) == "http://otro.es/pagina"

    async def test_invalid_json_uses_default(self):
        assert _get_frontend_redirect("not-json") == f"{FRONTEND_URL}/dashboard"


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
