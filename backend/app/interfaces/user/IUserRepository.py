"""
Interface de Repositorio de Usuarios - Principio de Segregación de Interfaces
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from app.models.user import User
from app.types.enums import UserRole, UserStatus


class IUserRepository(ABC):
    """
    Interface para repositorio de usuarios.
    Define el contrato para operaciones de base de datos de usuarios.
    """
    
    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Obtiene un usuario por ID.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Usuario encontrado o None
        """
        pass
    
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Obtiene un usuario por nombre de usuario.
        
        Args:
            username: Nombre de usuario
            
        Returns:
            Usuario encontrado o None
        """
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Obtiene un usuario por email.
        
        Args:
            email: Email del usuario
            
        Returns:
            Usuario encontrado o None
        """
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100,
                     search: Optional[str] = None,
                     role: Optional[UserRole] = None,
                     status: Optional[UserStatus] = None) -> List[User]:
        """
        Lista usuarios con filtros y paginación.
        
        Args:
            skip: Offset para paginación
            limit: Límite de resultados
            search: Término de búsqueda
            role: Filtro por rol
            status: Filtro por estado
            
        Returns:
            Lista de usuarios
        """
        pass
    
    @abstractmethod
    async def create(self, user_data: Dict[str, Any]) -> User:
        """
        Crea un nuevo usuario.
        
        Args:
            user_data: Datos del usuario
            
        Returns:
            Usuario creado
        """
        pass
    
    @abstractmethod
    async def update(self, user_id: int, update_data: Dict[str, Any]) -> User:
        """
        Actualiza un usuario existente.
        
        Args:
            user_id: ID del usuario
            update_data: Datos a actualizar
            
        Returns:
            Usuario actualizado
        """
        pass
    
    @abstractmethod
    async def delete(self, user_id: int) -> bool:
        """
        Elimina un usuario (borrado lógico).
        
        Args:
            user_id: ID del usuario
            
        Returns:
            True si se eliminó correctamente
        """
        pass
    
    @abstractmethod
    async def count(self, role: Optional[UserRole] = None,
                   status: Optional[UserStatus] = None) -> int:
        """
        Cuenta usuarios por filtros.
        
        Args:
            role: Filtro por rol
            status: Filtro por estado
            
        Returns:
            Número de usuarios
        """
        pass
    
    @abstractmethod
    async def exists_by_username(self, username: str) -> bool:
        """
        Verifica si existe un usuario por username.
        
        Args:
            username: Nombre de usuario
            
        Returns:
            True si existe
        """
        pass
    
    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """
        Verifica si existe un usuario por email.
        
        Args:
            email: Email del usuario
            
        Returns:
            True si existe
        """
        pass
