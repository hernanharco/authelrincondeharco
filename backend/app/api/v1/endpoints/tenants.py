"""
Endpoints de Tenants — CRUD completo.
Todos los endpoints requieren rol SUPERADMIN o ADMIN.
"""
from typing import List
from fastapi import APIRouter, Depends, Query

from app.models.user import User
from app.schemas.tenant import (
    TenantResponse,
    TenantCreate,
    TenantUpdate,
    TenantUsageResponse,
    TenantMemberResponse,
    TenantMemberAdd,
)
from app.schemas.user_tenant import UserTenantResponse
from app.services.tenant.TenantService import TenantService
from app.services.membership.MembershipService import MembershipService
from app.api.v1.dependencies import get_tenant_service, get_membership_service
from app.core.security import get_current_admin_user

router = APIRouter()


@router.get("/", response_model=List[TenantResponse])
async def list_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active_only: bool = Query(False, description="Solo tenants activos"),
    tenant_service: TenantService = Depends(get_tenant_service),
    _current_user: User = Depends(get_current_admin_user),
):
    """Lista todos los tenants. Requiere rol ADMIN."""
    return await tenant_service.get_all(skip=skip, limit=limit, active_only=active_only)


# --- Rutas estáticas / compuestas — SIEMPRE antes de /{tenant_id} ---


@router.get("/usage", response_model=List[TenantUsageResponse])
async def tenant_usage(
    tenant_service: TenantService = Depends(get_tenant_service),
    _current_user: User = Depends(get_current_admin_user),
):
    """Ranking de uso por tenant (member count DESC). Requiere rol ADMIN.

    Conteos basados en la membresía `user_tenants` (no en users.tenant_id).
    """
    return await tenant_service.get_usage()


@router.get("/{tenant_id}/users", response_model=List[TenantMemberResponse])
async def list_tenant_users(
    tenant_id: str,
    tenant_service: TenantService = Depends(get_tenant_service),
    _current_user: User = Depends(get_current_admin_user),
):
    """Miembros de un tenant con su rol de membresía. Requiere rol ADMIN.

    `role_tenant` viene de `user_tenants`, no del rol global del usuario.
    `role_global` sí expone `users.role`, para que la vista pinte
    SUPERADMIN cuando el rol de plataforma lo es.
    """
    return await tenant_service.get_tenant_users(tenant_id)


@router.post("/{tenant_id}/users", response_model=UserTenantResponse)
async def add_tenant_member(
    tenant_id: str,
    data: TenantMemberAdd,
    membership_service: MembershipService = Depends(get_membership_service),
    _current_user: User = Depends(get_current_admin_user),
):
    """Alta manual de membresía usuario↔tenant (idempotente). Requiere ADMIN.

    Respaldo del vínculo automático por origin (approval-tenant-membership S3).
    """
    return await membership_service.add_member(
        tenant_id=tenant_id, user_id=data.user_id, role=data.role
    )


@router.delete("/{tenant_id}/users/{user_id}", response_model=UserTenantResponse)
async def remove_tenant_member(
    tenant_id: str,
    user_id: int,
    membership_service: MembershipService = Depends(get_membership_service),
    _current_user: User = Depends(get_current_admin_user),
):
    """Baja de membresía: solo quita la relación, no borra el usuario. Requiere ADMIN."""
    return await membership_service.remove_member(tenant_id=tenant_id, user_id=user_id)


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    tenant_service: TenantService = Depends(get_tenant_service),
    _current_user: User = Depends(get_current_admin_user),
):
    """Obtiene un tenant por ID (UUID). Requiere rol ADMIN."""
    return await tenant_service.get_by_id(tenant_id)


@router.get("/by-slug/{slug}", response_model=TenantResponse)
async def get_tenant_by_slug(
    slug: str,
    tenant_service: TenantService = Depends(get_tenant_service),
    _current_user: User = Depends(get_current_admin_user),
):
    """Obtiene un tenant por slug. Requiere rol ADMIN."""
    return await tenant_service.get_by_slug(slug)


@router.post("/", response_model=TenantResponse, status_code=201)
async def create_tenant(
    data: TenantCreate,
    tenant_service: TenantService = Depends(get_tenant_service),
    _current_user: User = Depends(get_current_admin_user),
):
    """Crea un nuevo tenant. Requiere rol ADMIN."""
    return await tenant_service.create(slug=data.slug, name=data.name, is_active=data.is_active)


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    data: TenantUpdate,
    tenant_service: TenantService = Depends(get_tenant_service),
    _current_user: User = Depends(get_current_admin_user),
):
    """Actualiza un tenant. Requiere rol ADMIN."""
    return await tenant_service.update(
        tenant_id=tenant_id,
        name=data.name,
        is_active=data.is_active,
    )


@router.delete("/{tenant_id}", response_model=TenantResponse)
async def delete_tenant(
    tenant_id: str,
    tenant_service: TenantService = Depends(get_tenant_service),
    _current_user: User = Depends(get_current_admin_user),
):
    """Elimina un tenant. Requiere rol ADMIN."""
    return await tenant_service.delete(tenant_id)
