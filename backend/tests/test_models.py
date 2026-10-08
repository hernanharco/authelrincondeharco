"""
Tests para modelos de base de datos
Cubren estructura de columnas, defaults y representación del modelo User.

Reescritos contra el modelo actual (Fase 1):
- `full_name` es NOT NULL; defaults de columna (role=USER, status=PENDING,
  is_active=False) se aplican al flush, no en `__init__`.
- `__repr__` muestra solo username + role (sin email).
- Eliminado `test_user_validation`: SQLAlchemy valida al flush, no en el
  constructor.
"""
import pytest
from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String, Time
from app.models.base import Base
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

    def test_user_column_defaults(self):
        """Test valores por defecto de columna (se aplican al flush)"""
        # Los defaults viven en la definición de columna, no en __init__
        columns = User.__table__.columns

        assert columns["role"].default.arg == UserRole.USER
        assert columns["status"].default.arg == UserStatus.PENDING
        assert columns["is_active"].default.arg is False
        assert columns["is_locked"].default.arg is False
        assert columns["failed_login_attempts"].default.arg == 0
        assert columns["login_count"].default.arg == 0

        # Antes del flush, los atributos aún no tienen el default aplicado
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="$2b$12$hashed_password"
        )
        assert user.role is None
        assert user.status is None
        assert user.failed_login_attempts is None

    def test_user_not_null_columns(self):
        """Test columnas obligatorias (NOT NULL)"""
        columns = User.__table__.columns

        assert columns["username"].nullable is False
        assert columns["email"].nullable is False
        assert columns["password_hash"].nullable is False
        assert columns["full_name"].nullable is False

    def test_user_repr(self):
        """Test representación string del usuario (solo username y role)"""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.USER
        )

        repr_str = repr(user)
        assert "testuser" in repr_str
        assert "USER" in repr_str
        # El repr actual no incluye el email
        assert "test@example.com" not in repr_str

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
        """Test campos opcionales (full_name es NOT NULL, ya no es opcional)"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="$2b$12$hashed_password"
        )

        # Campos opcionales pueden ser None
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


class TestIntegridadForeignKeys:
    """Tests de integridad referencial a nivel de metadatos"""

    @staticmethod
    def _familia(tipo):
        """Agrupa tipos de columna en familias comparables (String, Integer, ...)"""
        if isinstance(tipo, String):
            return "string"
        if isinstance(tipo, Boolean):
            return "boolean"
        if isinstance(tipo, Integer):
            return "integer"
        if isinstance(tipo, Numeric):
            return "numeric"
        # Ojo con el orden: DateTime subclasea Date en SQLAlchemy
        if isinstance(tipo, DateTime):
            return "datetime"
        if isinstance(tipo, Date):
            return "date"
        if isinstance(tipo, Time):
            return "time"
        return type(tipo).__name__

    def test_foreign_keys_apuntan_a_columnas_compatibles(self):
        """Test que cada ForeignKey apunta a una columna de tipo compatible

        PostgreSQL rechaza crear una FK si los tipos no son compatibles
        (p. ej. VARCHAR -> INTEGER). SQLite no lo valida, así que verificamos
        los metadatos directamente.
        """
        incompatibles = []

        for nombre_tabla, tabla in Base.metadata.tables.items():
            for columna in tabla.columns:
                for fk in columna.foreign_keys:
                    destino = fk.column  # resuelve contra Base.metadata
                    familia_origen = self._familia(columna.type)
                    familia_destino = self._familia(destino.type)
                    if familia_origen != familia_destino:
                        incompatibles.append(
                            f"{nombre_tabla}.{columna.name} "
                            f"({familia_origen}) -> "
                            f"{destino.table.name}.{destino.name} "
                            f"({familia_destino})"
                        )

        assert not incompatibles, (
            "Foreign keys con tipos de columna incompatibles:\n"
            + "\n".join(incompatibles)
        )
