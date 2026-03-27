"""
User model.
Define la estructura de la tabla users en la base de datos.
Sin lógica de negocio — solo mapeo de columnas.
"""

from sqlalchemy import Column, String, Boolean, Enum, Integer, DateTime
from sqlalchemy.sql import func

from app.models.base import Base
from app.types.enums import UserRole, UserStatus


class User(Base):
    """
    Modelo ORM de la tabla users.
    Responsabilidad única: representar la estructura de datos en la BD.
    """

    __tablename__ = "users"

    # Llave primaria (Indispensable para SQLAlchemy)
    id = Column(
        Integer, 
        primary_key=True, 
        index=True, 
        autoincrement=True,
        comment="ID único autoincremental"
    )

    username = Column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="Nombre de usuario único para login"
    )

    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="Correo electrónico único del usuario"
    )

    password_hash = Column(
        String(255),
        nullable=False,
        comment="Contraseña hasheada (bcrypt)"
    )

    full_name = Column(
        String(100),
        nullable=False,
        comment="Nombre completo del usuario"
    )

    role = Column(
        Enum(UserRole),
        default=UserRole.USER,
        nullable=False,
        comment="Rol del usuario en el sistema"
    )

    status = Column(
        Enum(UserStatus),
        default=UserStatus.PENDING,
        nullable=False,
        comment="Estado de la cuenta del usuario"
    )

    is_active = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Bandera para control rápido de acceso"
    )

    # Cambio sugerido: DateTime es mejor para cálculos de tiempo que String
    last_login = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Fecha y hora del último login"
    )

    # Cambio sugerido: Integer para poder operar matemáticamente (+1)
    failed_login_attempts = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Número de intentos fallidos de login"
    )

    is_locked = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Indica si la cuenta está bloqueada por seguridad"
    )

    origin = Column(
        String(255),
        nullable=True,
        comment="URL de origen desde donde el usuario solicitó acceso"
    )

    # Timestamps automáticos (Opcional pero muy recomendado)
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="Fecha de creación del registro"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),  # ← añade esto
        onupdate=func.now(),
        comment="Última actualización del registro"
    )

    def __repr__(self) -> str:
        return f"<User(username='{self.username}', role='{self.role.value}')>"