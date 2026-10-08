"""
Endpoints de Modules — CRUD completo.
Todos los endpoints requieren rol ADMIN.
"""
from typing import List
from fastapi import APIRouter, Depends, Query

from app.models.user import User
from app.schemas.module import ModuleResponse, ModuleCreate, ModuleUpdate
from app.services.module.ModuleService import ModuleService
from app.api.v1.dependencies import get_module_service
from app.core.security import get_current_admin_user

router = APIRouter()


@router.get("/", response_model=List[ModuleResponse])
async def list_modules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active_only: bool = Query(False, description="Solo módulos activos"),
    module_service: ModuleService = Depends(get_module_service),
    _current_user: User = Depends(get_current_admin_user),
):
    """Lista todos los módulos. Requiere rol ADMIN."""
    return await module_service.get_all(skip=skip, limit=limit, active_only=active_only)


@router.get("/{module_id}", response_model=ModuleResponse)
async def get_module(
    module_id: str,
    module_service: ModuleService = Depends(get_module_service),
    _current_user: User = Depends(get_current_admin_user),
):
    """Obtiene un módulo por ID. Requiere rol ADMIN."""
    return await module_service.get_by_id(module_id)


@router.post("/", response_model=ModuleResponse, status_code=201)
async def create_module(
    data: ModuleCreate,
    module_service: ModuleService = Depends(get_module_service),
    _current_user: User = Depends(get_current_admin_user),
):
    """Crea un nuevo módulo. Requiere rol ADMIN."""
    return await module_service.create(
        module_id=data.id, name=data.name, description=data.description, is_active=data.is_active
    )


@router.put("/{module_id}", response_model=ModuleResponse)
async def update_module(
    module_id: str,
    data: ModuleUpdate,
    module_service: ModuleService = Depends(get_module_service),
    _current_user: User = Depends(get_current_admin_user),
):
    """Actualiza un módulo. Requiere rol ADMIN."""
    return await module_service.update(
        module_id=module_id, name=data.name, description=data.description, is_active=data.is_active
    )


@router.delete("/{module_id}", response_model=ModuleResponse)
async def delete_module(
    module_id: str,
    module_service: ModuleService = Depends(get_module_service),
    _current_user: User = Depends(get_current_admin_user),
):
    """Elimina un módulo. Requiere rol ADMIN."""
    return await module_service.delete(module_id)
