"""
Tests de los endpoints manuales de membresía (S3 — approval-tenant-membership).

Asignación manual usuario↔tenant desde el panel, como respaldo cuando el
`origin` no matchea ningún `slug`:
- POST   /api/v1/tenants/{tenant_id}/users → alta (idempotente) con rol.
- DELETE /api/v1/tenants/{tenant_id}/users/{user_id} → baja.

Guard admin+ (mismo patrón que el resto de /tenants). El GET de miembros
existente se mantiene intacto (regresión incluida abajo).
"""
import uuid

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import create_access_token
from app.models.tenant import Tenant
from app.models.user import User, UserRole, UserStatus
from app.models.user_tenant import UserTenant

pytestmark = pytest.mark.asyncio


# ── Helpers ──────────────────────────────────────────────────────


def auth_headers(user: User) -> dict:
    token = create_access_token(subject=str(user.id))
    return {"Authorization": f"Bearer {token}"}


async def seed_user(db_session: AsyncSession, **overrides) -> User:
    defaults = dict(
        username=f"user{uuid.uuid4().hex[:8]}",
        email=f"{uuid.uuid4().hex[:8]}@example.com",
        full_name="Membership User",
        password_hash="$2b$12$hashed_password",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        is_active=True,
        is_locked=False,
    )
    defaults.update(overrides)
    user = User(**defaults)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def seed_tenant(db_session: AsyncSession, **overrides) -> Tenant:
    defaults = dict(
        id=str(uuid.uuid4()),
        slug=f"tenant{uuid.uuid4().hex[:6]}",
        name="Manual Tenant",
    )
    defaults.update(overrides)
    tenant = Tenant(**defaults)
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


async def memberships_of(db_session: AsyncSession, user: User) -> list[UserTenant]:
    result = await db_session.execute(
        select(UserTenant)
        .options(selectinload(UserTenant.tenant))
        .where(UserTenant.user_id == user.id)
    )
    return list(result.scalars().all())


# ── POST: alta de membresía ──────────────────────────────────────


