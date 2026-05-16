"""
Interface de Repositorio de Usuarios - Principio de Segregación de Interfaces
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.models.user import User
from app.types.enums import UserRole


class IUserRepository(ABC):
    """
    Interface para repositorio de usuarios.
    Define el contrato para operaciones de base de datos de usuarios.
    """

    # --- Consultas básicas ---

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Obtiene un usuario por ID."""
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Obtiene un usuario por nombre de usuario."""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Obtiene un usuario por email."""
        pass

    @abstractmethod
    async def get_pending_users(self) -> List[User]:
        """Obtiene usuarios pendientes de aprobación."""
        pass

    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
    ) -> List[User]:
        """
        Lista usuarios con filtros y paginación.
        """
        pass

    # --- Existencia ---

    @abstractmethod
    async def exists_by_username(self, username: str) -> bool:
        """Verifica si existe un usuario por username."""
        pass

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Verifica si existe un usuario por email."""
        pass

    # --- Operaciones de escritura ---

    @abstractmethod
    async def create(self, user_data: Dict[str, Any]) -> User:
        """Crea un nuevo usuario. Devuelve el usuario creado."""
        pass

    @abstractmethod
    async def update(self, user_id: int, update_data: Dict[str, Any]) -> Optional[User]:
        """
        Actualiza un usuario existente.
        Devuelve el usuario actualizado o None si no existe.
        """
        pass

    @abstractmethod
    async def delete(self, user_id: int) -> Optional[User]:
        """
        Elimina un usuario (borrado físico).
        Devuelve el usuario eliminado o None si no existe.
        """
        pass

    # --- Estadísticas y agrupaciones ---

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """
        Estadísticas generales de usuarios.
        Returns:
            Dict con total, by_role, by_status, by_origin,
            locked_accounts, new_this_week
        """
        pass

    @abstractmethod
    async def get_users_by_origin(self) -> List[Dict[str, Any]]:
        """
        Usuarios agrupados por origen.
        Returns:
            Lista de dicts con origin, users, count
        """
        pass
