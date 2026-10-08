"""
Endpoints de TenantModules — Gestión de módulos por tenant.
Todos los endpoints requieren rol ADMIN.
"""
from typing import List
from fastapi import APIRouter, Depends, Query

from app.models.user import User
from app.schemas.tenant_module import (
    TenantModuleResponse,
    TenantModuleCreate,
    TenantModuleUpdate,
)
from app.services.tenant.TenantModuleService import TenantModuleService
from app.api.v1.dependencies import get_tenant_module_service
from app.core.security import get_current_admin_user

router = APIRouter()


@router.get("/tenants/{tenant_id}/modules", response_model=List[TenantModuleResponse])
async def list_tenant_modules(
    tenant_id: str,
    active_only: bool = Query(False, description="Solo módulos activos"),
    service: TenantModuleService = Depends(get_tenant_module_service),
    _current_user: User = Depends(get_current_admin_user),
):
    """Lista los módulos de un tenant. Requiere rol ADMIN."""
    if active_only:
        return await service.get_active_modules(tenant_id)
    return await service.get_by_tenant(tenant_id)


@router.post("/tenants/{tenant_id}/modules", response_model=TenantModuleResponse, status_code=201)
async def assign_module_to_tenant(
    tenant_id: str,
    data: TenantModuleCreate,
    service: TenantModuleService = Depends(get_tenant_module_service),
    _current_user: User = Depends(get_current_admin_user),
):
    """Asigna un módulo a un tenant. Requiere rol ADMIN."""
    return await service.assign_module(
        tenant_id=tenant_id,
        module_id=data.module_id,
        is_active=data.is_active,
        settings=data.settings,
    )


@router.put("/tenants/{tenant_id}/modules/{module_id}", response_model=TenantModuleResponse)
async def update_tenant_module(
    tenant_id: str,
    module_id: str,
    data: TenantModuleUpdate,
    service: TenantModuleService = Depends(get_tenant_module_service),
    _current_user: User = Depends(get_current_admin_user),
):
    """Actualiza la configuración de un módulo para un tenant. Requiere rol ADMIN."""
    return await service.update_settings(
        tenant_id=tenant_id,
        module_id=module_id,
        is_active=data.is_active,
        settings=data.settings,
    )


@router.delete("/tenants/{tenant_id}/modules/{module_id}", response_model=TenantModuleResponse)
async def remove_module_from_tenant(
    tenant_id: str,
    module_id: str,
    service: TenantModuleService = Depends(get_tenant_module_service),
    _current_user: User = Depends(get_current_admin_user),
):
    """Remueve un módulo de un tenant. Requiere rol ADMIN."""
    return await service.remove_module(tenant_id, module_id)
