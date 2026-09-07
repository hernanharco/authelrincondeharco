"""
Tests para endpoints de Tenants.
Cubren CRUD completo y validaciones.
"""
import uuid
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
