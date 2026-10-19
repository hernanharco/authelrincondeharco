"""
MembershipService — creación de membresías usuario↔tenant.

Responsabilidad única: vincular un usuario con el tenant de su origen
cuando su cuenta se activa (aprobación). El link se deduce de
`users.origin` contra `tenants.slug` (case-insensitive, tenant activo).

Decisiones de la feature approval-tenant-membership (odd/tasks/):
- Rol de membresía automática: `USER` (ascender a ADMIN a mano si es dueño).
- Idempotente: nunca duplica una membresía existente (uq_user_tenant).
- Si `origin` no matchea ningún tenant, NO falla la aprobación: devuelve
  None y el usuario queda pendiente de asignación manual (S5).
"""
import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.models.user import User
from app.models.user_tenant import UserTenant

# Rol de la membresía creada automáticamente al aprobar (decisión L3 del doc).
DEFAULT_MEMBERSHIP_ROLE = "USER"


class MembershipService:
    """Servicio dedicado a la tabla N:M `user_tenants`."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assign_by_origin(self, user: User) -> Optional[UserTenant]:
        """
        Crea (o devuelve si ya existe) la membresía del usuario en el tenant
        activo cuyo slug coincide con su origin, con rol USER.

        Devuelve la membresía creada/existente, o None cuando no hay match
        (sin origin, sin tenant, o tenant inactivo) — nunca lanza.
        """
        if not user.origin or user.id is None:
            return None

        # Slug único + case-insensitive (origin viene del host del sitio,
        # p. ej. "riderdefensa"; slug "riderdefensa").
        result = await self.db.execute(
            select(Tenant).where(
                func.lower(Tenant.slug) == user.origin.lower(),
                Tenant.is_active.is_(True),
            )
        )
        tenant = result.scalar_one_or_none()
        if tenant is None:
            return None

        # Idempotencia: la membresía puede existir ya (re-aprobación).
        result = await self.db.execute(
            select(UserTenant).where(
                UserTenant.user_id == user.id,
                UserTenant.tenant_id == tenant.id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            return existing

        membership = UserTenant(
            id=str(uuid.uuid4()),
            user_id=user.id,
            tenant_id=tenant.id,
            role=DEFAULT_MEMBERSHIP_ROLE,
        )
        self.db.add(membership)
        await self.db.commit()
        await self.db.refresh(membership)
        return membership
