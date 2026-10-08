"""
Lógica de dominio para usuarios.
Responsabilidad única: reglas de negocio sobre el estado de un usuario.
No conoce la BD, no conoce FastAPI, no conoce schemas.
"""

from typing import Protocol, runtime_checkable

from app.types.enums import UserRole, UserStatus


@runtime_checkable
class UserEntity(Protocol):
    """
    Protocolo que define los atributos mínimos que necesita UserDomain.
    Cualquier objeto que tenga estos atributos (incluyendo el modelo ORM User)
    cumple con este protocolo — no hay dependencia hacia SQLAlchemy.
    """
    id: int
    role: UserRole
    status: UserStatus
    is_active: bool
    is_locked: bool


class UserDomain:
    """
    Encapsula las reglas de negocio relacionadas con un usuario.
    Trabaja con cualquier objeto que cumpla UserEntity (Protocol),
    lo que permite desacoplarlo del ORM.
    """

    def __init__(self, user: UserEntity):
        self._user = user

    def is_authenticated(self) -> bool:
        """Usuario activo y con status ACTIVE puede operar."""
        return (
            self._user.is_active and
            self._user.status == UserStatus.ACTIVE
        )

    def is_pending_approval(self) -> bool:
        """Usuario registrado pero sin rol asignado aún."""
        return (
            self._user.role == UserRole.NONE or
            self._user.status == UserStatus.PENDING
        )

    def can_login(self) -> bool:
        """NONE y PENDING no pueden acceder al sistema."""
        return (
            self._user.is_active and
            self._user.status == UserStatus.ACTIVE and
            self._user.role != UserRole.NONE and
            not self._user.is_locked
        )

    def is_superadmin(self) -> bool:
        """Administrador de la plataforma SaaS."""
        return self._user.role == UserRole.SUPERADMIN

    def is_admin(self) -> bool:
        """Dueño de negocio o superior."""
        return self._user.role in [UserRole.SUPERADMIN, UserRole.ADMIN]

    def is_manager_or_above(self) -> bool:
        """Manager, admin o superadmin."""
        return self._user.role in [
            UserRole.SUPERADMIN,
            UserRole.ADMIN,
            UserRole.MANAGER
        ]

    def can_assign_role(self, target_role: UserRole) -> bool:
        """
        Determina si este usuario puede asignar un rol específico.
        Solo SUPERADMIN puede asignar SUPERADMIN o ADMIN.
        """
        if target_role in [UserRole.SUPERADMIN, UserRole.ADMIN]:
            return self._user.role == UserRole.SUPERADMIN
        return self.is_admin()

    def can_delete(self, target: UserEntity) -> bool:
        """
        Un ADMIN no puede eliminar a un SUPERADMIN.
        Nadie puede eliminarse a sí mismo.
        """
        if self._user.id == target.id:
            return False
        if self._user.role == UserRole.ADMIN and target.role == UserRole.SUPERADMIN:
            return False
        return self.is_admin()