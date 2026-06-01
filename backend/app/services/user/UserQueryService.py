"""
Servicio de Consultas de Usuarios - Principio de Responsabilidad Única
"""

from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.types.enums import UserRole
from app.interfaces.user.IUserRepository import IUserRepository
from app.services.user.UserValidationService import UserValidationService


class UserQueryService:
    """
    Servicio dedicado a consultas y estadísticas de usuarios.
    SRP: Única responsabilidad = operaciones de lectura y análisis de datos.
    """

    def __init__(self, db: AsyncSession, user_repository: IUserRepository):
        self.db = db
        self.user_repository = user_repository

    async def get_user_by_id(self, user_id: int, current_user: User) -> Optional[User]:
        """
        Obtiene un usuario por ID con validación de permisos.
        """
        # Validar permisos
        UserValidationService.validate_permission_to_view(current_user, user_id)

        user = await self.user_repository.get_by_id(user_id)
        UserValidationService.validate_user_exists(user)

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
        if current_user:
            UserValidationService.validate_permission_to_list(current_user)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Se requiere autenticación para listar usuarios",
            )

        return await self.user_repository.get_all(
            skip=skip, limit=limit, search=search, role=role
        )

    async def get_pending_users(self, current_user: User) -> List[User]:
        """
        Obtiene usuarios pendientes de aprobación.
        """
        UserValidationService.validate_superadmin_permission(current_user, "ver usuarios pendientes")

        return await self.user_repository.get_pending_users()

    async def get_stats(self, current_user: User = None) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de usuarios.
        """
        if current_user:
            UserValidationService.validate_permission_to_list(current_user)

        return await self.user_repository.get_stats()

    async def get_users_by_origin(
        self, current_user: User = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene usuarios agrupados por origen.
        """
        if current_user:
            UserValidationService.validate_permission_to_list(current_user)

        return await self.user_repository.get_users_by_origin()

    async def search_users(
        self,
        query: str,
        current_user: User,
        limit: int = 50
    ) -> List[User]:
        """
        Busca usuarios por texto con permisos validados.
        """
        UserValidationService.validate_permission_to_list(current_user)

        return await self.user_repository.search_users(query, limit)

    async def get_user_activity_summary(
        self, 
        user_id: int, 
        current_user: User
    ) -> Dict[str, Any]:
        """
        Obtiene un resumen de actividad de un usuario.
        """
        UserValidationService.validate_permission_to_view(current_user, user_id)
        
        user = await self.user_repository.get_by_id(user_id)
        UserValidationService.validate_user_exists(user)

        return await self.user_repository.get_user_activity_summary(user_id)

    async def get_users_by_role(
        self, 
        role: UserRole, 
        current_user: User
    ) -> List[User]:
        """
        Obtiene usuarios filtrados por rol específico.
        """
        UserValidationService.validate_permission_to_list(current_user)

        return await self.user_repository.get_users_by_role(role)

    async def get_active_users_count(self, current_user: User = None) -> int:
        """
        Obtiene el conteo de usuarios activos.
        """
        if current_user:
            UserValidationService.validate_permission_to_list(current_user)

        return await self.user_repository.get_active_users_count()

    async def get_recent_users(
        self, 
        days: int = 30, 
        current_user: User = None
    ) -> List[User]:
        """
        Obtiene usuarios registrados recientemente.
        """
        if current_user:
            UserValidationService.validate_permission_to_list(current_user)

        return await self.user_repository.get_recent_users(days)
