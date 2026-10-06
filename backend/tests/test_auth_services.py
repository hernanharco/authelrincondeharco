"""
Tests para servicios de autenticación (reescritos en Fase 1 contra la API actual).
Cubren AuthService, TokenService y GoogleOAuthService.

Unidad pura: repositorios y OAuth mockeados (sin BD, sin red).
NOTA: GoogleOAuthService abre un httpx.AsyncClient en su constructor —
el fixture lo parchea para no crear clientes reales (sin red ni resource warnings).
"""
import httpx
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, call, patch

from fastapi import HTTPException

from app.core.security import get_password_hash
from app.interfaces.user.IUserRepository import IUserRepository
from app.models.user import User
from app.services.auth.AuthService import AuthService
from app.services.auth.GoogleOAuthService import GoogleOAuthService
from app.services.auth.TokenService import TokenService
from app.types.enums import UserRole, UserStatus

pytestmark = pytest.mark.asyncio

PASSWORD = "testpass"
PASSWORD_HASH = get_password_hash(PASSWORD)
CALLBACK_URI = "http://localhost:8001/api/v1/auth/callback"
TOKEN_URL = "https://oauth2.googleapis.com/token"


def make_user(**overrides) -> User:
    """Usuario de prueba sin tocar la BD."""
    defaults = dict(
        id=1,
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        password_hash=PASSWORD_HASH,
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        is_active=True,
        is_locked=False,
        failed_login_attempts=0,
        origin="manual",
    )
    defaults.update(overrides)
    return User(**defaults)


def _response(status_code: int = 200, payload: dict = None, text: str = "") -> Mock:
    """Respuesta HTTP simulada para httpx (status_code + json + text)."""
    resp = Mock()
    resp.status_code = status_code
    resp.json.return_value = payload if payload is not None else {}
    resp.text = text
    return resp


