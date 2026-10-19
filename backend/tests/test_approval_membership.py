"""
Tests de la feature approval-tenant-membership (S1, S5).

La aprobación de un usuario debe crear su membresía en `user_tenants`
relacionándolo con el tenant cuyo `slug` coincide con su `users.origin`
(caso-insensitive), con rol `USER`, de forma idempotente. Si el origin no
matchea ningún tenant, la aprobación NO falla: el usuario queda activo y
pendiente de asignación manual (S5).

Se prueba por la API real (`PATCH /users/{id}/status`), que es el camino
del botón de aprobación del panel.
"""
import uuid

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.models.user import User, UserRole, UserStatus
from app.models.user_tenant import UserTenant
from app.schemas.user import StatusUpdate

pytestmark = pytest.mark.asyncio


# ── Helpers ──────────────────────────────────────────────────────


async def seed_user(db_session: AsyncSession, **overrides) -> User:
    defaults = dict(
        username=f"user{uuid.uuid4().hex[:8]}",
        email=f"{uuid.uuid4().hex[:8]}@example.com",
        full_name="Approved User",
        password_hash="$2b$12$hashed_password",
        role=UserRole.NONE,
        status=UserStatus.PENDING,
        is_active=False,
        is_locked=False,
    )
    defaults.update(overrides)
    user = User(**defaults)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def seed_tenant(db_session: AsyncSession, slug: str, **overrides) -> Tenant:
    defaults = dict(id=str(uuid.uuid4()), slug=slug, name=f"Tenant {slug}")
    defaults.update(overrides)
    tenant = Tenant(**defaults)
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


def auth_headers(user: User) -> dict:
    from app.core.security import create_access_token

    token = create_access_token(subject=str(user.id))
    return {"Authorization": f"Bearer {token}"}


async def memberships_of(db_session: AsyncSession, user: User) -> list[UserTenant]:
    """Membresías del usuario con el tenant ya cargado (JOIN explícito:
    el lazy-load de `.tenant` dispararía IO síncrono → MissingGreenlet)."""
    from sqlalchemy.orm import selectinload

    result = await db_session.execute(
        select(UserTenant)
        .options(selectinload(UserTenant.tenant))
        .where(UserTenant.user_id == user.id)
    )
    return list(result.scalars().all())


async def approve(
    client: AsyncClient, admin: User, target: User
) -> "httpx.Response":
    return await client.patch(
        f"/api/v1/users/{target.id}/status",
        json=StatusUpdate(status=UserStatus.ACTIVE).model_dump(),
        headers=auth_headers(admin),
    )


# ── S1: aprobar vincula al tenant de origen ──────────────────────


