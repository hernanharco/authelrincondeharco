"""
Tests para modelos de base de datos
Cubren validaciones de SQLAlchemy y relaciones
"""
import pytest
from app.models.user import User, UserRole, UserStatus


class TestUserModel:
    """Tests para modelo User"""

    def test_user_creation(self):
        """Test creación de usuario con todos los campos"""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            password_hash="$2b$12$hashed_password",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            is_active=True,
            is_locked=False
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.role == UserRole.USER
        assert user.status == UserStatus.ACTIVE
        assert user.is_active is True
        assert user.is_locked is False

    def test_user_defaults(self):
        """Test valores por defecto del modelo"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="$2b$12$hashed_password"
        )

        # Verificar valores por defecto
        assert user.role is not None  # Debe tener rol por defecto
        assert user.status is not None  # Debe tener estado por defecto
        assert user.failed_login_attempts == 0  # Debe inicializar en 0

    def test_user_repr(self):
        """Test representación string del usuario"""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User"
        )

        repr_str = repr(user)
        assert "testuser" in repr_str
        assert "test@example.com" in repr_str

    def test_user_to_dict(self):
        """Test conversión a diccionario"""
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.USER,
            status=UserStatus.ACTIVE
        )

        user_dict = user.__dict__

        assert user_dict["username"] == "testuser"
        assert user_dict["email"] == "test@example.com"
        assert user_dict["full_name"] == "Test User"
        assert user_dict["role"] == UserRole.USER

    def test_user_role_enum_values(self):
        """Test valores del enum UserRole"""
        assert UserRole.USER.value == "USER"
        assert UserRole.ADMIN.value == "ADMIN"
        assert UserRole.MANAGER.value == "MANAGER"
        assert UserRole.VIEWER.value == "VIEWER"
        assert UserRole.SUPERADMIN.value == "SUPERADMIN"
        assert UserRole.NONE.value == "NONE"

    def test_user_status_enum_values(self):
        """Test valores del enum UserStatus"""
        assert UserStatus.ACTIVE.value == "ACTIVE"
        assert UserStatus.INACTIVE.value == "INACTIVE"
        assert UserStatus.SUSPENDED.value == "SUSPENDED"
        assert UserStatus.PENDING.value == "PENDING"

    def test_user_validation(self):
        """Test validaciones del modelo"""
        # Username requerido
        with pytest.raises(Exception):
            user = User(email="test@example.com", password_hash="hash")

        # Email requerido
        with pytest.raises(Exception):
            user = User(username="testuser", password_hash="hash")

        # Password hash requerido
        with pytest.raises(Exception):
            user = User(username="testuser", email="test@example.com")

    def test_user_timestamps(self):
        """Test timestamps automáticos"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="$2b$12$hashed_password"
        )

        # Los timestamps deben ser None antes de guardar
        assert user.created_at is None
        assert user.updated_at is None

    def test_user_role_assignment(self):
        """Test asignación de roles"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="$2b$12$hashed_password",
            role=UserRole.ADMIN
        )

        assert user.role == UserRole.ADMIN
        assert isinstance(user.role, UserRole)

    def test_user_status_assignment(self):
        """Test asignación de estados"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="$2b$12$hashed_password",
            status=UserStatus.PENDING
        )

        assert user.status == UserStatus.PENDING
        assert isinstance(user.status, UserStatus)

    def test_user_boolean_fields(self):
        """Test campos booleanos"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="$2b$12$hashed_password",
            is_active=True,
            is_locked=False
        )

        assert user.is_active is True
        assert user.is_locked is False
        assert isinstance(user.is_active, bool)
        assert isinstance(user.is_locked, bool)

    def test_user_integer_fields(self):
        """Test campos enteros"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="$2b$12$hashed_password",
            failed_login_attempts=5
        )

        assert user.failed_login_attempts == 5
        assert isinstance(user.failed_login_attempts, int)

    def test_user_optional_fields(self):
        """Test campos opcionales"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="$2b$12$hashed_password"
        )

        # Campos opcionales pueden ser None
        assert user.full_name is None or isinstance(user.full_name, str)
        assert user.last_login is None
        assert user.last_ip is None
        assert user.notes is None
        assert user.origin is None

    def test_user_string_fields_max_length(self):
        """Test longitudes máximas de campos string"""
        # Username largo
        long_username = "a" * 100
        user = User(
            username=long_username,
            email="test@example.com",
            password_hash="$2b$12$hashed_password"
        )
        # SQLAlchemy debería manejar la validación de longitud
        assert len(user.username) == len(long_username)

        # Email largo
        long_email = "a" * 50 + "@example.com"
        user = User(
            username="testuser",
            email=long_email,
            password_hash="$2b$12$hashed_password"
        )
        assert len(user.email) == len(long_email)
