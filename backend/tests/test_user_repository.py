"""
Tests para repositorio de usuarios
Cubren acceso a datos y operaciones CRUD
"""
import pytest
from sqlalchemy.orm import Session
from app.repositories.user.UserRepository import UserRepository
from app.models.user import User, UserRole, UserStatus


class TestUserRepository:
    """Tests para UserRepository"""

    @pytest.fixture
    def user_repository(self, db_session):
        """Instancia de UserRepository para tests"""
        return UserRepository(db_session)

    @pytest.fixture
    def test_user(self):
        """Usuario de prueba"""
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

    def test_create_user(self, user_repository, test_user):
        """Test crear usuario en base de datos"""
        result = user_repository.create(test_user.__dict__)

        assert result is not None
        assert result.id is not None
        assert result.username == test_user.username
        assert result.email == test_user.email

    def test_get_by_id_success(self, user_repository, test_user):
        """Test obtener usuario por ID"""
        # Crear usuario
        created = user_repository.create(test_user.__dict__)
        user_repository.db.commit()

        # Obtener por ID
        result = user_repository.get_by_id(created.id)

        assert result is not None
        assert result.id == created.id
        assert result.username == test_user.username

    def test_get_by_id_not_found(self, user_repository):
        """Test obtener usuario por ID que no existe"""
        result = user_repository.get_by_id(99999)

        assert result is None

    def test_get_by_username_success(self, user_repository, test_user):
        """Test obtener usuario por username"""
        # Crear usuario
        created = user_repository.create(test_user.__dict__)
        user_repository.db.commit()

        # Obtener por username
        result = user_repository.get_by_username(test_user.username)

        assert result is not None
        assert result.username == test_user.username

    def test_get_by_username_not_found(self, user_repository):
        """Test obtener usuario por username que no existe"""
        result = user_repository.get_by_username("nonexistent")

        assert result is None

    def test_get_by_email_success(self, user_repository, test_user):
        """Test obtener usuario por email"""
        # Crear usuario
        created = user_repository.create(test_user.__dict__)
        user_repository.db.commit()

        # Obtener por email
        result = user_repository.get_by_email(test_user.email)

        assert result is not None
        assert result.email == test_user.email

    def test_get_by_email_not_found(self, user_repository):
        """Test obtener usuario por email que no existe"""
        result = user_repository.get_by_email("nonexistent@example.com")

        assert result is None

    def test_exists_by_username_true(self, user_repository, test_user):
        """Test verificar existencia por username - existe"""
        user_repository.create(test_user.__dict__)
        user_repository.db.commit()

        result = user_repository.exists_by_username(test_user.username)

        assert result is True

    def test_exists_by_username_false(self, user_repository):
        """Test verificar existencia por username - no existe"""
        result = user_repository.exists_by_username("nonexistent")

        assert result is False

    def test_exists_by_email_true(self, user_repository, test_user):
        """Test verificar existencia por email - existe"""
        user_repository.create(test_user.__dict__)
        user_repository.db.commit()

        result = user_repository.exists_by_email(test_user.email)

        assert result is True

    def test_exists_by_email_false(self, user_repository):
        """Test verificar existencia por email - no existe"""
        result = user_repository.exists_by_email("nonexistent@example.com")

        assert result is False

    def test_get_all_with_filters(self, user_repository, test_user):
        """Test listar usuarios con filtros"""
        # Crear múltiples usuarios
        users_data = [
            User(
                username="user1",
                email="user1@example.com",
                full_name="User One",
                password_hash="$2b$12$hashed_password",
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                is_active=True,
                is_locked=False
            ),
            User(
                username="admin1",
                email="admin1@example.com",
                full_name="Admin One",
                password_hash="$2b$12$hashed_password",
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
                is_active=True,
                is_locked=False
            ),
            test_user
        ]

        for user in users_data:
            user_repository.create(user.__dict__)
        user_repository.db.commit()

        # Test sin filtros
        result_all = user_repository.get_all()
        assert len(result_all) >= 3

        # Test filtro por rol
        result_users = user_repository.get_all(role=UserRole.USER)
        user_count = len([u for u in result_all if u.role == UserRole.USER])
        assert len(result_users) == user_count

        # Test filtro por búsqueda
        result_search = user_repository.get_all(search="user")
        assert len(result_search) >= 2  # user1 y testuser

        # Test paginación
        result_paginated = user_repository.get_all(skip=0, limit=2)
        assert len(result_paginated) == 2

    def test_update_user(self, user_repository, test_user):
        """Test actualizar usuario"""
        # Crear usuario
        created = user_repository.create(test_user.__dict__)
        user_repository.db.commit()

        # Actualizar
        update_data = {
            "full_name": "Updated Name",
            "email": "updated@example.com"
        }
        result = user_repository.update(created.id, update_data)

        assert result is not None
        assert result.full_name == "Updated Name"
        assert result.email == "updated@example.com"

    def test_update_user_not_found(self, user_repository):
        """Test actualizar usuario que no existe"""
        update_data = {"full_name": "Updated Name"}

        result = user_repository.update(99999, update_data)

        assert result is None

    def test_delete_user(self, user_repository, test_user):
        """Test eliminar usuario (borrado lógico)"""
        # Crear usuario
        created = user_repository.create(test_user.__dict__)
        user_repository.db.commit()

        # Eliminar
        result = user_repository.delete(created.id)

        assert result is True

        # Verificar que está inactivo
        deleted = user_repository.get_by_id(created.id)
        assert deleted is not None
        assert deleted.is_active is False

    def test_delete_user_not_found(self, user_repository):
        """Test eliminar usuario que no existe"""
        result = user_repository.delete(99999)

        assert result is False

    def test_get_pending_users(self, user_repository):
        """Test obtener usuarios pendientes"""
        # Crear usuarios pendientes
        pending_user = User(
            username="pending",
            email="pending@example.com",
            full_name="Pending User",
            password_hash="$2b$12$hashed_password",
            role=UserRole.NONE,
            status=UserStatus.PENDING,
            is_active=True,
            is_locked=False
        )

        user_repository.create(pending_user.__dict__)
        user_repository.create(test_user.__dict__)  # Usuario activo
        user_repository.db.commit()

        result = user_repository.get_pending_users()

        assert len(result) == 1
        assert result[0].status == UserStatus.PENDING

    def test_get_stats(self, user_repository, test_user):
        """Test obtener estadísticas"""
        # Crear usuarios con diferentes estados
        active_user = User(
            username="active",
            email="active@example.com",
            full_name="Active User",
            password_hash="$2b$12$hashed_password",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            is_active=True,
            is_locked=False
        )

        pending_user = User(
            username="pending",
            email="pending@example.com",
            full_name="Pending User",
            password_hash="$2b$12$hashed_password",
            role=UserRole.NONE,
            status=UserStatus.PENDING,
            is_active=True,
            is_locked=False
        )

        user_repository.create(active_user.__dict__)
        user_repository.create(pending_user.__dict__)
        user_repository.create(test_user.__dict__)
        user_repository.db.commit()

        result = user_repository.get_stats()

        assert "total_users" in result
        assert "active_users" in result
        assert "pending_users" in result
        assert result["total_users"] >= 3
        assert result["active_users"] >= 2
        assert result["pending_users"] >= 1

    def test_get_users_by_origin(self, user_repository, test_user):
        """Test obtener usuarios por origen"""
        # Crear usuarios con diferentes orígenes
        google_user = User(
            username="googleuser",
            email="google@example.com",
            full_name="Google User",
            password_hash="$2b$12$hashed_password",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            is_active=True,
            is_locked=False,
            origin="google"
        )

        manual_user = User(
            username="manualuser",
            email="manual@example.com",
            full_name="Manual User",
            password_hash="$2b$12$hashed_password",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            is_active=True,
            is_locked=False,
            origin="manual"
        )

        user_repository.create(google_user.__dict__)
        user_repository.create(manual_user.__dict__)
        user_repository.create(test_user.__dict__)
        user_repository.db.commit()

        result = user_repository.get_users_by_origin()

        assert isinstance(result, list)
        assert len(result) >= 2  # Al menos google y manual

        # Verificar estructura de resultados
        for item in result:
            assert "origin" in item
            assert "count" in item
            assert isinstance(item["count"], int)
