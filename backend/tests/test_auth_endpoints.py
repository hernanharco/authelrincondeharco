"""
Tests para endpoints de autenticación.
Cubren login tradicional, Google OAuth y gestión de tokens.
Async: usa httpx.AsyncClient + SQLAlchemy async.
"""
import pytest
from datetime import timedelta
from fastapi import status
# Importamos la herramienta de hashing real para evitar hardcoding de hashes
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

    async def test_google_oauth_redirect(self, client):
        """Test que Google OAuth redirige correctamente"""
        response = await client.get("/api/v1/auth/google", follow_redirects=False)

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert "accounts.google.com" in response.headers["location"]

    @pytest.mark.skip(reason="GoogleCallback requiere refactor de process_google_login (issue #8)")
    async def test_google_callback_success(self, client, db_session, mock_google_oauth):
        """Test callback de Google OAuth exitoso"""
        response = await client.get(
            "/api/v1/auth/callback?code=test_code&state=test_state"
        )

        assert response.status_code == status.HTTP_200_OK
        assert "window.opener.postMessage" in response.text

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
def mock_google_oauth(monkeypatch):
    """Mock para simular la respuesta exitosa de Google"""
    from app.services.auth.GoogleOAuthService import GoogleOAuthService
    
    async def mock_get_user_info(code, redirect_uri):
        return "test@example.com", "Test User", "testuser"
    
    monkeypatch.setattr(GoogleOAuthService, "get_user_info", mock_get_user_info)
    return mock_get_user_info