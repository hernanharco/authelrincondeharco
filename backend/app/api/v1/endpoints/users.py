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
from app.api.v1.dependencies import get_user_service

router = APIRouter()


@router.get("/pending", response_model=List[UserResponse])
async def list_pending_users(
    *,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_superadmin_user),  # solo SUPERADMIN
) -> Any:
    """Lista usuarios pendientes de aprobación — vista del SUPERADMIN."""
    return user_service.get_pending()


@router.get("/", response_model=List[UserResponse])
async def list_users(
    *,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[UserRole] = Query(None),
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_manager_or_admin),
) -> Any:
    return user_service.get_all(skip, limit, search, role)


@router.post("/", response_model=UserResponse)
async def create_user(
    *,
    user_in: UserCreate,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    return user_service.create(user_in.model_dump(), current_user)


@router.get("/me", response_model=UserResponse)
async def read_user_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    *,
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    return user_service.get_by_id(user_id, current_user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    *,
    user_id: int,
    user_in: UserUpdate,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    return user_service.update(
        user_id, user_in.model_dump(exclude_unset=True), current_user
    )


@router.delete("/{user_id}", response_model=UserResponse)
async def delete_user(
    *,
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    return user_service.delete(user_id, current_user)


@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    *,
    user_id: int,
    role_update: RoleUpdate,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    return user_service.update_role(user_id, role_update.role, current_user)


# ```

# ---

# La diferencia es clara. Cada endpoint ahora tiene exactamente **una línea de lógica** — delegar al servicio. Toda la inteligencia vive en `UserService` que a su vez delega las reglas en `UserDomain`. La estructura final queda:
# ```
# api/endpoints/users.py   → recibe HTTP, delega
# services/user_service.py → orquesta BD + dominio
# domain/user_domain.py    → reglas de negocio puras
# types/enums.py           → tipos compartidos
# models/user.py           → estructura de tabla
