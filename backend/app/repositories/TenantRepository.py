"""
TenantRepository — Acceso a datos de tenants.
Implementa ITenantRepository para cumplir con el Principio de Inversión de Dependencias.
Usa SQLAlchemy 2.0 style async: select() + await db.execute()
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.models.user import User
from app.models.user_tenant import UserTenant
from app.types.enums import UserStatus
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

    async def get_usage(self) -> List[Dict[str, Any]]:
        """Ranking de uso por tenant ordenado por nº de miembros (DESC).

        Fuente de membresía: `authharco.user_tenants` (N:M), NO la columna
        legacy `users.tenant_id`. LEFT JOIN desde tenants: un tenant sin
        miembros sigue apareciendo (personas=0, ultimo_acceso=None).
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        stmt = (
            select(
                Tenant.slug,
                Tenant.name,
                func.count(UserTenant.id).label("personas"),
                func.coalesce(
                    func.sum(case((UserTenant.role == "ADMIN", 1), else_=0)), 0
                ).label("admins"),
                func.coalesce(
                    func.sum(case((User.last_login > cutoff, 1), else_=0)), 0
                ).label("activas_30d"),
                func.coalesce(
                    func.sum(case((User.status == UserStatus.ACTIVE, 1), else_=0)),
                    0,
                ).label("activos"),
                func.max(User.last_login).label("ultimo_acceso"),
            )
            .select_from(Tenant)
            .outerjoin(UserTenant, UserTenant.tenant_id == Tenant.id)
            .outerjoin(User, User.id == UserTenant.user_id)
            .group_by(Tenant.id, Tenant.slug, Tenant.name)
            .order_by(func.count(UserTenant.id).desc(), Tenant.slug.asc())
        )
        result = await self.db.execute(stmt)
        return [
            {
                "slug": slug,
                "name": name,
                "personas": int(personas),
                "admins": int(admins),
                "activas_30d": int(activas_30d),
                "activos": int(activos),
                "ultimo_acceso": ultimo_acceso,
            }
            for slug, name, personas, admins, activas_30d, activos, ultimo_acceso
            in result.all()
        ]

    async def get_members_by_tenant(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Miembros de un tenant vía user_tenants (la membresía real).

        `role_tenant` es el rol de la membresía, no el rol global del usuario.
        Orden: last_login DESC NULLS LAST, luego username ASC.
        """
        stmt = (
            select(
                User.id,
                User.username,
                User.email,
                UserTenant.role.label("role_tenant"),
                User.status,
                User.login_count,
                User.last_login,
            )
            .join(UserTenant, UserTenant.user_id == User.id)
            .where(UserTenant.tenant_id == tenant_id)
            .order_by(User.last_login.desc().nulls_last(), User.username.asc())
        )
        result = await self.db.execute(stmt)
        return [
            {
                "id": row.id,
                "username": row.username,
                "email": row.email,
                "role_tenant": row.role_tenant,
                "status": row.status.value
                if isinstance(row.status, UserStatus)
                else row.status,
                "login_count": row.login_count,
                "last_login": row.last_login,
            }
            for row in result.all()
        ]
