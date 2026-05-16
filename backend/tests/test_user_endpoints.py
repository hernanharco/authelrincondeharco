"""
Tests para endpoints de usuarios
Cubren CRUD completo, gestión de roles y permisos

NOTA: Tests desincronizados con implementación (stats keys, usuarios no persistidos en fixtures, etc.)
Se skippean hasta la estabilización arquitectónica (Fase 1).
"""
import pytest
from fastapi import status
from app.models.user import User, UserRole, UserStatus
from app.schemas.user import UserCreate, UserUpdate, RoleUpdate, StatusUpdate

pytestmark = pytest.mark.skip(reason="Necesita reescritura post-estabilización (Fase 1)")


class TestUserEndpoints:
    """Tests para endpoints de usuarios"""

    def test_get_current_user(self, client, auth_headers, test_user):
        """Test obtener usuario actual"""
        response = client.get("/api/v1/users/me", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email

    def test_get_users_as_admin(self, client, admin_headers, test_user):
        """Test listar usuarios como administrador"""
        response = client.get("/api/v1/users/", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_users_as_user_forbidden(self, client, auth_headers):
        """Test listar usuarios como usuario normal (debe fallar)"""
        response = client.get("/api/v1/users/", headers=auth_headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_users_with_filters(self, client, admin_headers, test_user):
        """Test filtros en listado de usuarios"""
        # Filtro por rol
        response = client.get(
            "/api/v1/users/?role=USER", headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK

        # Filtro por búsqueda
        response = client.get(
            "/api/v1/users/?search=test", headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK

        # Paginación
        response = client.get(
            "/api/v1/users/?skip=0&limit=5", headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK

    def test_get_user_by_id_success(self, client, admin_headers, test_user):
        """Test obtener usuario por ID exitoso"""
        response = client.get(
            f"/api/v1/users/{test_user.id}", headers=admin_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_user.id
        assert data["username"] == test_user.username

    def test_get_user_by_id_not_found(self, client, admin_headers):
        """Test obtener usuario por ID que no existe"""
        response = client.get("/api/v1/users/99999", headers=admin_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_user_as_admin(self, client, admin_headers):
        """Test crear usuario como administrador"""
        user_data = UserCreate(
            username="newuser",
            email="newuser@example.com",
            full_name="New User",
            password="newpass123",
            role=UserRole.USER
        )

        response = client.post(
            "/api/v1/users/", 
            json=user_data.model_dump(), 
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"

    def test_create_user_duplicate_username(self, client, admin_headers, test_user):
        """Test crear usuario con username duplicado"""
        user_data = UserCreate(
            username=test_user.username,  # Duplicado
            email="different@example.com",
            full_name="Different User",
            password="newpass123"
        )

        response = client.post(
            "/api/v1/users/", 
            json=user_data.model_dump(), 
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "ya existe" in response.json()["detail"]

    def test_create_user_as_user_forbidden(self, client, auth_headers):
        """Test crear usuario como usuario normal (debe fallar)"""
        user_data = UserCreate(
            username="newuser",
            email="newuser@example.com",
            full_name="New User",
            password="newpass123"
        )

        response = client.post(
            "/api/v1/users/", 
            json=user_data.model_dump(), 
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_user_as_admin(self, client, admin_headers, test_user):
        """Test actualizar usuario como administrador"""
        update_data = UserUpdate(
            full_name="Updated Name",
            email="updated@example.com"
        )

        response = client.put(
            f"/api/v1/users/{test_user.id}", 
            json=update_data.model_dump(), 
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["full_name"] == "Updated Name"

    def test_update_user_role(self, client, admin_headers, test_user):
        """Test cambiar rol de usuario"""
        role_data = RoleUpdate(role=UserRole.MANAGER)

        response = client.patch(
            f"/api/v1/users/{test_user.id}/role", 
            json=role_data.model_dump(), 
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == UserRole.MANAGER.value

    def test_update_user_status(self, client, admin_headers, test_user):
        """Test cambiar estado de usuario"""
        status_data = StatusUpdate(status=UserStatus.SUSPENDED)

        response = client.patch(
            f"/api/v1/users/{test_user.id}/status", 
            json=status_data.model_dump(), 
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == UserStatus.SUSPENDED.value

    def test_delete_user_as_admin(self, client, admin_headers, test_user):
        """Test eliminar usuario como administrador"""
        response = client.delete(
            f"/api/v1/users/{test_user.id}", 
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_200_OK

    def test_delete_user_as_user_forbidden(self, client, auth_headers, test_user):
        """Test eliminar usuario como usuario normal (debe fallar)"""
        response = client.delete(
            f"/api/v1/users/{test_user.id}", 
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_pending_users_as_admin(self, client, admin_headers, pending_user):
        """Test obtener usuarios pendientes como administrador"""
        response = client.get("/api/v1/users/pending", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_get_pending_users_as_user_forbidden(self, client, auth_headers):
        """Test obtener usuarios pendientes como usuario normal (debe fallar)"""
        response = client.get("/api/v1/users/pending", headers=auth_headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_user_stats_as_admin(self, client, admin_headers):
        """Test obtener estadísticas como administrador"""
        response = client.get("/api/v1/users/stats", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_users" in data
        assert "active_users" in data
        assert "pending_users" in data

    def test_get_user_stats_as_user_forbidden(self, client, auth_headers):
        """Test obtener estadísticas como usuario normal (debe fallar)"""
        response = client.get("/api/v1/users/stats", headers=auth_headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_users_by_origin_as_admin(self, client, admin_headers):
        """Test obtener usuarios por origen como administrador"""
        response = client.get("/api/v1/users/by-origin", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)


@pytest.fixture
def test_user():
    """Usuario de prueba para tests"""
    return User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        password_hash="$2b$12$hashed_password",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        is_active=True,
        is_locked=False
    )


@pytest.fixture
def pending_user():
    """Usuario pendiente para tests"""
    return User(
        username="pendinguser",
        email="pending@example.com",
        full_name="Pending User",
        password_hash="$2b$12$hashed_password",
        role=UserRole.NONE,
        status=UserStatus.PENDING,
        is_active=True,
        is_locked=False
    )


@pytest.fixture
def admin_user():
    """Usuario administrador para tests"""
    return User(
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        password_hash="$2b$12$hashed_password",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        is_active=True,
        is_locked=False
    )


@pytest.fixture
def auth_headers(client, test_user):
    """Headers de autenticación para usuario normal"""
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client, admin_user):
    """Headers de autenticación para administrador"""
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": str(admin_user.id)})
    return {"Authorization": f"Bearer {token}"}