class TestAddMember:
    async def test_admin_adds_member_with_default_role(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """POST → 200, membresía creada con rol USER, visible en el GET."""
        admin = await seed_user(
            db_session, username="admin", email="admin@example.com",
            role=UserRole.ADMIN,
        )
        tenant = await seed_tenant(db_session)
        member = await seed_user(db_session)

        response = await client.post(
            f"/api/v1/tenants/{tenant.id}/users",
            json={"user_id": member.id},
            headers=auth_headers(admin),
        )

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["role"] == "USER"
        assert body["tenant_id"] == tenant.id

        memberships = await memberships_of(db_session, member)
        assert len(memberships) == 1
        assert memberships[0].tenant.slug == tenant.slug

        # El GET de miembros existente lo muestra (regresión del contrato)
        listing = await client.get(
            f"/api/v1/tenants/{tenant.id}/users", headers=auth_headers(admin)
        )
        assert listing.status_code == status.HTTP_200_OK
        assert [m["id"] for m in listing.json()] == [member.id]

    async def test_admin_adds_member_as_tenant_admin(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """POST con role=ADMIN → el rol de membresía queda ADMIN (dueño)."""
        admin = await seed_user(
            db_session, username="admin", email="admin@example.com",
            role=UserRole.ADMIN,
        )
        tenant = await seed_tenant(db_session)
        owner = await seed_user(db_session)

        response = await client.post(
            f"/api/v1/tenants/{tenant.id}/users",
            json={"user_id": owner.id, "role": "ADMIN"},
            headers=auth_headers(admin),
        )

        assert response.status_code == status.HTTP_200_OK
        memberships = await memberships_of(db_session, owner)
        assert memberships[0].role == "ADMIN"

    async def test_add_is_idempotent(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Repetir la alta no duplica ni explota por la unique constraint."""
        admin = await seed_user(
            db_session, username="admin", email="admin@example.com",
            role=UserRole.ADMIN,
        )
        tenant = await seed_tenant(db_session)
        member = await seed_user(db_session)

        first = await client.post(
            f"/api/v1/tenants/{tenant.id}/users",
            json={"user_id": member.id},
            headers=auth_headers(admin),
        )
        second = await client.post(
            f"/api/v1/tenants/{tenant.id}/users",
            json={"user_id": member.id},
            headers=auth_headers(admin),
        )

        assert first.status_code == status.HTTP_200_OK
        assert second.status_code == status.HTTP_200_OK
        assert len(await memberships_of(db_session, member)) == 1

    async def test_unknown_tenant_returns_404(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        admin = await seed_user(
            db_session, username="admin", email="admin@example.com",
            role=UserRole.ADMIN,
        )
        member = await seed_user(db_session)

        response = await client.post(
            f"/api/v1/tenants/{uuid.uuid4()}/users",
            json={"user_id": member.id},
            headers=auth_headers(admin),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert await memberships_of(db_session, member) == []

    async def test_unknown_user_returns_404(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        admin = await seed_user(
            db_session, username="admin", email="admin@example.com",
            role=UserRole.ADMIN,
        )
        tenant = await seed_tenant(db_session)

        response = await client.post(
            f"/api/v1/tenants/{tenant.id}/users",
            json={"user_id": 999999},
            headers=auth_headers(admin),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert await memberships_of(db_session, admin) == []

    async def test_invalid_membership_role_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Rol de membresía fuera de {ADMIN, MANAGER, USER, VIEWER} → 4xx."""
        admin = await seed_user(
            db_session, username="admin", email="admin@example.com",
            role=UserRole.ADMIN,
        )
        tenant = await seed_tenant(db_session)
        member = await seed_user(db_session)

        response = await client.post(
            f"/api/v1/tenants/{tenant.id}/users",
            json={"user_id": member.id, "role": "SUPERADMIN"},
            headers=auth_headers(admin),
        )

        assert response.status_code in (400, 422)
        assert await memberships_of(db_session, member) == []

    async def test_non_admin_forbidden(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """USER/VIEWER no puede asignar membresías (guard admin+)."""
        plain = await seed_user(
            db_session, username="plain", email="plain@example.com",
            role=UserRole.USER,
        )
        tenant = await seed_tenant(db_session)
        member = await seed_user(db_session)

        response = await client.post(
            f"/api/v1/tenants/{tenant.id}/users",
            json={"user_id": member.id},
            headers=auth_headers(plain),
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert await memberships_of(db_session, member) == []


# ── DELETE: baja de membresía ────────────────────────────────────


class TestRemoveMember:
    async def test_admin_removes_member(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        admin = await seed_user(
            db_session, username="admin", email="admin@example.com",
            role=UserRole.ADMIN,
        )
        tenant = await seed_tenant(db_session)
        member = await seed_user(db_session)
        db_session.add(
            UserTenant(
                id=str(uuid.uuid4()),
                user_id=member.id,
                tenant_id=tenant.id,
                role="USER",
            )
        )
        await db_session.commit()

        response = await client.delete(
            f"/api/v1/tenants/{tenant.id}/users/{member.id}",
            headers=auth_headers(admin),
        )

        assert response.status_code == status.HTTP_200_OK
        assert await memberships_of(db_session, member) == []
        # El usuario NO se borra: solo la membresía
        assert (
            await db_session.get(User, member.id) is not None
        )

    async def test_remove_non_member_returns_404(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        admin = await seed_user(
            db_session, username="admin", email="admin@example.com",
            role=UserRole.ADMIN,
        )
        tenant = await seed_tenant(db_session)
        member = await seed_user(db_session)

        response = await client.delete(
            f"/api/v1/tenants/{tenant.id}/users/{member.id}",
            headers=auth_headers(admin),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_non_admin_forbidden_to_remove(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        plain = await seed_user(
            db_session, username="plain", email="plain@example.com",
            role=UserRole.USER,
        )
        tenant = await seed_tenant(db_session)
        member = await seed_user(db_session)
        db_session.add(
            UserTenant(
                id=str(uuid.uuid4()),
                user_id=member.id,
                tenant_id=tenant.id,
                role="USER",
            )
        )
        await db_session.commit()

        response = await client.delete(
            f"/api/v1/tenants/{tenant.id}/users/{member.id}",
            headers=auth_headers(plain),
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert len(await memberships_of(db_session, member)) == 1
