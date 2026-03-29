"""
Repositorio de Usuarios - Principio de Responsabilidad Única
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, case
from datetime import datetime, timedelta
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

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
    ) -> List[User]:
        """
        Lista usuarios con filtros y paginación.
        """
        query = self.db.query(User)

        # Filtro de búsqueda
        if search:
            query = query.filter(
                or_(
                    User.username.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%"),
                )
            )

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

    async def count(
        self, role: Optional[UserRole] = None, status: Optional[UserStatus] = None
    ) -> int:
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
        return (
            self.db.query(User)
            .filter(
                and_(
                    User.role == UserRole.NONE,
                    User.status == UserStatus.PENDING,
                    User.is_active == True,
                )
            )
            .all()
        )

    async def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de usuarios.
        """
        # Fecha de hace una semana para contar usuarios nuevos
        week_ago = datetime.now() - timedelta(days=7)

        # Query base
        base_query = self.db.query(User)

        # Total de usuarios
        total = base_query.count()

        # Usuarios por rol
        role_stats = (
            self.db.query(User.role, func.count(User.id).label("count"))
            .group_by(User.role)
            .all()
        )
        by_role = {str(role): count for role, count in role_stats}

        # Usuarios por estado
        status_stats = (
            self.db.query(User.status, func.count(User.id).label("count"))
            .group_by(User.status)
            .all()
        )
        by_status = {str(status): count for status, count in status_stats}

        # Usuarios por origen
        origin_stats = (
            self.db.query(
                func.coalesce(User.origin, "unknown"),
                func.count(User.id).label("count"),
            )
            .group_by(func.coalesce(User.origin, "unknown"))
            .all()
        )
        by_origin = {str(origin): count for origin, count in origin_stats}

        # Usuarios nuevos esta semana
        new_this_week = base_query.filter(User.created_at >= week_ago).count()

        # Cuentas bloqueadas
        locked_accounts = base_query.filter(User.is_locked == True).count()

        return {
            "total": total,
            "by_role": by_role,
            "by_status": by_status,
            "by_origin": by_origin,
            "new_this_week": new_this_week,
            "locked_accounts": locked_accounts,
        }

    async def get_users_by_origin(self) -> List[Dict[str, Any]]:
        """
        Obtiene usuarios agrupados por origen con estadísticas.
        """
        origins_data = (
            self.db.query(
                func.coalesce(User.origin, "unknown").label("origin"),
                func.count(User.id).label("total_users"),
                func.sum(case([(User.role == UserRole.SUPERADMIN, 1)], else_=0)).label(
                    "superadmin_count"
                ),
                func.sum(case([(User.role == UserRole.ADMIN, 1)], else_=0)).label(
                    "admin_count"
                ),
                func.sum(case([(User.role == UserRole.MANAGER, 1)], else_=0)).label(
                    "manager_count"
                ),
                func.sum(case([(User.role == UserRole.USER, 1)], else_=0)).label(
                    "user_count"
                ),
                func.sum(case([(User.role == UserRole.VIEWER, 1)], else_=0)).label(
                    "viewer_count"
                ),
                func.sum(case([(User.role == UserRole.NONE, 1)], else_=0)).label(
                    "none_count"
                ),
                func.sum(case([(User.status == UserStatus.ACTIVE, 1)], else_=0)).label(
                    "active_count"
                ),
                func.sum(
                    case([(User.status == UserStatus.INACTIVE, 1)], else_=0)
                ).label("inactive_count"),
                func.sum(
                    case([(User.status == UserStatus.SUSPENDED, 1)], else_=0)
                ).label("suspended_count"),
                func.sum(case([(User.status == UserStatus.PENDING, 1)], else_=0)).label(
                    "pending_count"
                ),
            )
            .group_by(func.coalesce(User.origin, "unknown"))
            .all()
        )

        result = []
        for row in origins_data:
            by_role = {
                "SUPERADMIN": row.superadmin_count or 0,
                "ADMIN": row.admin_count or 0,
                "MANAGER": row.manager_count or 0,
                "USER": row.user_count or 0,
                "VIEWER": row.viewer_count or 0,
                "NONE": row.none_count or 0,
            }

            by_status = {
                "ACTIVE": row.active_count or 0,
                "INACTIVE": row.inactive_count or 0,
                "SUSPENDED": row.suspended_count or 0,
                "PENDING": row.pending_count or 0,
            }

            result.append(
                {
                    "origin": row.origin,
                    "total_users": row.total_users,
                    "by_role": by_role,
                    "by_status": by_status,
                }
            )

        return result
