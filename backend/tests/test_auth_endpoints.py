"""
Tests para endpoints de autenticación
Cubren login tradicional, Google OAuth y gestión de tokens
"""
import pytest
from fastapi import status
from app.schemas.auth import LoginRequest
from app.models.user import User, UserRole, UserStatus
from app.core.security import create_access_token


class TestAuthEndpoints:
    """Tests para endpoints de autenticación"""

    def test_login_success(self, client, db_session, test_user):
        """Test login exitoso con credenciales válidas"""
        # Crear usuario de prueba
        db_session.add(test_user)
        db_session.commit()

        login_data = LoginRequest(username="testuser", password="testpass")
        response = client.post("/api/v1/auth/login", json=login_data.model_dump())

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert data["user"]["username"] == "testuser"

    def test_login_invalid_credentials(self, client, db_session, test_user):
        """Test login con credenciales inválidas"""
        db_session.add(test_user)
        db_session.commit()

        login_data = LoginRequest(username="testuser", password="wrongpass")
        response = client.post("/api/v1/auth/login", json=login_data.model_dump())

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Credenciales incorrectas"

    def test_login_user_not_found(self, client):
        """Test login con usuario que no existe"""
        login_data = LoginRequest(username="nonexistent", password="anypass")
        response = client.post("/api/v1/auth/login", json=login_data.model_dump())

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_invalid_data(self, client):
        """Test login con datos inválidos"""
        # Sin username
        response = client.post("/api/v1/auth/login", json={"password": "testpass"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Sin password
        response = client.post("/api/v1/auth/login", json={"username": "testuser"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_google_oauth_redirect(self, client):
        """Test que Google OAuth redirige correctamente"""
        response = client.get("/api/v1/auth/google", allow_redirects=False)

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert "accounts.google.com" in response.headers["location"]
        assert "client_id" in response.headers["location"]

    def test_google_callback_success(self, client, db_session, mock_google_oauth):
        """Test callback de Google OAuth exitoso"""
        # Mock del servicio de Google
        mock_google_oauth.return_value = (
            "test@example.com",
            "Test User",
            "testuser"
        )

        response = client.get(
            "/api/v1/auth/callback?code=test_code&state=test_state"
        )

        assert response.status_code == status.HTTP_200_OK
        assert "window.opener.postMessage" in response.text

    def test_google_callback_error(self, client, mock_google_oauth_error):
        """Test callback de Google OAuth con error"""
        mock_google_oauth_error.side_effect = Exception("OAuth Error")

        response = client.get(
            "/api/v1/auth/callback?code=invalid_code"
        )

        assert response.status_code == status.HTTP_200_OK
        assert "AUTH_ERROR" in response.text

    def test_protected_endpoint_without_token(self, client):
        """Test acceso a endpoint protegido sin token"""
        response = client.get("/api/v1/users/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_endpoint_with_invalid_token(self, client):
        """Test acceso a endpoint protegido con token inválido"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_endpoint_with_expired_token(self, client, test_user):
        """Test acceso con token expirado"""
        # Crear token expirado
        expired_token = create_access_token(
            data={"sub": str(test_user.id)},
            expires_delta=-1  # Expirado
        )
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.fixture
def test_user():
    """Usuario de prueba para tests"""
    return User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        password_hash="$2b$12$hashed_password",  # Mock hash
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        is_active=True,
        is_locked=False
    )


@pytest.fixture
def mock_google_oauth(monkeypatch):
    """Mock del servicio de Google OAuth"""
    from app.services.auth.GoogleOAuthService import GoogleOAuthService
    
    async def mock_get_user_info(code, redirect_uri):
        return "test@example.com", "Test User", "testuser"
    
    monkeypatch.setattr(GoogleOAuthService, "get_user_info", mock_get_user_info)
    return mock_get_user_info


@pytest.fixture
def mock_google_oauth_error(monkeypatch):
    """Mock del servicio de Google OAuth con error"""
    from app.services.auth.GoogleOAuthService import GoogleOAuthService
    
    async def mock_error(code, redirect_uri):
        raise Exception("OAuth Error")
    
    monkeypatch.setattr(GoogleOAuthService, "get_user_info", mock_error)
    return mock_error
