"""
Servicio de Actualización de Usuarios - Principio de Responsabilidad Única
"""

from typing import Dict, Any, Optional
import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.types.enums import UserRole, UserStatus
from app.core.security import get_password_hash
from app.interfaces.user.IUserRepository import IUserRepository
from app.services.membership.MembershipService import MembershipService
from app.services.user.UserValidationService import UserValidationService
from app.services.email.EmailService import EmailService

logger = logging.getLogger(__name__)


class UserUpdateService:
    """
    Servicio dedicado a operaciones de actualización de usuarios.
    SRP: Única responsabilidad = modificar datos de usuarios.
    """

    def __init__(
        self,
        db: AsyncSession,
        user_repository: IUserRepository,
        membership_service: Optional[MembershipService] = None,
        email_service: Optional[EmailService] = None,
    ):
        self.db = db
        self.user_repository = user_repository
        # Inyectable para tests unitarios sin BD (la suite de servicios
        # mockea db con AsyncMock); por defecto el real sobre la sesión.
        self.membership_service = membership_service or MembershipService(db)
        self.email_service = email_service or EmailService(db)

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

        updated = await self.user_repository.update(user_id, update_data)

        # Mismo criterio que update_user_status (S1): al activar, vincular
        # al tenant de su origin.
        if new_role != UserRole.NONE and updated is not None:
            await self.membership_service.assign_by_origin(updated)

        return updated

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

        previous_status = user.status

        # Actualiza ambos campos: status y is_active
        update_data = {
            "status": new_status,
            "is_active": new_status == UserStatus.ACTIVE,
        }

        updated = await self.user_repository.update(user_id, update_data)

        # Aprobación (S1): al activar, vincular al tenant de su origin.
        # Si origin no matchea ningún tenant, no falla (S5): queda para
        # asignación manual.
        if new_status == UserStatus.ACTIVE and updated is not None:
            await self.membership_service.assign_by_origin(updated)

            # Correo de aprobación (feature approval-email): solo en la
            # transición → ACTIVE (botón Aprobar/Re-aprobar), nunca en
            # ACTIVE repetido. Fail-open: un fallo de envío no rompe la
            # aprobación, solo se loguea.
            if previous_status != UserStatus.ACTIVE:
                try:
                    await self.email_service.send_approval_email(updated)
                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "No se pudo enviar el correo de aprobación "
                        "al user %s: %s",
                        user_id,
                        exc,
                    )

        return updated

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
        # NOTA: CompanyProfile (Fase 2) tendrá empresa, CIF, dirección, IBAN, etc.
        allowed_fields = ["avatar_url"]
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

        update_data = {
            "password_hash": password_hash,
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
                    # Criterio de aprobación unificado (S1): si el bulk
                    # activa la cuenta, vincular al tenant de su origin.
                    if (
                        update_data.get("status") == UserStatus.ACTIVE
                        and updated_user is not None
                    ):
                        await self.membership_service.assign_by_origin(
                            updated_user
                        )
            except Exception as e:
                # Log error pero continuar con otros usuarios
                print(f"Error updating user {user_id}: {e}")

        return updated_users
