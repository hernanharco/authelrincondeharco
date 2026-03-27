"""
User Service.
Responsabilidad única: orquestar operaciones de usuarios.
Conoce la BD y delega reglas de negocio al UserDomain.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status

from app.models.user import User
from app.types.enums import UserRole, UserStatus
from app.domain.user_domain import UserDomain
from app.core.security import get_password_hash


class UserService:

    def __init__(self, db: Session):
        self.db = db

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
    ) -> List[User]:
        query = self.db.query(User)

        if search:
            query = query.filter(
                or_(
                    User.username.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%"),
                )
            )

        if role:
            query = query.filter(User.role == role)

        return query.offset(skip).limit(limit).all()

    def get_by_id(self, user_id: int, current_user: User) -> User:
        domain = UserDomain(current_user)
        if not domain.is_manager_or_above() and current_user.id != user_id:
            raise HTTPException(status_code=403, detail="No tienes permiso")

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return user

    def create(self, user_data: dict, current_user: User) -> User:
        domain = UserDomain(current_user)

        # Validar duplicados
        if self.db.query(User).filter(User.username == user_data["username"]).first():
            raise HTTPException(status_code=400, detail="Username ya existe")
        if self.db.query(User).filter(User.email == user_data["email"]).first():
            raise HTTPException(status_code=400, detail="Email ya existe")

        # Validar permiso de asignar el rol solicitado
        target_role = user_data.get("role", UserRole.USER)
        if not domain.can_assign_role(target_role):
            raise HTTPException(
                status_code=403, detail="No tienes permiso para asignar ese rol"
            )

        password = user_data.pop("password")
        user_data.pop("confirm_password", None)
        user_data["password_hash"] = get_password_hash(password)

        user = User(**user_data)
        if user.status == UserStatus.ACTIVE:
            user.is_active = True

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user_id: int, update_data: dict, current_user: User) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="No encontrado")

        domain = UserDomain(current_user)

        if not domain.is_admin() and current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Sin permisos")

        # Sin rol privilegiado no puede cambiar campos sensibles
        if not domain.is_admin():
            for field in ["role", "status", "is_active"]:
                update_data.pop(field, None)

        # Validar rol si se está cambiando
        if "role" in update_data:
            if not domain.can_assign_role(update_data["role"]):
                raise HTTPException(
                    status_code=403, detail="No tienes permiso para asignar ese rol"
                )

        for field, value in update_data.items():
            setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user_id: int, current_user: User) -> dict:
        domain = UserDomain(current_user)

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="No encontrado")

        if not domain.can_delete(user):
            raise HTTPException(
                status_code=403, detail="No tienes permiso para eliminar este usuario"
            )

        user.is_active = False
        user.status = UserStatus.INACTIVE
        self.db.commit()
        return {"message": "Usuario desactivado correctamente"}

    def update_role(self, user_id: int, new_role: UserRole, current_user: User) -> User:
        domain = UserDomain(current_user)

        if current_user.id == user_id:
            raise HTTPException(
                status_code=400, detail="No puedes cambiar tu propio rol"
            )

        if not domain.can_assign_role(new_role):
            raise HTTPException(
                status_code=403, detail="No tienes permiso para asignar ese rol"
            )

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        user.role = new_role

        # ✅ Al asignar un rol válido, activar la cuenta automáticamente
        if new_role != UserRole.NONE:
            user.status = UserStatus.ACTIVE
            user.is_active = True

        self.db.commit()
        self.db.refresh(user)
        return user

    def get_pending(self) -> List[User]:
        """Retorna usuarios con role NONE o status PENDING."""
        return (
            self.db.query(User)
            .filter(or_(User.role == UserRole.NONE, User.status == UserStatus.PENDING))
            .order_by(User.created_at.desc())
            .all()
        )
