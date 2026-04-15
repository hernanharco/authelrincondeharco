"""
Servicio de Actualización de Usuarios - Principio de Responsabilidad Única
"""

from typing import Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.types.enums import UserRole, UserStatus
from app.core.security import get_password_hash
from app.interfaces.user.IUserRepository import IUserRepository
from app.services.user.UserValidationService import UserValidationService


class UserUpdateService:
    """
    Servicio dedicado a operaciones de actualización de usuarios.
    SRP: Única responsabilidad = modificar datos de usuarios.
    """

    def __init__(self, db: Session, user_repository: IUserRepository):
        self.db = db
        self.user_repository = user_repository

    async def update_user(
        self, user_id: int, update_data: Dict[str, Any], current_user: User
    ) -> User:
        """
        Actualiza un usuario existente con validaciones.
        """
        user = await self.user_repository.get_by_id(user_id)
        UserValidationService.validate_user_exists(user)

        UserValidationService.validate_permission_to_update(current_user, user_id)

        # Filtrar campos sensibles si no es admin
        update_data = UserValidationService.filter_sensitive_fields(
            update_data, current_user
        )

        # Validar rol si se está cambiando
        if "role" in update_data:
            UserValidationService.validate_role_assignment(
                current_user, update_data["role"]
            )

        # Hashear contraseña si se está actualizando
        if "password" in update_data:
            update_data["password_hash"] = get_password_hash(
                update_data.pop("password")
            )

        return await self.user_repository.update(user_id, update_data)

    async def update_user_role(
        self, user_id: int, new_role: UserRole, current_user: User
    ) -> User:
        """
        Actualiza el rol de un usuario con validaciones.
        """
        UserValidationService.validate_self_role_change(current_user, user_id)

        user = await self.user_repository.get_by_id(user_id)
        UserValidationService.validate_user_exists(user)

        UserValidationService.validate_role_assignment(current_user, new_role)

        # Actualizar rol y estado
        update_data = {"role": new_role}

        # Si se asigna un rol válido, activar la cuenta automáticamente
        if new_role != UserRole.NONE:
            update_data.update({"status": UserStatus.ACTIVE, "is_active": True})

        return await self.user_repository.update(user_id, update_data)

    async def update_user_status(
        self, user_id: int, new_status: UserStatus, current_user: User
    ) -> User:
        """
        Actualiza el estado de un usuario.
        """
        user = await self.user_repository.get_by_id(user_id)
        UserValidationService.validate_user_exists(user)

        UserValidationService.validate_admin_permission(
            current_user, "cambiar el estado de usuarios"
        )

        # Actualiza ambos campos: status y is_active
        update_data = {
            "status": new_status,
            "is_active": new_status == UserStatus.ACTIVE,
        }

        return await self.user_repository.update(user_id, update_data)

    async def update_user_lock(
        self, user_id: int, is_locked: bool, current_user: User
    ) -> User:
        """
        Bloquea o desbloquea un usuario.
        """
        user = await self.user_repository.get_by_id(user_id)
        UserValidationService.validate_user_exists(user)

        UserValidationService.validate_admin_permission(
            current_user, "bloquear usuarios"
        )

        return await self.user_repository.update(user_id, {"is_locked": is_locked})

    async def update_user_notes(
        self, user_id: int, notes: str, current_user: User
    ) -> User:
        """
        Actualiza las notas de un usuario.
        """
        user = await self.user_repository.get_by_id(user_id)
        UserValidationService.validate_user_exists(user)

        UserValidationService.validate_admin_permission(
            current_user, "editar notas de usuarios"
        )

        return await self.user_repository.update(user_id, {"notes": notes})

    async def update_user_profile(
        self, user_id: int, profile_data: Dict[str, Any], current_user: User
    ) -> User:
        """
        Actualiza datos del perfil de un usuario (campos no sensibles).
        """
        user = await self.user_repository.get_by_id(user_id)
        UserValidationService.validate_user_exists(user)

        UserValidationService.validate_permission_to_update(current_user, user_id)

        # Solo permitir campos de perfil no sensibles
        allowed_fields = ["first_name", "last_name", "phone", "bio", "avatar_url"]
        filtered_data = {k: v for k, v in profile_data.items() if k in allowed_fields}

        return await self.user_repository.update(user_id, filtered_data)

    async def reset_user_password(
        self, user_id: int, new_password: str, current_user: User
    ) -> User:
        """
        Resetea la contraseña de un usuario.
        """
        user = await self.user_repository.get_by_id(user_id)
        UserValidationService.validate_user_exists(user)

        UserValidationService.validate_admin_permission(
            current_user, "resetear contraseñas"
        )

        password_hash = get_password_hash(new_password)

        # Opcional: marcar como que debe cambiar contraseña en próximo login
        update_data = {
            "password_hash": password_hash,
            "must_change_password": True,
            "failed_login_attempts": 0,
            "is_locked": False,
        }

        return await self.user_repository.update(user_id, update_data)

    def prepare_password_hash(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforma 'password' → 'password_hash' hasheado con bcrypt.
        SRP: toda manipulación de credenciales vive en este servicio.
        """
        if "password" in user_data:
            user_data["password_hash"] = get_password_hash(user_data.pop("password"))
        return user_data

    async def bulk_update_users(
        self, user_ids: list[int], update_data: Dict[str, Any], current_user: User
    ) -> list[User]:
        """
        Actualiza múltiples usuarios en lote.
        """
        UserValidationService.validate_admin_permission(
            current_user, "actualizar usuarios en lote"
        )

        # Filtrar campos sensibles
        update_data = UserValidationService.filter_sensitive_fields(
            update_data, current_user
        )

        updated_users = []
        for user_id in user_ids:
            try:
                user = await self.user_repository.get_by_id(user_id)
                if user:
                    updated_user = await self.user_repository.update(
                        user_id, update_data
                    )
                    updated_users.append(updated_user)
            except Exception as e:
                # Log error pero continuar con otros usuarios
                print(f"Error updating user {user_id}: {e}")

        return updated_users
