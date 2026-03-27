"""
Repositorio de Usuarios - Principio de Responsabilidad Única
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models.user import User
from app.types.enums import UserRole, UserStatus
from app.interfaces.user.IUserRepository import IUserRepository


class UserRepository(IUserRepository):
    """
    Implementación concreta del repositorio de usuarios.
    Maneja solo operaciones de base de datos de usuarios.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Obtiene un usuario por ID.
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Obtiene un usuario por nombre de usuario.
        """
        return self.db.query(User).filter(User.username == username).first()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Obtiene un usuario por email.
        """
        return self.db.query(User).filter(User.email == email).first()
    
    async def get_all(self, skip: int = 0, limit: int = 100,
                     search: Optional[str] = None,
                     role: Optional[UserRole] = None,
                     status: Optional[UserStatus] = None) -> List[User]:
        """
        Lista usuarios con filtros y paginación.
        """
        query = self.db.query(User)
        
        # Filtro de búsqueda
        if search:
            query = query.filter(or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            ))
        
        # Filtro por rol
        if role:
            query = query.filter(User.role == role)
        
        # Filtro por estado
        if status:
            query = query.filter(User.status == status)
        
        return query.offset(skip).limit(limit).all()
    
    async def create(self, user_data: Dict[str, Any]) -> User:
        """
        Crea un nuevo usuario.
        """
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    async def update(self, user_id: int, update_data: Dict[str, Any]) -> User:
        """
        Actualiza un usuario existente.
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError("Usuario no encontrado")
        
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    async def delete(self, user_id: int) -> bool:
        """
        Elimina un usuario (borrado lógico).
        """
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        user.is_active = False
        user.status = UserStatus.INACTIVE
        self.db.commit()
        return True
    
    async def count(self, role: Optional[UserRole] = None,
                   status: Optional[UserStatus] = None) -> int:
        """
        Cuenta usuarios por filtros.
        """
        query = self.db.query(User)
        
        if role:
            query = query.filter(User.role == role)
        
        if status:
            query = query.filter(User.status == status)
        
        return query.count()
    
    async def exists_by_username(self, username: str) -> bool:
        """
        Verifica si existe un usuario por username.
        """
        return self.db.query(User).filter(User.username == username).first() is not None
    
    async def exists_by_email(self, email: str) -> bool:
        """
        Verifica si existe un usuario por email.
        """
        return self.db.query(User).filter(User.email == email).first() is not None
    
    async def get_pending_users(self) -> List[User]:
        """
        Obtiene usuarios pendientes de aprobación.
        """
        return self.db.query(User).filter(
            and_(
                User.role == UserRole.NONE,
                User.status == UserStatus.PENDING,
                User.is_active == True
            )
        ).all()
