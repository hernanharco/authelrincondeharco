"""
TenantService — Lógica de negocio de tenants.
Responsabilidad única: orquestar operaciones sobre tenants.
"""
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.tenant import Tenant
from app.interfaces.tenant.ITenantRepository import ITenantRepository
from app.interfaces.tenant.ITenantService import ITenantService


class TenantService(ITenantService):
    def __init__(self, tenant_repository: ITenantRepository):
        self.tenant_repository = tenant_repository

    async def get_by_id(self, tenant_id: str) -> Optional[Tenant]:
        tenant = await self.tenant_repository.get_by_id(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant con id '{tenant_id}' no encontrado",
            )
        return tenant

    async def get_by_slug(self, slug: str) -> Optional[Tenant]:
        tenant = await self.tenant_repository.get_by_slug(slug)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant con slug '{slug}' no encontrado",
            )
        return tenant

    async def get_all(
        self, skip: int = 0, limit: int = 100, active_only: bool = False
    ) -> List[Tenant]:
        return await self.tenant_repository.get_all(skip, limit, active_only)

    async def create(self, slug: str, name: str, is_active: bool = True) -> Tenant:
        # Validar que el slug no exista
        if await self.tenant_repository.exists_by_slug(slug):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un tenant con slug '{slug}'",
            )
        return await self.tenant_repository.create(
            {"slug": slug, "name": name, "is_active": is_active}
        )

    async def update(
        self,
        tenant_id: str,
        name: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[Tenant]:
        # Verificar que existe
        await self.get_by_id(tenant_id)
        return await self.tenant_repository.update(tenant_id, {"name": name, "is_active": is_active})

    async def delete(self, tenant_id: str) -> Optional[Tenant]:
        # Verificar que existe
        await self.get_by_id(tenant_id)
        return await self.tenant_repository.delete(tenant_id)
