"""
Servicio de Usuarios - Principio de Responsabilidad Única
Refactorizado para seguir SRP usando servicios especializados.
"""

from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.types.enums import UserRole, UserStatus
from app.interfaces.user.IUserService import IUserService
from app.interfaces.user.IUserRepository import IUserRepository
from app.services.user.UserValidationService import UserValidationService
from app.services.user.UserQueryService import UserQueryService
from app.services.user.UserUpdateService import UserUpdateService


class UserService(IUserService):
    """
    Servicio principal de usuarios que coordina servicios especializados.
    Aplica SRP delegando responsabilidades específicas a servicios dedicados.
    Patrón Facade: proporciona una interfaz unificada para el subsistema de usuarios.
    """

    def __init__(self, db: Session, user_repository: IUserRepository):
        self.db = db
        self.user_repository = user_repository

        # Inicializar servicios especializados
        self.validation_service = UserValidationService()
        self.query_service = UserQueryService(db, user_repository)
        self.update_service = UserUpdateService(db, user_repository)

    async def get_user_by_id(self, user_id: int, current_user: User) -> Optional[User]:
        """
        Obtiene un usuario por ID con validación de permisos.
        """
        return await self.query_service.get_user_by_id(user_id, current_user)

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
        return await self.query_service.get_users(
            skip, limit, search, role, current_user
        )

    async def create_user(self, user_data: Dict[str, Any], current_user: User) -> User:
        """
        Crea un nuevo usuario con validaciones.
        """
        # Validar permisos
        UserValidationService.validate_permission_to_create(current_user)

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

        # Validar y preparar datos
        user_data = UserValidationService.validate_user_data_for_creation(
            user_data, current_user
        )

        # Delegar el hash de la contraseña al servicio especializado (SRP)
        user_data = self.update_service.prepare_password_hash(user_data)

        return await self.user_repository.create(user_data)

    async def update_user(
        self, user_id: int, update_data: Dict[str, Any], current_user: User
    ) -> User:
        """
        Actualiza un usuario existente con validaciones.
        """
        return await self.update_service.update_user(user_id, update_data, current_user)

    async def delete_user(self, user_id: int, current_user: User) -> bool:
        """
        Desactiva un usuario (borrado lógico).
        """
        user = await self.user_repository.get_by_id(user_id)
        UserValidationService.validate_user_exists(user)

        UserValidationService.validate_permission_to_delete(current_user, user)

        return await self.user_repository.delete(user_id)

    async def update_user_role(
        self, user_id: int, new_role: UserRole, current_user: User
    ) -> User:
        """
        Actualiza el rol de un usuario con validaciones.
        """
        return await self.update_service.update_user_role(
            user_id, new_role, current_user
        )

    async def get_pending_users(self, current_user: User) -> List[User]:
        """
        Obtiene usuarios pendientes de aprobación.
        """
        return await self.query_service.get_pending_users(current_user)

    async def get_stats(self, current_user: User = None) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de usuarios.
        """
        return await self.query_service.get_stats(current_user)

    async def get_users_by_origin(
        self, current_user: User = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene usuarios agrupados por origen.
        """
        return await self.query_service.get_users_by_origin(current_user)

    async def update_user_status(
        self, user_id: int, new_status: UserStatus, current_user: User
    ) -> User:
        """
        Actualiza el estado de un usuario.
        """
        return await self.update_service.update_user_status(
            user_id, new_status, current_user
        )

    async def update_user_lock(
        self, user_id: int, is_locked: bool, current_user: User
    ) -> User:
        """
        Bloquea o desbloquea un usuario.
        """
        return await self.update_service.update_user_lock(
            user_id, is_locked, current_user
        )

    async def update_user_notes(
        self, user_id: int, notes: str, current_user: User
    ) -> User:
        """
        Actualiza las notas de un usuario.
        """
        return await self.update_service.update_user_notes(user_id, notes, current_user)

    # Métodos de compatibilidad para los endpoints existentes
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
        current_user: User = None,
    ) -> List[User]:
        """Método de compatibilidad para get_users."""
        return await self.get_users(skip, limit, search, role, current_user)

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

    # --- Más métodos de compatibilidad ---

    async def update_status(
        self, user_id: int, new_status: UserStatus, current_user: User
    ) -> User:
        """Método de compatibilidad para update_user_status."""
        return await self.update_user_status(user_id, new_status, current_user)

    async def update_lock(
        self, user_id: int, is_locked: bool, current_user: User
    ) -> User:
        """Método de compatibilidad para update_user_lock."""
        return await self.update_user_lock(user_id, is_locked, current_user)

    async def update_notes(self, user_id: int, notes: str, current_user: User) -> User:
        """Método de compatibilidad para update_user_notes."""
        return await self.update_user_notes(user_id, notes, current_user)

    # --- Métodos adicionales que delegan a servicios especializados ---

    async def search_users(
        self, query: str, current_user: User, limit: int = 50
    ) -> List[User]:
        """Busca usuarios por texto."""
        return await self.query_service.search_users(query, current_user, limit)

    async def get_user_activity_summary(
        self, user_id: int, current_user: User
    ) -> Dict[str, Any]:
        """Obtiene resumen de actividad de un usuario."""
        return await self.query_service.get_user_activity_summary(user_id, current_user)

    async def update_user_profile(
        self, user_id: int, profile_data: Dict[str, Any], current_user: User
    ) -> User:
        """Actualiza datos del perfil de un usuario."""
        return await self.update_service.update_user_profile(
            user_id, profile_data, current_user
        )

    async def reset_user_password(
        self, user_id: int, new_password: str, current_user: User
    ) -> User:
        """Resetea la contraseña de un usuario."""
        return await self.update_service.reset_user_password(
            user_id, new_password, current_user
        )

    async def bulk_update_users(
        self, user_ids: list[int], update_data: Dict[str, Any], current_user: User
    ) -> list[User]:
        """Actualiza múltiples usuarios en lote."""
        return await self.update_service.bulk_update_users(
            user_ids, update_data, current_user
        )