class TestAuthService:
    """Tests para AuthService (authenticate_user, create_access_token, process_google_login)"""

    @pytest.fixture
    def user_repository(self):
        return AsyncMock(spec=IUserRepository)

    @pytest.fixture
    def oauth_service(self):
        return AsyncMock()

    @pytest.fixture
    def token_service(self):
        # Servicio real: los tests de token deben producir JWT RS256 válidos.
        return TokenService()

    @pytest.fixture
    def auth_service(self, token_service, oauth_service, user_repository):
        return AuthService(
            token_service=token_service,
            oauth_service=oauth_service,
            user_repository=user_repository,
        )

    # ── authenticate_user (login tradicional) ───────────────────

    async def test_authenticate_user_success(self, auth_service, user_repository):
        user = make_user()
        user_repository.get_by_username.return_value = user

        result = await auth_service.authenticate_user("testuser", PASSWORD)

        assert result is not None
        assert result.username == "testuser"
        assert result.email == "test@example.com"
        user_repository.get_by_username.assert_awaited_once_with("testuser")

    async def test_authenticate_user_falls_back_to_email(
        self, auth_service, user_repository
    ):
        user = make_user()
        user_repository.get_by_username.return_value = None
        user_repository.get_by_email.return_value = user

        result = await auth_service.authenticate_user("test@example.com", PASSWORD)

        assert result is user
        user_repository.get_by_email.assert_awaited_once_with("test@example.com")

    async def test_authenticate_user_wrong_password(
        self, auth_service, user_repository
    ):
        user = make_user(failed_login_attempts=0)
        user_repository.get_by_username.return_value = user

        result = await auth_service.authenticate_user("testuser", "wrongpass")

        assert result is None
        # Cada fallo incrementa el contador de intentos
        user_repository.update.assert_awaited_once_with(1, {"failed_login_attempts": 1})

    async def test_authenticate_user_lockout_after_max_attempts(
        self, auth_service, user_repository
    ):
        user = make_user(failed_login_attempts=4)
        user_repository.get_by_username.return_value = user

        result = await auth_service.authenticate_user("testuser", "wrongpass")

        assert result is None
        # 5º intento fallido → bloqueo de la cuenta (MAX_FAILED_LOGIN_ATTEMPTS = 5)
        user_repository.update.assert_awaited_once_with(
            1, {"failed_login_attempts": 5, "is_locked": True}
        )

    async def test_authenticate_user_not_found(self, auth_service, user_repository):
        user_repository.get_by_username.return_value = None
        user_repository.get_by_email.return_value = None

        result = await auth_service.authenticate_user("nonexistent", "anypass")

        assert result is None

    async def test_authenticate_user_inactive(self, auth_service, user_repository):
        user = make_user(is_active=False, status=UserStatus.INACTIVE)
        user_repository.get_by_username.return_value = user

        result = await auth_service.authenticate_user("testuser", PASSWORD)

        assert result is None

    async def test_authenticate_user_locked(self, auth_service, user_repository):
        user = make_user(is_locked=True)
        user_repository.get_by_username.return_value = user

        result = await auth_service.authenticate_user("testuser", PASSWORD)

        # Cuenta bloqueada: se rechaza antes de verificar la contraseña
        assert result is None
        user_repository.update.assert_not_awaited()

    async def test_authenticate_user_resets_counter_on_success(
        self, auth_service, user_repository
    ):
        user = make_user(failed_login_attempts=3)
        user_repository.get_by_username.return_value = user

        result = await auth_service.authenticate_user("testuser", PASSWORD)

        assert result is user
        user_repository.update.assert_awaited_once_with(
            1, {"failed_login_attempts": 0, "is_locked": False}
        )

    # ── create_access_token ─────────────────────────────────────

    async def test_create_access_token(self, auth_service, token_service):
        user = make_user()

        token, expires_in = await auth_service.create_access_token(user)

        assert isinstance(token, str)
        assert len(token.split(".")) == 3  # JWT con 3 partes
        assert expires_in > 0

        payload = token_service.get_token_payload(token)
        assert payload["sub"] == str(user.id)
        assert payload["username"] == "testuser"
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "USER"
        assert payload["type"] == "access"

    # ── process_google_login (Authorization Code Flow) ──────────

    async def test_process_google_login_new_user_pending_approval(
        self, auth_service, oauth_service, user_repository
    ):
        """Usuario nuevo vía Google → se crea PENDING y se lanza 403 PENDING_APPROVAL (sin token)."""
        oauth_service.exchange_code.return_value = {
            "email": "newuser@gmail.com",
            "name": "New Google User",
        }
        user_repository.get_by_email.return_value = None
        user_repository.exists_by_username.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.process_google_login("auth-code", CALLBACK_URI)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "PENDING_APPROVAL"

        user_repository.create.assert_awaited_once()
        created = user_repository.create.await_args.args[0]
        assert created["email"] == "newuser@gmail.com"
        assert created["username"] == "newuser"
        assert created["full_name"] == "New Google User"
        assert created["role"] == UserRole.NONE
        assert created["status"] == UserStatus.PENDING
        assert created["is_active"] is False
        assert created["origin"] == "google"

    async def test_process_google_login_new_user_username_collision(
        self, auth_service, oauth_service, user_repository
    ):
        """Si el username base ya existe, se le añade un sufijo numérico."""
        oauth_service.exchange_code.return_value = {
            "email": "newuser@gmail.com",
            "name": "New Google User",
        }
        user_repository.get_by_email.return_value = None
        user_repository.exists_by_username.side_effect = [True, False]

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.process_google_login("auth-code", CALLBACK_URI)

        assert exc_info.value.status_code == 403
        created = user_repository.create.await_args.args[0]
        assert created["username"] == "newuser1"

    async def test_process_google_login_new_user_keeps_origin(
        self, auth_service, oauth_service, user_repository
    ):
        """El parámetro origin (sitio de origen) se persiste en el usuario nuevo."""
        oauth_service.exchange_code.return_value = {
            "email": "newuser@gmail.com",
            "name": "New Google User",
        }
        user_repository.get_by_email.return_value = None
        user_repository.exists_by_username.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.process_google_login(
                "auth-code", CALLBACK_URI, origin="rincom"
            )

        assert exc_info.value.status_code == 403
        created = user_repository.create.await_args.args[0]
        assert created["origin"] == "rincom"

    async def test_process_google_login_existing_user(
        self, auth_service, oauth_service, user_repository, token_service
    ):
        """Usuario existente y activo → actualiza last_login y devuelve token."""
        user = make_user(id=7, role=UserRole.USER)
        oauth_service.exchange_code.return_value = {
            "email": user.email,
            "name": user.full_name,
        }
        user_repository.get_by_email.return_value = user

        result_user, token, expires_in = await auth_service.process_google_login(
            "auth-code", CALLBACK_URI
        )

        assert result_user is user
        assert result_user.id == 7
        assert isinstance(token, str)
        assert len(token.split(".")) == 3
        assert expires_in > 0

        user_repository.update.assert_awaited_once()
        update_id, update_data = user_repository.update.await_args.args
        assert update_id == 7
        assert "last_login" in update_data

        payload = token_service.get_token_payload(token)
        assert payload["sub"] == "7"

    async def test_process_google_login_existing_user_updates_origin(
        self, auth_service, oauth_service, user_repository
    ):
        """Usuario existente que llega de un sitio nuevo → se actualiza su origin."""
        user = make_user(id=7, origin="manual")
        oauth_service.exchange_code.return_value = {"email": user.email}
        user_repository.get_by_email.return_value = user

        await auth_service.process_google_login("auth-code", CALLBACK_URI, origin="rincom")

        first_id, first_data = user_repository.update.await_args_list[0].args
        assert first_id == 7
        assert first_data == {"origin": "rincom"}

    async def test_process_google_login_existing_pending_user(
        self, auth_service, oauth_service, user_repository
    ):
        """Usuario existente aún PENDING → 403 PENDING_APPROVAL, sin token."""
        user = make_user(id=7, role=UserRole.NONE, status=UserStatus.PENDING, is_active=False)
        oauth_service.exchange_code.return_value = {"email": user.email}
        user_repository.get_by_email.return_value = user

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.process_google_login("auth-code", CALLBACK_URI)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "PENDING_APPROVAL"

    async def test_process_google_login_existing_locked_user(
        self, auth_service, oauth_service, user_repository
    ):
        user = make_user(id=7, is_locked=True)
        oauth_service.exchange_code.return_value = {"email": user.email}
        user_repository.get_by_email.return_value = user

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.process_google_login("auth-code", CALLBACK_URI)

        assert exc_info.value.status_code == 403
        assert "bloqueada" in exc_info.value.detail.lower()

    async def test_process_google_login_without_email(
        self, auth_service, oauth_service, user_repository
    ):
        oauth_service.exchange_code.return_value = {"name": "Sin email"}

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.process_google_login("auth-code", CALLBACK_URI)

        assert exc_info.value.status_code == 400
        user_repository.get_by_email.assert_not_awaited()


