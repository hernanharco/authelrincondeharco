"""
Tests del flujo de aprobación manual (decisión A4) — visibilidad al usuario.

Cubre los dos huecos que ocultaban el estado "pending":

1. Login por contraseña: usuario existente + inactivo + contraseña correcta →
   403 {"detail": "PENDING_APPROVAL"} (mismo body que el flujo Google), mientras
   que contraseña incorrecta o usuario desconocido siguen respondiendo
   401 {"detail": "Credenciales incorrectas"} (contrato intacto).

2. Callback de Google: cuando el flujo vino de un spoke (state con
   redirect_to cross-origin a un origen distinto de FRONTEND_URL), los
   redirects de pending/error van a ESE redirect_to conservando la query que
   el spoke entiende (?status=pending / ?error=...), sin token. Sin
   redirect_to (o same-origin) se mantiene el destino histórico:
   FRONTEND_URL/login.

Patrones de fixtures tomados de tests/test_auth_endpoints.py (solo lectura).
"""
import json

import pytest
from fastapi import status
from urllib.parse import unquote_plus

from app.api.v1.endpoints.auth.google import FRONTEND_URL
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.auth import LoginRequest
from app.types.enums import UserRole, UserStatus

pytestmark = pytest.mark.asyncio

PASSWORD = "testpass"
# Origen de un spoke (distinto de FRONTEND_URL) para redirect_to cross-origin
SPOKE_URL = "https://www.rincom.es/ofertas"


# ── Fixtures ───────────────────────────────────────────────────

@pytest.fixture
def pending_user() -> User:
    """Usuario existente pendiente de aprobación (is_active=False)."""
    return User(
        username="pendinguser",
        email="pending@example.com",
        full_name="Pending User",
        password_hash=get_password_hash(PASSWORD),
        role=UserRole.NONE,
        status=UserStatus.PENDING,
        is_active=False,
        is_locked=False,
    )


@pytest.fixture
def active_user() -> User:
    """Usuario existente y activo (para el caso de contraseña incorrecta)."""
    return User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        password_hash=get_password_hash(PASSWORD),
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        is_active=True,
        is_locked=False,
    )


@pytest.fixture
def mock_google_exchange(monkeypatch):
    """Instala un mock de GoogleOAuthService.exchange_code (sin red)."""
    from app.services.auth.GoogleOAuthService import GoogleOAuthService

    def _install(userinfo: dict):
        async def _exchange(self, code, redirect_uri):
            return userinfo

        monkeypatch.setattr(GoogleOAuthService, "exchange_code", _exchange)

    return _install


# ── Gap 1: login por contraseña ────────────────────────────────

