"""
TenantModuleRepository — Acceso a datos de tenant_modules.
Implementa ITenantModuleRepository.
"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant_module import TenantModule
from app.interfaces.tenant.ITenantModuleRepository import ITenantModuleRepository


class TenantModuleRepository(ITenantModuleRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_tenant_and_module(
        self, tenant_id: str, module_id: str
    ) -> Optional[TenantModule]:
        result = await self.db.execute(
            select(TenantModule).where(
                TenantModule.tenant_id == tenant_id,
                TenantModule.module_id == module_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_tenant(self, tenant_id: str) -> List[TenantModule]:
        result = await self.db.execute(
            select(TenantModule).where(TenantModule.tenant_id == tenant_id)
        )
        return list(result.scalars().all())

    async def get_by_module(self, module_id: str) -> List[TenantModule]:
        result = await self.db.execute(
            select(TenantModule).where(TenantModule.module_id == module_id)
        )
        return list(result.scalars().all())

    async def get_active_modules_for_tenant(self, tenant_id: str) -> List[TenantModule]:
        result = await self.db.execute(
            select(TenantModule).where(
                TenantModule.tenant_id == tenant_id,
                TenantModule.is_active == True,
            )
        )
        return list(result.scalars().all())

    async def create(self, data: dict) -> TenantModule:
        tenant_module = TenantModule(**data)
        self.db.add(tenant_module)
        await self.db.commit()
        await self.db.refresh(tenant_module)
        return tenant_module

    async def update(
        self, tenant_id: str, module_id: str, data: dict
    ) -> Optional[TenantModule]:
        tenant_module = await self.get_by_tenant_and_module(tenant_id, module_id)
        if not tenant_module:
            return None
        for key, value in data.items():
            if hasattr(tenant_module, key) and value is not None:
                setattr(tenant_module, key, value)
        await self.db.commit()
        await self.db.refresh(tenant_module)
        return tenant_module

    async def delete(self, tenant_id: str, module_id: str) -> Optional[TenantModule]:
        tenant_module = await self.get_by_tenant_and_module(tenant_id, module_id)
        if not tenant_module:
            return None
        await self.db.delete(tenant_module)
        await self.db.commit()
        return tenant_module

    async def exists(self, tenant_id: str, module_id: str) -> bool:
        result = await self.db.execute(
            select(TenantModule).where(
                TenantModule.tenant_id == tenant_id,
                TenantModule.module_id == module_id,
            ).limit(1)
        )
        return result.first() is not None