class TestTokenService:
    """Tests para TokenService (JWT RS256: create_access_token / verify_token / revocación)"""

    @pytest.fixture
    def token_service(self):
        return TokenService()

    async def test_create_access_token(self, token_service):
        data = {"sub": "123", "role": "USER"}

        token, expires_at = await token_service.create_access_token(data)

        assert isinstance(token, str)
        assert len(token.split(".")) == 3  # JWT con 3 partes
        assert isinstance(expires_at, datetime)
        assert expires_at > datetime.now(timezone.utc)

    async def test_create_access_token_with_expires_delta(self, token_service):
        token, expires_at = await token_service.create_access_token(
            {"sub": "123"}, expires_delta=60
        )

        now = datetime.now(timezone.utc)
        assert now + timedelta(seconds=55) <= expires_at <= now + timedelta(seconds=61)
        assert await token_service.verify_token(token) is not None

    async def test_verify_token_success(self, token_service):
        data = {"sub": "123", "role": "USER"}

        token, _ = await token_service.create_access_token(data)
        result = await token_service.verify_token(token)

        assert result is not None
        assert result["sub"] == "123"
        assert result["role"] == "USER"
        # Trazabilidad: iat + jti siempre presentes
        assert "iat" in result
        assert "jti" in result

    async def test_verify_token_invalid(self, token_service):
        assert await token_service.verify_token("invalid.token.here") is None

    async def test_verify_token_expired(self, token_service):
        token, _ = await token_service.create_access_token(
            {"sub": "123"}, expires_delta=-1
        )

        assert await token_service.verify_token(token) is None

    async def test_verify_token_revoked(self, token_service):
        token, _ = await token_service.create_access_token({"sub": "123"})

        assert await token_service.revoke_token(token) is True
        assert await token_service.is_token_revoked(token) is True
        # Un token revocado se rechaza aunque su firma siga siendo válida
        assert await token_service.verify_token(token) is None

    async def test_get_token_payload_ignores_expiration(self, token_service):
        token, _ = await token_service.create_access_token(
            {"sub": "123"}, expires_delta=-1
        )

        # get_token_payload decodifica sin validar exp (a diferencia de verify_token)
        payload = token_service.get_token_payload(token)
        assert payload is not None
        assert payload["sub"] == "123"