class TestApprovalCreatesMembership:
    async def test_approve_links_user_to_origin_tenant(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """origin 'riderdefensa' + slug 'riderdefensa' → membresía con rol USER."""
        admin = await seed_user(
            db_session,
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_active=True,
        )
        await seed_tenant(db_session, slug="riderdefensa")
        target = await seed_user(
            db_session, origin="riderdefensa", username="elianadeseguros",
            email="elianadeseguros@gmail.com",
        )

        response = await approve(client, admin, target)

        assert response.status_code == status.HTTP_200_OK
        # La aprobación sigue funcionando igual (regresión del contrato previo)
        body = response.json()
        assert body["status"] == UserStatus.ACTIVE.value
        assert body["is_active"] is True

        memberships = await memberships_of(db_session, target)
        assert len(memberships) == 1
        assert memberships[0].role == "USER"
        assert memberships[0].tenant.slug == "riderdefensa"

    async def test_origin_match_is_case_insensitive(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """origin 'RiderDefensa' matchea slug 'riderdefensa'."""
        admin = await seed_user(
            db_session, username="admin", email="admin@example.com",
            role=UserRole.ADMIN, status=UserStatus.ACTIVE, is_active=True,
        )
        await seed_tenant(db_session, slug="riderdefensa")
        target = await seed_user(db_session, origin="RiderDefensa")

        response = await approve(client, admin, target)

        assert response.status_code == status.HTTP_200_OK
        memberships = await memberships_of(db_session, target)
        assert len(memberships) == 1
        assert memberships[0].tenant.slug == "riderdefensa"

    async def test_approval_is_idempotent(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Re-aprobar (o aprobar dos veces) nunca duplica la membresía."""
        admin = await seed_user(
            db_session, username="admin", email="admin@example.com",
            role=UserRole.ADMIN, status=UserStatus.ACTIVE, is_active=True,
        )
        await seed_tenant(db_session, slug="riderdefensa")
        target = await seed_user(db_session, origin="riderdefensa")

        first = await approve(client, admin, target)
        second = await approve(client, admin, target)

        assert first.status_code == status.HTTP_200_OK
        assert second.status_code == status.HTTP_200_OK
        memberships = await memberships_of(db_session, target)
        assert len(memberships) == 1

    async def test_does_not_touch_other_tenants_memberships(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """La aprobación solo agrega la membresía de su origin: no inventa filas."""
        admin = await seed_user(
            db_session, username="admin", email="admin@example.com",
            role=UserRole.ADMIN, status=UserStatus.ACTIVE, is_active=True,
        )
        await seed_tenant(db_session, slug="riderdefensa")
        await seed_tenant(db_session, slug="nanatamoda")
        target = await seed_user(db_session, origin="riderdefensa")

        await approve(client, admin, target)

        memberships = await memberships_of(db_session, target)
        assert [m.tenant.slug for m in memberships] == ["riderdefensa"]

    async def test_approval_never_changes_global_role(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Regresión/S4: aprobar solo cambia status+is_active — el rol
        global queda intacto (nunca puede devenir SUPERADMIN por aprobar)."""
        admin = await seed_user(
            db_session, username="admin", email="admin@example.com",
            role=UserRole.ADMIN, status=UserStatus.ACTIVE, is_active=True,
        )
        target = await seed_user(db_session, origin="riderdefensa")
        assert target.role == UserRole.NONE

        response = await approve(client, admin, target)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["role"] == UserRole.NONE.value
        await db_session.refresh(target)
        assert target.role == UserRole.NONE


# ── S1: otros caminos que activan la cuenta (T2) ───────────────


class TestOtherActivationPaths:
    async def test_bulk_update_active_creates_membership(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """PATCH /users/bulk-update con status ACTIVE también vincula (S1)."""
        admin = await seed_user(
            db_session, username="admin", email="admin@example.com",
            role=UserRole.ADMIN, status=UserStatus.ACTIVE, is_active=True,
        )
        await seed_tenant(db_session, slug="riderdefensa")
        t1 = await seed_user(db_session, origin="riderdefensa")
        t2 = await seed_user(db_session, origin="riderdefensa")

        response = await client.patch(
            "/api/v1/users/bulk-update",
            json={
                "user_ids": [t1.id, t2.id],
                "update_data": {"status": UserStatus.ACTIVE.value},
            },
            headers=auth_headers(admin),
        )

        assert response.status_code == status.HTTP_200_OK
        # Regresión: el contrato previo del bulk sigue igual (lista actualizada)
        assert len(response.json()) == 2
        for target in (t1, t2):
            memberships = await memberships_of(db_session, target)
            assert len(memberships) == 1
            assert memberships[0].tenant.slug == "riderdefensa"
            assert memberships[0].role == "USER"

    async def test_bulk_update_other_status_creates_nothing(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Bulk con status distinto de ACTIVE no crea membresías."""
        admin = await seed_user(
            db_session, username="admin", email="admin@example.com",
            role=UserRole.ADMIN, status=UserStatus.ACTIVE, is_active=True,
        )
        await seed_tenant(db_session, slug="riderdefensa")
        target = await seed_user(
            db_session, origin="riderdefensa",
            status=UserStatus.ACTIVE, is_active=True,
        )

        response = await client.patch(
            "/api/v1/users/bulk-update",
            json={
                "user_ids": [target.id],
                "update_data": {"status": UserStatus.SUSPENDED.value},
            },
            headers=auth_headers(admin),
        )

        assert response.status_code == status.HTTP_200_OK
        assert await memberships_of(db_session, target) == []

    async def test_role_assignment_that_activates_creates_membership(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """PATCH /users/{id}/role con rol válido auto-activa Y vincula (S1)."""
        admin = await seed_user(
            db_session, username="admin", email="admin@example.com",
            role=UserRole.ADMIN, status=UserStatus.ACTIVE, is_active=True,
        )
        await seed_tenant(db_session, slug="riderdefensa")
        target = await seed_user(db_session, origin="riderdefensa")

        response = await client.patch(
            f"/api/v1/users/{target.id}/role",
            json={"role": UserRole.USER.value},
            headers=auth_headers(admin),
        )

        assert response.status_code == status.HTTP_200_OK
        # Regresión: asignar rol sigue activando la cuenta (contrato previo)
        assert response.json()["status"] == UserStatus.ACTIVE.value
        memberships = await memberships_of(db_session, target)
        assert len(memberships) == 1
        assert memberships[0].tenant.slug == "riderdefensa"


# ── S5: origin sin tenant → sin membresía, sin error ─────────────


class TestApprovalWithoutTenantMatch:
    async def test_unknown_origin_approves_without_membership(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """origin 'rincon' sin tenant 'rincon' → 200, activo, SIN membresía."""
        admin = await seed_user(
            db_session, username="admin", email="admin@example.com",
            role=UserRole.ADMIN, status=UserStatus.ACTIVE, is_active=True,
        )
        await seed_tenant(db_session, slug="rincom")
        target = await seed_user(db_session, origin="rincon")

        response = await approve(client, admin, target)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == UserStatus.ACTIVE.value
        assert await memberships_of(db_session, target) == []

    async def test_null_origin_approves_without_membership(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Usuario sin origin (registro manual) → aprueba sin membresía."""
        admin = await seed_user(
            db_session, username="admin", email="admin@example.com",
            role=UserRole.ADMIN, status=UserStatus.ACTIVE, is_active=True,
        )
        target = await seed_user(db_session, origin=None)

        response = await approve(client, admin, target)

        assert response.status_code == status.HTTP_200_OK
        assert await memberships_of(db_session, target) == []

    async def test_inactive_tenant_is_not_matched(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Tenant desactivado no recibe membresías nuevas."""
        admin = await seed_user(
            db_session, username="admin", email="admin@example.com",
            role=UserRole.ADMIN, status=UserStatus.ACTIVE, is_active=True,
        )
        await seed_tenant(db_session, slug="riderdefensa", is_active=False)
        target = await seed_user(db_session, origin="riderdefensa")

        response = await approve(client, admin, target)

        assert response.status_code == status.HTTP_200_OK
        assert await memberships_of(db_session, target) == []
