"""
Tests para endpoints de Tenants.
Cubren CRUD completo y validaciones.
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient


# ── Helpers ──────────────────────────────────────────────────────

async def _create_admin_user(db_session):
    """Crea un usuario admin para autenticar requests."""
    from app.models.user import User
    from app.types.enums import UserRole, UserStatus
    from app.core.security import get_password_hash

    user = User(
        username="admin_test",
        email="admin@test.com",
        full_name="Admin Test",
        password_hash=get_password_hash("testpass123"),
        role=UserRole.SUPERADMIN,
        status=UserStatus.ACTIVE,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _get_auth_token(client: AsyncClient, db_session) -> str:
    """Login y retorna el JWT."""
    # Crear usuario admin
    user = await _create_admin_user(db_session)

    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin_test", "password": "testpass123"},
    )
    if response.status_code == 200:
        return response.json()["access_token"]

    # Si el login falla (porque auth depende de config), crear token directo
    from app.services.auth.TokenService import TokenService
    token_service = TokenService()
    token, _ = await token_service.create_access_token({
        "sub": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role.value,
        "type": "access",
    })
    return token


# ── Tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestTenantEndpoints:
    """Tests para CRUD de tenants."""

    async def test_create_tenant(self, client: AsyncClient, db_session):
        """POST /tenants/ crea un tenant nuevo."""
        token = await _get_auth_token(client, db_session)
        response = await client.post(
            "/api/v1/tenants/",
            json={"slug": "test-tenant", "name": "Test Tenant"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["slug"] == "test-tenant"
        assert data["name"] == "Test Tenant"
        assert data["is_active"] is True
        assert "id" in data

    async def test_create_tenant_duplicate_slug(self, client: AsyncClient, db_session):
        """POST /tenants/ con slug duplicado retorna 409."""
        token = await _get_auth_token(client, db_session)
        # Crear primero
        await client.post(
            "/api/v1/tenants/",
            json={"slug": "dup-tenant", "name": "First"},
            headers={"Authorization": f"Bearer {token}"},
        )
        # Intentar duplicar
        response = await client.post(
            "/api/v1/tenants/",
            json={"slug": "dup-tenant", "name": "Second"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 409

    async def test_list_tenants(self, client: AsyncClient, db_session):
        """GET /tenants/ lista todos los tenants."""
        token = await _get_auth_token(client, db_session)
        # Crear 2 tenants
        await client.post(
            "/api/v1/tenants/",
            json={"slug": "list-a", "name": "Tenant A"},
            headers={"Authorization": f"Bearer {token}"},
        )
        await client.post(
            "/api/v1/tenants/",
            json={"slug": "list-b", "name": "Tenant B"},
            headers={"Authorization": f"Bearer {token}"},
        )
        # Listar
        response = await client.get(
            "/api/v1/tenants/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    async def test_get_tenant_by_id(self, client: AsyncClient, db_session):
        """GET /tenants/{id} retorna un tenant específico."""
        token = await _get_auth_token(client, db_session)
        # Crear
        create_res = await client.post(
            "/api/v1/tenants/",
            json={"slug": "get-by-id", "name": "Get By ID"},
            headers={"Authorization": f"Bearer {token}"},
        )
        tenant_id = create_res.json()["id"]
        # Obtener
        response = await client.get(
            f"/api/v1/tenants/{tenant_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["slug"] == "get-by-id"

    async def test_get_tenant_by_slug(self, client: AsyncClient, db_session):
        """GET /tenants/by-slug/{slug} retorna un tenant por slug."""
        token = await _get_auth_token(client, db_session)
        await client.post(
            "/api/v1/tenants/",
            json={"slug": "by-slug-test", "name": "By Slug"},
            headers={"Authorization": f"Bearer {token}"},
        )
        response = await client.get(
            "/api/v1/tenants/by-slug/by-slug-test",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["slug"] == "by-slug-test"

    async def test_get_tenant_not_found(self, client: AsyncClient, db_session):
        """GET /tenants/{id} con ID inexistente retorna 404."""
        token = await _get_auth_token(client, db_session)
        response = await client.get(
            "/api/v1/tenants/nonexistent-id",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def test_update_tenant(self, client: AsyncClient, db_session):
        """PUT /tenants/{id} actualiza un tenant."""
        token = await _get_auth_token(client, db_session)
        create_res = await client.post(
            "/api/v1/tenants/",
            json={"slug": "update-test", "name": "Old Name"},
            headers={"Authorization": f"Bearer {token}"},
        )
        tenant_id = create_res.json()["id"]
        # Actualizar
        response = await client.put(
            f"/api/v1/tenants/{tenant_id}",
            json={"name": "New Name"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    async def test_delete_tenant(self, client: AsyncClient, db_session):
        """DELETE /tenants/{id} elimina un tenant."""
        token = await _get_auth_token(client, db_session)
        create_res = await client.post(
            "/api/v1/tenants/",
            json={"slug": "delete-test", "name": "Delete Me"},
            headers={"Authorization": f"Bearer {token}"},
        )
        tenant_id = create_res.json()["id"]
        # Eliminar
        response = await client.delete(
            f"/api/v1/tenants/{tenant_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        # Verificar que ya no existe
        get_res = await client.get(
            f"/api/v1/tenants/{tenant_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_res.status_code == 404

    async def test_requires_admin_role(self, client: AsyncClient, db_session):
        """GET /tenants/ sin token retorna 401."""
        response = await client.get("/api/v1/tenants/")
        assert response.status_code in (401, 403)


# ── Helpers: seeds de tenants + membresías (user_tenants) ────────

def _auth_headers(user) -> dict:
    """Cabecera Authorization con un JWT RS256 real para un usuario persistido."""
    from app.core.security import create_access_token

    return {"Authorization": f"Bearer {create_access_token(subject=str(user.id))}"}


async def _seed_tenant(db_session, slug: str, name: str):
    """Inserta un tenant directamente en BD."""
    from app.models.tenant import Tenant

    tenant = Tenant(id=str(uuid.uuid4()), slug=slug, name=name, is_active=True)
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


async def _seed_plain_user(db_session):
    """Usuario normal (role USER) para probar el guard 403."""
    from app.models.user import User
    from app.types.enums import UserRole, UserStatus

    user = User(
        username="plainuser",
        email="plain@example.com",
        full_name="Plain User",
        password_hash="$2b$12$hashed_password",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _seed_member(
    db_session,
    *,
    username: str,
    email: str,
    tenant_id: str,
    membership_role: str = "USER",
    status=None,
    last_login=None,
    login_count: int = 0,
):
    """Usuario + fila en user_tenants (la fuente real de membresía).

    El rol GLOBAL del usuario es siempre USER: `role_tenant` en la
    respuesta debe venir de la membresía, no de users.role.
    """
    from app.models.user import User
    from app.models.user_tenant import UserTenant
    from app.types.enums import UserRole, UserStatus

    user = User(
        username=username,
        email=email,
        full_name=username.title(),
        password_hash="$2b$12$hashed_password",
        role=UserRole.USER,
        status=status if status is not None else UserStatus.ACTIVE,
        is_active=True,
        last_login=last_login,
        login_count=login_count,
    )
    db_session.add(user)
    await db_session.flush()  # asigna user.id
    db_session.add(
        UserTenant(
            id=str(uuid.uuid4()),
            user_id=user.id,
            tenant_id=tenant_id,
            role=membership_role,
        )
    )
    await db_session.commit()
    return user


async def _seed_usage_scenario(db_session):
    """2 tenants: 'big-corp' con 4 miembros, 'empty-co' con 0.

    - alice: membresía ADMIN, last_login hace 1 día (activa_30d), ACTIVE
    - bob:   last_login hace 40 días (fuera de 30d), ACTIVE
    - carol: PENDING, last_login NULL
    - dave:  ACTIVE, last_login NULL (empate con carol → orden por username)
    """
    from app.types.enums import UserStatus

    big = await _seed_tenant(db_session, "big-corp", "Big Corp")
    empty = await _seed_tenant(db_session, "empty-co", "Empty Co")
    now = datetime.now(timezone.utc)

    await _seed_member(
        db_session,
        username="alice",
        email="alice@big.test",
        tenant_id=big.id,
        membership_role="ADMIN",
        status=UserStatus.ACTIVE,
        last_login=now - timedelta(days=1),
        login_count=5,
    )
    await _seed_member(
        db_session,
        username="bob",
        email="bob@big.test",
        tenant_id=big.id,
        membership_role="USER",
        status=UserStatus.ACTIVE,
        last_login=now - timedelta(days=40),
        login_count=2,
    )
    await _seed_member(
        db_session,
        username="carol",
        email="carol@big.test",
        tenant_id=big.id,
        membership_role="USER",
        status=UserStatus.PENDING,
        last_login=None,
        login_count=0,
    )
    await _seed_member(
        db_session,
        username="dave",
        email="dave@big.test",
        tenant_id=big.id,
        membership_role="USER",
        status=UserStatus.ACTIVE,
        last_login=None,
        login_count=1,
    )
    return big, empty, now


# ── Tests: usage y membresías ────────────────────────────────────

@pytest.mark.asyncio
class TestTenantUsageEndpoints:
    """GET /tenants/usage y GET /tenants/{id}/users (ambos admin-gated)."""

    USAGE_KEYS = {
        "slug",
        "name",
        "personas",
        "admins",
        "activas_30d",
        "activos",
        "ultimo_acceso",
    }
    MEMBER_KEYS = {
        "id",
        "username",
        "email",
        "role_tenant",
        "status",
        "login_count",
        "last_login",
    }

    async def test_usage_ranking_as_admin(self, client: AsyncClient, db_session):
        """GET /tenants/usage como admin → 200, conteos/orden correctos."""
        token = await _get_auth_token(client, db_session)
        big, empty, _ = await _seed_usage_scenario(db_session)

        response = await client.get(
            "/api/v1/tenants/usage",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2  # solo nuestros 2 tenants
        # Orden: member count DESC → big (4) antes que empty (0)
        assert [t["slug"] for t in data] == ["big-corp", "empty-co"]

        big_row = data[0]
        assert set(big_row.keys()) == self.USAGE_KEYS
        assert big_row["name"] == "Big Corp"
        assert big_row["personas"] == 4
        assert big_row["admins"] == 1  # solo alice, por membresía
        assert big_row["activas_30d"] == 1  # solo alice (bob: 40 días)
        assert big_row["activos"] == 3  # alice, bob, dave (carol: PENDING)
        assert big_row["ultimo_acceso"] is not None

        empty_row = data[1]
        assert set(empty_row.keys()) == self.USAGE_KEYS
        assert empty_row["personas"] == 0
        assert empty_row["admins"] == 0
        assert empty_row["activas_30d"] == 0
        assert empty_row["activos"] == 0
        assert empty_row["ultimo_acceso"] is None

    async def test_tenant_users_as_admin(self, client: AsyncClient, db_session):
        """GET /tenants/{id}/users como admin → 200, rol de membresía y orden."""
        token = await _get_auth_token(client, db_session)
        big, empty, _ = await _seed_usage_scenario(db_session)
        auth = {"Authorization": f"Bearer {token}"}

        response = await client.get(f"/api/v1/tenants/{big.id}/users", headers=auth)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4
        # Orden: last_login DESC NULLS LAST, luego username ASC
        assert [m["username"] for m in data] == ["alice", "bob", "carol", "dave"]
        assert set(data[0].keys()) == self.MEMBER_KEYS

        alice = data[0]
        # role_tenant viene de la membresía (ADMIN), no del rol global (USER)
        assert alice["role_tenant"] == "ADMIN"
        assert alice["status"] == "ACTIVE"
        assert alice["login_count"] == 5
        assert {m["role_tenant"] for m in data} == {"ADMIN", "USER"}
        # Solo miembros de ESTE tenant
        assert {m["username"] for m in data} == {"alice", "bob", "carol", "dave"}

        # Tenant sin miembros → 200 con lista vacía
        empty_res = await client.get(f"/api/v1/tenants/{empty.id}/users", headers=auth)
        assert empty_res.status_code == 200
        assert empty_res.json() == []

    async def test_legacy_tenant_id_not_used_as_membership(
        self, client: AsyncClient, db_session
    ):
        """users.tenant_id (legacy) NO cuenta como membresía."""
        from app.models.user import User
        from app.types.enums import UserRole, UserStatus

        token = await _get_auth_token(client, db_session)
        big, _, _ = await _seed_usage_scenario(db_session)

        # Usuario con tenant_id legacy pero SIN fila en user_tenants
        ghost = User(
            username="ghost",
            email="ghost@big.test",
            full_name="Ghost",
            password_hash="$2b$12$hashed_password",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            is_active=True,
            tenant_id=big.id,
        )
        db_session.add(ghost)
        await db_session.commit()
        auth = {"Authorization": f"Bearer {token}"}

        members = await client.get(f"/api/v1/tenants/{big.id}/users", headers=auth)
        assert members.status_code == 200
        assert "ghost" not in [m["username"] for m in members.json()]

        usage = await client.get("/api/v1/tenants/usage", headers=auth)
        assert usage.status_code == 200
        big_row = next(t for t in usage.json() if t["slug"] == "big-corp")
        assert big_row["personas"] == 4  # ghost no cuenta

    async def test_usage_and_members_as_non_admin_forbidden(
        self, client: AsyncClient, db_session
    ):
        """Usuario normal → 403 en ambos endpoints (guard admin+)."""
        plain = await _seed_plain_user(db_session)
        tenant = await _seed_tenant(db_session, "forb-tenant", "Forbidden Tenant")
        headers = _auth_headers(plain)

        usage = await client.get("/api/v1/tenants/usage", headers=headers)
        assert usage.status_code == 403

        members = await client.get(
            f"/api/v1/tenants/{tenant.id}/users", headers=headers
        )
        assert members.status_code == 403

    async def test_tenant_users_unknown_tenant_404(
        self, client: AsyncClient, db_session
    ):
        """GET /tenants/{id}/users con ID inexistente → 404."""
        token = await _get_auth_token(client, db_session)
        response = await client.get(
            f"/api/v1/tenants/{uuid.uuid4()}/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
