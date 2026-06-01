"""
app/repositories/UserRepository.py
Responsabilidad única: acceso a datos del usuario.
Implementa IUserRepository para cumplir con el Principio de Inversión de Dependencias.
Usa SQLAlchemy 2.0 style async: select() + await db.execute()
"""
from typing import Any, Dict, List, Optional
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.types.enums import UserRole, UserStatus
from app.interfaces.user.IUserRepository import IUserRepository


class UserRepository(IUserRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stats(self) -> Dict[str, Any]:
        """
        Estadísticas generales de usuarios con GROUP BY optimizado.
        Antes: 10 queries individuales + carga de todos los registros.
        Ahora: 6 queries async con GROUP BY.
        """
        from datetime import datetime, timedelta, timezone

        # ── Total de usuarios ───────────────────────────────────
        result = await self.db.execute(select(func.count(User.id)))
        total = result.scalar() or 0

        # ── Por rol: 1 query con GROUP BY ───────────────────────
        result = await self.db.execute(
            select(User.role, func.count(User.id)).group_by(User.role)
        )
        by_role = {role: count for role, count in result.all()}

        # ── Por estado: 1 query con GROUP BY ────────────────────
        result = await self.db.execute(
            select(User.status, func.count(User.id)).group_by(User.status)
        )
        by_status = {status: count for status, count in result.all()}

        # ── Por origen: GROUP BY en SQL ─────────────────────────
        result = await self.db.execute(
            select(User.origin, func.count(User.id)).group_by(User.origin)
        )
        by_origin = {(origin or "unknown"): count for origin, count in result.all()}

        # ── Cuentas bloqueadas ──────────────────────────────────
        result = await self.db.execute(
            select(func.count(User.id)).where(User.is_locked == True)
        )
        locked = result.scalar() or 0

        # ── Nuevos esta semana ──────────────────────────────────
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        result = await self.db.execute(
            select(func.count(User.id)).where(User.created_at >= week_ago)
        )
        new_this_week = result.scalar() or 0

        return {
            "total": total,
            "by_role": by_role,
            "by_status": by_status,
            "by_origin": by_origin,
            "locked_accounts": locked,
            "new_this_week": new_this_week,
        }

    async def get_users_by_origin(self) -> List[Dict[str, Any]]:
        """
        Usuarios agrupados por origen con GROUP BY en SQL.
        """
        result = await self.db.execute(
            select(User.origin, func.count(User.id)).group_by(User.origin)
        )
        return [
            {"origin": origin or "unknown", "count": count}
            for origin, count in result.all()
        ]

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
    ) -> List[User]:
        stmt = select(User)
        if search:
            stmt = stmt.where(
                or_(
                    User.username.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%"),
                )
            )
        if role:
            stmt = stmt.where(User.role == role)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_pending_users(self) -> List[User]:
        result = await self.db.execute(
            select(User).where(User.status == UserStatus.PENDING)
        )
        return list(result.scalars().all())

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def exists_by_username(self, username: str) -> bool:
        result = await self.db.execute(
            select(User.id).where(User.username == username).limit(1)
        )
        return result.first() is not None

    async def exists_by_email(self, email: str) -> bool:
        result = await self.db.execute(
            select(User.id).where(User.email == email).limit(1)
        )
        return result.first() is not None

    async def create(self, data: Dict[str, Any]) -> User:
        user = User(**data)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user_id: int, data: Dict[str, Any]) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        for key, value in data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user_id: int) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        await self.db.delete(user)
        await self.db.commit()
        return user
