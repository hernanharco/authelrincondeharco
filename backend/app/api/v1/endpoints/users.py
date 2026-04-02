from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.user.UserService import UserService
from app.api.v1.dependencies import get_user_service
from app.core.security import (
    get_current_active_user,
    get_current_admin_user,
    get_current_manager_or_admin,
)
from app.schemas.user import (
    UserResponse, UserStats, UsersByOrigin,
    UserCreate, UserUpdate, RoleUpdate, StatusUpdate, LockUpdate, NotesUpdate
)
from app.models.user import User
from app.types.enums import UserRole

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def read_user_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.get("/pending", response_model=List[UserResponse])
async def get_pending_users(
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_admin_user)
):
    return await user_service.get_pending()

@router.get("/stats", response_model=UserStats)
async def get_user_stats(
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_manager_or_admin)
):
    return await user_service.get_stats()

@router.get("/by-origin", response_model=List[UsersByOrigin])
async def get_users_by_origin(
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_manager_or_admin)
):
    return await user_service.get_users_by_origin()

@router.get("/", response_model=List[UserResponse])
async def read_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[UserRole] = Query(None),
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_manager_or_admin)
):
    return await user_service.get_all(skip=skip, limit=limit, search=search, role=role, current_user=current_user)

@router.post("/", response_model=UserResponse)
async def create_user(
    user_in: UserCreate,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_admin_user)
):
    return await user_service.create(user_in.model_dump(), current_user)

@router.get("/{user_id}", response_model=UserResponse)
async def read_user_by_id(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user)
):
    user = await user_service.get_by_id(user_id, current_user)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user)
):
    return await user_service.update(user_id, user_in.model_dump(exclude_unset=True), current_user)

@router.delete("/{user_id}", response_model=UserResponse)
async def delete_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_admin_user)
):
    return await user_service.delete(user_id, current_user)

@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    role_update: RoleUpdate,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_admin_user)
):
    return await user_service.update_role(user_id, role_update.role, current_user)

@router.patch("/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: int,
    status_update: StatusUpdate,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_admin_user)
):
    return await user_service.update_status(user_id, status_update.status, current_user)

@router.patch("/{user_id}/lock", response_model=UserResponse)
async def update_user_lock(
    user_id: int,
    lock_update: LockUpdate,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_admin_user)
):
    return await user_service.update_lock(user_id, lock_update.is_locked, current_user)

@router.post("/{user_id}/notes", response_model=UserResponse)
async def add_user_notes(
    user_id: int,
    notes_update: NotesUpdate,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_admin_user)
):
    return await user_service.update_notes(user_id, notes_update.notes, current_user)
