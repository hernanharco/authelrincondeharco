"""
Servicio de Usuarios - Principio de Responsabilidad Única
"""

from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.types.enums import UserRole, UserStatus
from app.domain.user_domain import UserDomain
from app.core.security import get_password_hash
from app.interfaces.user.IUserService import IUserService
from app.interfaces.user.IUserRepository import IUserRepository


class UserService(IUserService):
    """
    Implementación concreta del servicio de usuarios.
    Maneja la lógica de negocio de usuarios con validaciones de dominio.
    """

    def __init__(self, db: Session, user_repository: IUserRepository):
        self.db = db
        self.user_repository = user_repository

    async def get_user_by_id(self, user_id: int, current_user: User) -> Optional[User]:
        """
        Obtiene un usuario por ID con validación de permisos.
        """
        domain = UserDomain(current_user)

        # Verificar permisos
        if not domain.is_manager_or_above() and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver este usuario",
            )

        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
            )

        return user

    async def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
        current_user: User = None,
    ) -> List[User]:
        """
        Lista usuarios con filtros y paginación.
        """
        domain = UserDomain(current_user) if current_user else None

        # Verificar permisos
        if not domain or not domain.is_manager_or_above():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para listar usuarios",
            )

        return await self.user_repository.get_all(
            skip=skip, limit=limit, search=search, role=role
        )

    async def create_user(self, user_data: Dict[str, Any], current_user: User) -> User:
        """
        Crea un nuevo usuario con validaciones.
        """
        domain = UserDomain(current_user)

        # Verificar permisos
        if not domain.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para crear usuarios",
            )

        # Verificar que no exista el username
        if await self.user_repository.exists_by_username(user_data.get("username")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de usuario ya existe",
            )

        # Verificar que no exista el email
        if await self.user_repository.exists_by_email(user_data.get("email")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado",
            )

        # Validar rol
        if "role" in user_data:
            if not domain.can_assign_role(user_data["role"]):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permiso para asignar ese rol",
                )
        else:
            user_data["role"] = UserRole.USER

        # Hashear contraseña
        if "password" in user_data:
            user_data["password_hash"] = get_password_hash(user_data.pop("password"))

        # Establecer valores por defecto
        user_data.setdefault("status", UserStatus.ACTIVE)
        user_data.setdefault("is_active", True)
        user_data.setdefault("is_locked", False)
        user_data.setdefault("failed_login_attempts", 0)

        return await self.user_repository.create(user_data)

    async def update_user(
        self, user_id: int, update_data: Dict[str, Any], current_user: User
    ) -> User:
        """
        Actualiza un usuario existente con validaciones.
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
            )

        domain = UserDomain(current_user)

        # Verificar permisos
        if not domain.is_admin() and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para actualizar este usuario",
            )

        # Sin rol privilegiado no puede cambiar campos sensibles
        if not domain.is_admin():
            for field in ["role", "status", "is_active", "is_locked"]:
                update_data.pop(field, None)

        # Validar rol si se está cambiando
        if "role" in update_data:
            if not domain.can_assign_role(update_data["role"]):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permiso para asignar ese rol",
                )

        # Hashear contraseña si se está actualizando
        if "password" in update_data:
            update_data["password_hash"] = get_password_hash(
                update_data.pop("password")
            )

        return await self.user_repository.update(user_id, update_data)

    async def delete_user(self, user_id: int, current_user: User) -> bool:
        """
        Desactiva un usuario (borrado lógico).
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
            )

        domain = UserDomain(current_user)

        # Verificar permisos
        if not domain.can_delete(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para eliminar este usuario",
            )

        return await self.user_repository.delete(user_id)

    async def update_user_role(
        self, user_id: int, new_role: UserRole, current_user: User
    ) -> User:
        """
        Actualiza el rol de un usuario con validaciones.
        """
        if current_user.id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes cambiar tu propio rol",
            )

        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
            )

        domain = UserDomain(current_user)

        if not domain.can_assign_role(new_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para asignar ese rol",
            )

        # Actualizar rol y estado
        update_data = {"role": new_role}

        # Si se asigna un rol válido, activar la cuenta automáticamente
        if new_role != UserRole.NONE:
            update_data.update({"status": UserStatus.ACTIVE, "is_active": True})

        return await self.user_repository.update(user_id, update_data)

    async def get_pending_users(self, current_user: User) -> List[User]:
        """
        Obtiene usuarios pendientes de aprobación.
        """
        domain = UserDomain(current_user)

        if not domain.is_superadmin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los superadministradores pueden ver usuarios pendientes",
            )

        return await self.user_repository.get_pending_users()

    async def get_stats(self, current_user: User = None) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de usuarios.
        """
        if current_user:
            domain = UserDomain(current_user)
            if not domain.is_manager_or_above():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permiso para ver estadísticas",
                )

        return await self.user_repository.get_stats()

    async def get_users_by_origin(
        self, current_user: User = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene usuarios agrupados por origen.
        """
        if current_user:
            domain = UserDomain(current_user)
            if not domain.is_manager_or_above():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permiso para ver usuarios por origen",
                )

        return await self.user_repository.get_users_by_origin()

    async def update_user_status(
        self, user_id: int, new_status: UserStatus, current_user: User
    ) -> User:
        """
        Actualiza el estado de un usuario.
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
            )

        domain = UserDomain(current_user)
        if not domain.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para cambiar el estado de usuarios",
            )

        return await self.user_repository.update(user_id, {"status": new_status})

    async def update_user_lock(
        self, user_id: int, is_locked: bool, current_user: User
    ) -> User:
        """
        Bloquea o desbloquea un usuario.
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
            )

        domain = UserDomain(current_user)
        if not domain.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para bloquear usuarios",
            )

        return await self.user_repository.update(user_id, {"is_locked": is_locked})

    async def update_user_notes(
        self, user_id: int, notes: str, current_user: User
    ) -> User:
        """
        Actualiza las notas de un usuario.
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
            )

        domain = UserDomain(current_user)
        if not domain.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para editar notas de usuarios",
            )

        return await self.user_repository.update(user_id, {"notes": notes})

    # Métodos de compatibilidad para los endpoints existentes
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
    ) -> List[User]:
        """Método de compatibilidad para get_users."""
        return await self.get_users(skip, limit, search, role)

    async def get_by_id(self, user_id: int, current_user: User) -> User:
        """Método de compatibilidad para get_user_by_id."""
        return await self.get_user_by_id(user_id, current_user)

    async def create(self, user_data: Dict[str, Any], current_user: User) -> User:
        """Método de compatibilidad para create_user."""
        return await self.create_user(user_data, current_user)

    async def update(
        self, user_id: int, update_data: Dict[str, Any], current_user: User
    ) -> User:
        """Método de compatibilidad para update_user."""
        return await self.update_user(user_id, update_data, current_user)

    async def delete(self, user_id: int, current_user: User) -> User:
        """Método de compatibilidad para delete_user."""
        await self.delete_user(user_id, current_user)
        return await self.user_repository.get_by_id(user_id)

    async def update_role(
        self, user_id: int, new_role: UserRole, current_user: User
    ) -> User:
        """Método de compatibilidad para update_user_role."""
        return await self.update_user_role(user_id, new_role, current_user)

    async def get_pending(self) -> List[User]:
        """Método de compatibilidad para get_pending_users."""
        return await self.user_repository.get_pending_users()
