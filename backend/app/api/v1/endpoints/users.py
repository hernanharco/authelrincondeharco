"""
User endpoints.
Responsabilidad única: recibir HTTP, delegar al servicio, responder.
Sin lógica de negocio ni acceso directo a BD.
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.types.enums import UserRole
from app.schemas.user import UserCreate, UserResponse, UserUpdate, RoleUpdate
from app.services.user.UserService import UserService
from app.repositories.UserRepository import UserRepository
from app.core.security import (
    get_password_hash,
    get_current_active_user,
    get_current_admin_user,
    get_current_manager_or_admin,
    get_current_superadmin_user,
)

router = APIRouter()


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Dependency injection para UserService."""
    user_repository = UserRepository(db)
    return UserService(db, user_repository)


@router.get("/pending", response_model=List[UserResponse])
async def list_pending_users(
    *,
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_superadmin_user),  # solo SUPERADMIN
) -> Any:
    """Lista usuarios pendientes de aprobación — vista del SUPERADMIN."""
    return UserService(db).get_pending()


@router.get("/", response_model=List[UserResponse])
async def list_users(
    *,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[UserRole] = Query(None),
    current_user: User = Depends(get_current_manager_or_admin),
) -> Any:
    return UserService(db).get_all(skip, limit, search, role)


@router.post("/", response_model=UserResponse)
async def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    return UserService(db).create(user_in.model_dump(), current_user)


@router.get("/me", response_model=UserResponse)
async def read_user_me(current_user: User = Depends(get_current_active_user)) -> Any:
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    return UserService(db).get_by_id(user_id, current_user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    return UserService(db).update(
        user_id, user_in.model_dump(exclude_unset=True), current_user
    )


@router.delete("/{user_id}")
async def delete_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    return UserService(db).delete(user_id, current_user)


@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    role_update: RoleUpdate,
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    return UserService(db).update_role(user_id, role_update.role, current_user)


# ```

# ---

# La diferencia es clara. Cada endpoint ahora tiene exactamente **una línea de lógica** — delegar al servicio. Toda la inteligencia vive en `UserService` que a su vez delega las reglas en `UserDomain`. La estructura final queda:
# ```
# api/endpoints/users.py   → recibe HTTP, delega
# services/user_service.py → orquesta BD + dominio
# domain/user_domain.py    → reglas de negocio puras
# types/enums.py           → tipos compartidos
# models/user.py           → estructura de tabla
