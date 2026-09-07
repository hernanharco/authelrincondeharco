"""
TenantRepository — Acceso a datos de tenants.
Implementa ITenantRepository para cumplir con el Principio de Inversión de Dependencias.
Usa SQLAlchemy 2.0 style async: select() + await db.execute()
"""
import uuid
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.interfaces.tenant.ITenantRepository import ITenantRepository


class TenantRepository(ITenantRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, tenant_id: str) -> Optional[Tenant]:
        result = await self.db.execute(select(Tenant).where(Tenant.id == tenant_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Tenant]:
        result = await self.db.execute(select(Tenant).where(Tenant.slug == slug))
        return result.scalar_one_or_none()

    async def get_all(
        self, skip: int = 0, limit: int = 100, active_only: bool = False
    ) -> List[Tenant]:
        stmt = select(Tenant)
        if active_only:
            stmt = stmt.where(Tenant.is_active == True)
        stmt = stmt.order_by(Tenant.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def exists_by_slug(self, slug: str) -> bool:
        result = await self.db.execute(
            select(Tenant.id).where(Tenant.slug == slug).limit(1)
        )
        return result.first() is not None

    async def create(self, tenant_data: dict) -> Tenant:
        if "id" not in tenant_data or not tenant_data["id"]:
            tenant_data["id"] = str(uuid.uuid4())
        tenant = Tenant(**tenant_data)
        self.db.add(tenant)
        await self.db.commit()
        await self.db.refresh(tenant)
        return tenant

    async def update(self, tenant_id: str, data: dict) -> Optional[Tenant]:
        tenant = await self.get_by_id(tenant_id)
        if not tenant:
            return None
        for key, value in data.items():
            if hasattr(tenant, key) and value is not None:
                setattr(tenant, key, value)
        await self.db.commit()
        await self.db.refresh(tenant)
        return tenant

    async def delete(self, tenant_id: str) -> Optional[Tenant]:
        tenant = await self.get_by_id(tenant_id)
        if not tenant:
            return None
        await self.db.delete(tenant)
        await self.db.commit()
        return tenant

    async def count(self) -> int:
        result = await self.db.execute(select(func.count(Tenant.id)))
        return result.scalar() or 0
