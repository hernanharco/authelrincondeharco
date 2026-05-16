"""
app/repositories/UserRepository.py
Responsabilidad única: acceso a datos del usuario.
Implementa IUserRepository para cumplir con el Principio de Inversión de Dependencias.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.types.enums import UserRole, UserStatus
from app.interfaces.user.IUserRepository import IUserRepository


class UserRepository(IUserRepository):
    def __init__(self, db: Session):
        self.db = db

    async def get_stats(self) -> Dict[str, Any]:
        from sqlalchemy import func
        total = self.db.query(func.count(User.id)).scalar() or 0
        by_role = {}
        for role in UserRole:
            count = self.db.query(func.count(User.id)).filter(User.role == role).scalar() or 0
            if count > 0:
                by_role[role.value] = count
        by_status = {}
        for status in UserStatus:
            count = self.db.query(func.count(User.id)).filter(User.status == status).scalar() or 0
            if count > 0:
                by_status[status.value] = count
        by_origin = {}
        users = self.db.query(User.origin).all()
        for (origin,) in users:
            key = origin or "unknown"
            by_origin[key] = by_origin.get(key, 0) + 1
        locked = self.db.query(func.count(User.id)).filter(User.is_locked == True).scalar() or 0
        from datetime import datetime, timedelta, timezone
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        new_this_week = self.db.query(func.count(User.id)).filter(User.created_at >= week_ago).scalar() or 0
        return {
            "total": total,
            "by_role": by_role,
            "by_status": by_status,
            "by_origin": by_origin,
            "locked_accounts": locked,
            "new_this_week": new_this_week,
        }

    async def get_users_by_origin(self) -> List[Dict[str, Any]]:
        users = self.db.query(User).all()
        grouped: Dict[str, List[User]] = {}
        for user in users:
            key = user.origin or "unknown"
            grouped.setdefault(key, []).append(user)
        return [{"origin": k, "users": v, "count": len(v)} for k, v in grouped.items()]

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
    ) -> List[User]:
        query = self.db.query(User)
        if search:
            query = query.filter(
                User.username.ilike(f"%{search}%") |
                User.email.ilike(f"%{search}%") |
                User.full_name.ilike(f"%{search}%")
            )
        if role:
            query = query.filter(User.role == role)
        return query.offset(skip).limit(limit).all()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    async def get_pending_users(self) -> List[User]:
        return self.db.query(User).filter(User.status == UserStatus.PENDING).all()

    async def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    async def get_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    async def exists_by_username(self, username: str) -> bool:
        return self.db.query(User).filter(User.username == username).first() is not None

    async def exists_by_email(self, email: str) -> bool:
        return self.db.query(User).filter(User.email == email).first() is not None

    async def create(self, data: Dict[str, Any]) -> User:
        user = User(**data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    async def update(self, user_id: int, data: Dict[str, Any]) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        for key, value in data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    async def delete(self, user_id: int) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        self.db.delete(user)
        self.db.commit()
        return user
