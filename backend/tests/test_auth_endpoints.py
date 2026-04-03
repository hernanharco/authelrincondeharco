"""
Tests para endpoints de autenticación
Cubren login tradicional, Google OAuth y gestión de tokens
"""
import pytest
from fastapi import status
# Importamos la herramienta de hashing real para evitar hardcoding de hashes
from app.core.security import create_access_token, get_password_hash
from app.schemas.auth import LoginRequest
from app.models.user import User, UserRole, UserStatus

class TestAuthEndpoints:
    """Tests para endpoints de autenticación"""

    def test_login_success(self, client, db_session, test_user):
        """Test login exitoso con credenciales válidas"""
        # El usuario ya tiene el hash de "testpass" gracias a la fixture
        db_session.add(test_user)
        db_session.commit()

        login_data = LoginRequest(username="testuser", password="testpass")
        response = client.post("/api/v1/auth/login", json=login_data.model_dump())

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
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

    def test_google_oauth_redirect(self, client):
        """Test que Google OAuth redirige correctamente"""
        response = client.get("/api/v1/auth/google", allow_redirects=False)

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert "accounts.google.com" in response.headers["location"]

    def test_google_callback_success(self, client, db_session, mock_google_oauth):
        """Test callback de Google OAuth exitoso"""
        # El mock ya está configurado vía fixture
        response = client.get(
            "/api/v1/auth/callback?code=test_code&state=test_state"
        )

        assert response.status_code == status.HTTP_200_OK
        # Verificamos que devuelva el HTML que hace el postMessage al frontend
        assert "window.opener.postMessage" in response.text

    def test_protected_endpoint_without_token(self, client):
        """Test acceso a endpoint protegido sin token"""
        response = client.get("/api/v1/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_endpoint_with_expired_token(self, client, db_session, test_user):
        """Test acceso con token expirado"""
        db_session.add(test_user)
        db_session.commit()
        
        # Creamos un token con tiempo en el pasado
        expired_token = create_access_token(
            data={"sub": str(test_user.id)},
            expires_delta=-1 
        )
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/users/me", headers=headers)

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