class TestGoogleOAuthService:
    """Tests para GoogleOAuthService (exchange_code / verify_token / get_user_info).
    El cliente httpx se mockea: cero llamadas a la red."""

    @pytest.fixture
    def oauth_service(self):
        # Parchea el constructor para no crear un httpx.AsyncClient real
        # (evita resource warnings y garantiza cero red en los tests).
        with patch("app.services.auth.GoogleOAuthService.httpx.AsyncClient"):
            service = GoogleOAuthService()
        service._client = AsyncMock()
        return service

    # ── exchange_code ───────────────────────────────────────────

    async def test_exchange_code_success(self, oauth_service):
        oauth_service._client.post.return_value = _response(
            200, {"access_token": "google-access-token"}
        )
        oauth_service._client.get.return_value = _response(
            200, {"email": "user@gmail.com", "name": "Test User", "sub": "123456789"}
        )

        user_info = await oauth_service.exchange_code("test_code", CALLBACK_URI)

        assert user_info["email"] == "user@gmail.com"
        assert user_info["name"] == "Test User"
        assert user_info["sub"] == "123456789"

        post_kwargs = oauth_service._client.post.await_args.kwargs
        assert post_kwargs["data"]["code"] == "test_code"
        assert post_kwargs["data"]["grant_type"] == "authorization_code"
        assert post_kwargs["data"]["redirect_uri"] == CALLBACK_URI

    async def test_exchange_code_token_endpoint_error(self, oauth_service):
        oauth_service._client.post.return_value = _response(400, text="bad code")

        with pytest.raises(HTTPException) as exc_info:
            await oauth_service.exchange_code("bad_code", CALLBACK_URI)

        assert exc_info.value.status_code == 400

    async def test_exchange_code_missing_access_token(self, oauth_service):
        oauth_service._client.post.return_value = _response(200, {"token_type": "Bearer"})

        with pytest.raises(HTTPException) as exc_info:
            await oauth_service.exchange_code("test_code", CALLBACK_URI)

        assert exc_info.value.status_code == 400
        assert "access_token" in exc_info.value.detail

    async def test_exchange_code_userinfo_endpoint_error(self, oauth_service):
        oauth_service._client.post.return_value = _response(
            200, {"access_token": "google-access-token"}
        )
        oauth_service._client.get.return_value = _response(500, text="server error")

        with pytest.raises(HTTPException) as exc_info:
            await oauth_service.exchange_code("test_code", CALLBACK_URI)

        assert exc_info.value.status_code == 400

    async def test_exchange_code_connection_error(self, oauth_service):
        request = httpx.Request("POST", TOKEN_URL)
        oauth_service._client.post.side_effect = httpx.ConnectError(
            "connection refused", request=request
        )

        with pytest.raises(HTTPException) as exc_info:
            await oauth_service.exchange_code("test_code", CALLBACK_URI)

        assert exc_info.value.status_code == 503

    async def test_exchange_code_timeout(self, oauth_service):
        request = httpx.Request("POST", TOKEN_URL)
        oauth_service._client.post.side_effect = httpx.TimeoutException(
            "timed out", request=request
        )

        with pytest.raises(HTTPException) as exc_info:
            await oauth_service.exchange_code("test_code", CALLBACK_URI)

        assert exc_info.value.status_code == 504

    # ── verify_token ────────────────────────────────────────────

    async def test_verify_token_success(self, oauth_service):
        oauth_service._client.get.return_value = _response(
            200, {"email": "user@gmail.com", "name": "Test User"}
        )

        result = await oauth_service.verify_token("google-access-token")

        assert result["email"] == "user@gmail.com"
        # Llama a la API v3 de userinfo con el Bearer token
        headers = oauth_service._client.get.await_args.kwargs["headers"]
        assert headers["Authorization"] == "Bearer google-access-token"

    async def test_verify_token_invalid(self, oauth_service):
        oauth_service._client.get.return_value = _response(401, text="invalid")

        with pytest.raises(HTTPException) as exc_info:
            await oauth_service.verify_token("expired-token")

        assert exc_info.value.status_code == 401

    # ── get_user_info ───────────────────────────────────────────

    async def test_get_user_info_success(self, oauth_service):
        """Mapea la respuesta de Google a los campos públicos del servicio."""
        oauth_service._client.get.return_value = _response(
            200,
            {
                "email": "user@gmail.com",
                "name": "Test User",
                "picture": "https://pic",
                "given_name": "Test",
                "family_name": "User",
                "locale": "es",
                "email_verified": True,
            },
        )

        user_info = await oauth_service.get_user_info("google-access-token")

        assert user_info is not None
        assert user_info["email"] == "user@gmail.com"
        assert user_info["name"] == "Test User"
        assert user_info["verified_email"] is True

    async def test_get_user_info_error_returns_none(self, oauth_service):
        """Ante cualquier fallo de Google, get_user_info degrada a None (no lanza)."""
        oauth_service._client.get.return_value = _response(401, text="invalid")

        assert await oauth_service.get_user_info("bad-token") is None