class TestPasswordLoginPendingApproval:
    async def test_pending_user_with_correct_password_returns_403(
        self, client, db_session, pending_user
    ):
        """Usuario existente + inactivo + contraseña correcta → 403 PENDING_APPROVAL."""
        db_session.add(pending_user)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/login",
            json=LoginRequest(username="pendinguser", password=PASSWORD).model_dump(),
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {"detail": "PENDING_APPROVAL"}
        # Sin cookie de sesión para usuarios pendientes
        assert "set-cookie" not in response.headers

    async def test_wrong_password_returns_401_unchanged(
        self, client, db_session, active_user
    ):
        """Contraseña incorrecta → 401 Credenciales incorrectas (contrato intacto)."""
        db_session.add(active_user)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/login",
            json=LoginRequest(username="testuser", password="wrongpass").model_dump(),
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {"detail": "Credenciales incorrectas"}
        assert "set-cookie" not in response.headers

    async def test_wrong_password_on_pending_user_returns_401_not_403(
        self, client, db_session, pending_user
    ):
        """Pendiente + contraseña incorrecta → sigue siendo 401 (no filtra existencia)."""
        db_session.add(pending_user)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/login",
            json=LoginRequest(username="pendinguser", password="wrongpass").model_dump(),
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {"detail": "Credenciales incorrectas"}

    async def test_unknown_user_returns_401_unchanged(self, client):
        """Usuario inexistente → 401 Credenciales incorrectas (contrato intacto)."""
        response = await client.post(
            "/api/v1/auth/login",
            json=LoginRequest(username="nonexistent", password="anypassword").model_dump(),
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {"detail": "Credenciales incorrectas"}


# ── Gap 2: pending/error del callback de Google ────────────────

class TestGoogleCallbackPendingRedirectToSpoke:
    async def test_pending_cross_origin_redirects_to_spoke_without_token(
        self, client, db_session, pending_user, mock_google_exchange
    ):
        """Pendiente + redirect_to cross-origin → 30x al origen del spoke con
        ?status=pending, sin token en la URL ni cookie de sesión."""
        mock_google_exchange({"email": pending_user.email, "name": "Pending"})
        db_session.add(pending_user)
        await db_session.commit()

        state = json.dumps({"redirect_to": SPOKE_URL})
        response = await client.get(
            "/api/v1/auth/callback",
            params={"code": "test_code", "state": state},
            follow_redirects=False,
        )

        assert response.status_code in (
            status.HTTP_302_FOUND,
            status.HTTP_307_TEMPORARY_REDIRECT,
        )
        location = response.headers["location"]
        assert location == f"{SPOKE_URL}?status=pending"
        # Nunca se filtra el token en el redirect de pending
        assert "token" not in location
        assert "access_token" not in response.headers.get("set-cookie", "")

    async def test_error_cross_origin_redirects_to_spoke_with_error(
        self, client, db_session, mock_google_exchange
    ):
        """Error (cuenta bloqueada) + redirect_to cross-origin → 30x al spoke
        con ?error=..., sin token."""
        mock_google_exchange({"email": "locked@example.com", "name": "Locked"})
        db_session.add(
            User(
                username="locked",
                email="locked@example.com",
                full_name="Locked",
                password_hash=get_password_hash(PASSWORD),
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                is_active=True,
                is_locked=True,
            )
        )
        await db_session.commit()

        state = json.dumps({"redirect_to": SPOKE_URL})
        response = await client.get(
            "/api/v1/auth/callback",
            params={"code": "test_code", "state": state},
            follow_redirects=False,
        )

        assert response.status_code in (
            status.HTTP_302_FOUND,
            status.HTTP_307_TEMPORARY_REDIRECT,
        )
        location = response.headers["location"]
        assert location.startswith(f"{SPOKE_URL}?error=")
        assert "Cuenta bloqueada" in unquote_plus(location)
        assert "token" not in location
        assert "access_token" not in response.headers.get("set-cookie", "")

    async def test_pending_without_redirect_to_keeps_authcore_frontend(
        self, client, db_session, mock_google_exchange
    ):
        """Regresión: sin redirect_to en el state → el destino sigue siendo
        el frontend propio de authCore (FRONTEND_URL/login?status=pending)."""
        mock_google_exchange({"email": "newuser@example.com", "name": "New User"})

        response = await client.get(
            "/api/v1/auth/callback",
            params={"code": "new_code"},
            follow_redirects=False,
        )

        assert response.status_code in (
            status.HTTP_302_FOUND,
            status.HTTP_307_TEMPORARY_REDIRECT,
        )
        location = response.headers["location"]
        assert location == f"{FRONTEND_URL}/login?status=pending"
        assert "access_token" not in response.headers.get("set-cookie", "")

    async def test_pending_relative_redirect_stays_on_authcore_frontend(
        self, client, db_session, mock_google_exchange
    ):
        """Regresión: redirect_to relativo (same-origin) → resuelto contra
        FRONTEND_URL y al login de authCore, no al spoke."""
        mock_google_exchange({"email": "newuser2@example.com", "name": "New User 2"})

        state = json.dumps({"redirect_to": "/registro"})
        response = await client.get(
            "/api/v1/auth/callback",
            params={"code": "new_code", "state": state},
            follow_redirects=False,
        )

        assert response.status_code in (
            status.HTTP_302_FOUND,
            status.HTTP_307_TEMPORARY_REDIRECT,
        )
        assert response.headers["location"] == f"{FRONTEND_URL}/login?status=pending"
