"""
Interface de Servicio de Usuarios - Principio de Segregación de Interfaces
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from app.models.user import User
from app.types.enums import UserRole, UserStatus


class IUserService(ABC):
    """
    Interface para servicios de gestión de usuarios.
    Define el contrato para operaciones CRUD y lógica de negocio de usuarios.
    """
    
    @abstractmethod
    async def get_user_by_id(self, user_id: int, current_user: User) -> Optional[User]:
        """
        Obtiene un usuario por ID con validación de permisos.
        
        Args:
            user_id: ID del usuario a buscar
            current_user: Usuario que realiza la consulta
            
        Returns:
            Usuario encontrado o None
            
        Raises:
            HTTPException: Si no tiene permisos
        """
        pass
    
    @abstractmethod
    async def get_users(self, skip: int = 0, limit: int = 100, 
                       search: Optional[str] = None, 
                       role: Optional[UserRole] = None,
                       current_user: User = None) -> List[User]:
        """
        Lista usuarios con filtros y paginación.
        
        Args:
            skip: Offset para paginación
            limit: Límite de resultados
            search: Término de búsqueda
            role: Filtro por rol
            current_user: Usuario que realiza la consulta
            
        Returns:
            Lista de usuarios
            
        Raises:
            HTTPException: Si no tiene permisos
        """
        pass
    
    @abstractmethod
    async def create_user(self, user_data: Dict[str, Any], 
                         current_user: User) -> User:
        """
        Crea un nuevo usuario con validaciones.
        
        Args:
            user_data: Datos del nuevo usuario
            current_user: Usuario que crea el registro
            
        Returns:
            Usuario creado
            
        Raises:
            HTTPException: Si no tiene permisos o datos inválidos
        """
        pass
    
    @abstractmethod
    async def update_user(self, user_id: int, update_data: Dict[str, Any], 
                         current_user: User) -> User:
        """
        Actualiza un usuario existente con validaciones.
        
        Args:
            user_id: ID del usuario a actualizar
            update_data: Datos a actualizar
            current_user: Usuario que realiza la actualización
            
        Returns:
            Usuario actualizado
            
        Raises:
            HTTPException: Si no tiene permisos o datos inválidos
        """
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: int, current_user: User) -> bool:
        """
        Desactiva un usuario (borrado lógico).
        
        Args:
            user_id: ID del usuario a desactivar
            current_user: Usuario que realiza la acción
            
        Returns:
            True si se desactivó correctamente
            
        Raises:
            HTTPException: Si no tiene permisos
        """
        pass
    
    @abstractmethod
    async def update_user_role(self, user_id: int, new_role: UserRole, 
                              current_user: User) -> User:
        """
        Actualiza el rol de un usuario con validaciones.
        
        Args:
            user_id: ID del usuario
            new_role: Nuevo rol
            current_user: Usuario que realiza el cambio
            
        Returns:
            Usuario con rol actualizado
            
        Raises:
            HTTPException: Si no tiene permisos
        """
        pass
    
    @abstractmethod
    async def get_pending_users(self, current_user: User) -> List[User]:
        """
        Obtiene usuarios pendientes de aprobación.
        
        Args:
            current_user: Usuario que realiza la consulta
            
        Returns:
            Lista de usuarios pendientes
            
        Raises:
            HTTPException: Si no es superadmin
        """
        pass
