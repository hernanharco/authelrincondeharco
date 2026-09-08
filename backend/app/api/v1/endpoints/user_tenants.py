"""
Endpoints de UserTenants — Gestión de usuarios ↔ tenants.

Flujo de Tenant Switching:
1. GET  /users/me/tenants       → lista los tenants del usuario actual
2. POST /auth/select-tenant     → genera JWT para un tenant específico
"""
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.models.user_tenant import UserTenant
from app.models.tenant_module import TenantModule
from app.schemas.user_tenant import UserTenantResponse, SelectTenantRequest
from app.core.security import get_current_active_user
from app.services.auth.TokenService import TokenService

router = APIRouter()


@router.get("/me/tenants", response_model=List[UserTenantResponse])
async def get_my_tenants(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna los tenants a los que pertenece el usuario actual.
    SUPERADMIN: ve TODOS los tenants.
    Otros: solo los asignados en user_tenants.
    """
    # SUPERADMIN bypass — ver todos los tenants
    if current_user.role.value == "SUPERADMIN":
        result = await db.execute(select(Tenant).where(Tenant.is_active == True))
        tenants = result.scalars().all()
        return [
            UserTenantResponse(
                id=f"superadmin-{t.id}",
                user_id=str(current_user.id),
                tenant_id=t.id,
                tenant_slug=t.slug,
                tenant_name=t.name,
                role="ADMIN",
                created_at=t.created_at,
            )
            for t in tenants
        ]

    # Usuarios normales — buscar en user_tenants
    result = await db.execute(
        select(UserTenant, Tenant)
        .join(Tenant, UserTenant.tenant_id == Tenant.id)
        .where(UserTenant.user_id == current_user.id)
    )
    rows = result.all()

    return [
        UserTenantResponse(
            id=ut.id,
            user_id=str(ut.user_id),
            tenant_id=ut.tenant_id,
            tenant_slug=tenant.slug,
            tenant_name=tenant.name,
            role=ut.role,
            created_at=ut.created_at,
        )
        for ut, tenant in rows
    ]


@router.post("/select-tenant")
async def select_tenant(
    data: SelectTenantRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Genera un JWT para un tenant específico.
    El usuario debe pertenecer al tenant (o ser SUPERADMIN).
    Retorna: { access_token, tenant, expires_in }
    """
    # Verificar que el usuario tiene acceso al tenant
    is_superadmin = current_user.role.value == "SUPERADMIN"

    if not is_superadmin:
        result = await db.execute(
            select(UserTenant).where(
                UserTenant.user_id == current_user.id,
                UserTenant.tenant_id == data.tenant_id,
            )
        )
        user_tenant = result.scalar_one_or_none()
        if not user_tenant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes acceso a este tenant",
            )

    # Obtener info del tenant
    result = await db.execute(select(Tenant).where(Tenant.id == data.tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")

    # Obtener módulos activos del tenant
    result = await db.execute(
        select(TenantModule).where(
            TenantModule.tenant_id == data.tenant_id,
            TenantModule.is_active == True,
        )
    )
    modules = result.scalars().all()
    modules_dict = {}
    for tm in modules:
        mod_data = {"enabled": True}
        if tm.settings:
            mod_data.update(tm.settings)
        modules_dict[tm.module_id] = mod_data

    # Generar JWT
    token_service = TokenService()
    token_data = {
        "sub": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role.value,
        "type": "access",
        "tenant": {"id": tenant.id, "slug": tenant.slug, "name": tenant.name},
        "modules": modules_dict,
    }

    from datetime import datetime, timezone
    token, expires_at = await token_service.create_access_token(token_data)
    expires_in = int((expires_at - datetime.now(timezone.utc)).total_seconds())

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "tenant": {"id": tenant.id, "slug": tenant.slug, "name": tenant.name},
    }
