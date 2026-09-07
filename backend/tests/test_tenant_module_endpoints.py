"""
Tests para endpoints de TenantModules (feature flags).
Cubren asignación, configuración y remoción de módulos por tenant.
"""
import pytest
from httpx import AsyncClient


async def _get_auth_token(client: AsyncClient, db_session) -> str:
    """Login y retorna el JWT."""
    from app.models.user import User
    from app.types.enums import UserRole, UserStatus
    from app.core.security import get_password_hash

    user = User(
        username="admin_tm",
        email="admin_tm@test.com",
        full_name="Admin TM",
        password_hash=get_password_hash("testpass123"),
        role=UserRole.SUPERADMIN,
        status=UserStatus.ACTIVE,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

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


async def _setup_tenant_and_module(client: AsyncClient, token: str) -> tuple:
    """Crea un tenant y un módulo, retorna (tenant_id, module_id)."""
    tenant_res = await client.post(
        "/api/v1/tenants/",
        json={"slug": "tm-test", "name": "TM Test"},
        headers={"Authorization": f"Bearer {token}"},
    )
    tenant_id = tenant_res.json()["id"]

    module_res = await client.post(
        "/api/v1/modules/",
        json={"id": "tm-module", "name": "TM Module"},
        headers={"Authorization": f"Bearer {token}"},
    )
    module_id = module_res.json()["id"]

    return tenant_id, module_id


@pytest.mark.asyncio
class TestTenantModuleEndpoints:
    """Tests para asignación de módulos a tenants."""

    async def test_assign_module_to_tenant(self, client: AsyncClient, db_session):
        """POST /tenant-modules/tenants/{id}/modules asigna un módulo."""
        token = await _get_auth_token(client, db_session)
        tenant_id, module_id = await _setup_tenant_and_module(client, token)

        response = await client.post(
            f"/api/v1/tenant-modules/tenants/{tenant_id}/modules",
            json={"module_id": module_id, "is_active": True},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["tenant_id"] == tenant_id
        assert data["module_id"] == module_id
        assert data["is_active"] is True

    async def test_assign_module_with_settings(self, client: AsyncClient, db_session):
        """POST con settings JSONB guarda la configuración."""
        token = await _get_auth_token(client, db_session)
        tenant_id, module_id = await _setup_tenant_and_module(client, token)

        settings = {"enabled_providers": ["vinted", "micolet"], "sync_interval_minutes": 15}
        response = await client.post(
            f"/api/v1/tenant-modules/tenants/{tenant_id}/modules",
            json={"module_id": module_id, "is_active": True, "settings": settings},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["settings"]["enabled_providers"] == ["vinted", "micolet"]
        assert data["settings"]["sync_interval_minutes"] == 15

    async def test_list_tenant_modules(self, client: AsyncClient, db_session):
        """GET lista los módulos de un tenant."""
        token = await _get_auth_token(client, db_session)
        tenant_id, module_id = await _setup_tenant_and_module(client, token)

        # Asignar
        await client.post(
            f"/api/v1/tenant-modules/tenants/{tenant_id}/modules",
            json={"module_id": module_id, "is_active": True},
            headers={"Authorization": f"Bearer {token}"},
        )
        # Listar
        response = await client.get(
            f"/api/v1/tenant-modules/tenants/{tenant_id}/modules",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["module_id"] == module_id

    async def test_update_tenant_module_settings(self, client: AsyncClient, db_session):
        """PUT actualiza la configuración de un módulo para un tenant."""
        token = await _get_auth_token(client, db_session)
        tenant_id, module_id = await _setup_tenant_and_module(client, token)

        # Asignar
        await client.post(
            f"/api/v1/tenant-modules/tenants/{tenant_id}/modules",
            json={"module_id": module_id, "is_active": True},
            headers={"Authorization": f"Bearer {token}"},
        )
        # Actualizar
        response = await client.put(
            f"/api/v1/tenant-modules/tenants/{tenant_id}/modules/{module_id}",
            json={"is_active": False, "settings": {"new_key": "new_value"}},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        assert data["settings"]["new_key"] == "new_value"

    async def test_remove_module_from_tenant(self, client: AsyncClient, db_session):
        """DELETE remueve un módulo de un tenant."""
        token = await _get_auth_token(client, db_session)
        tenant_id, module_id = await _setup_tenant_and_module(client, token)

        # Asignar
        await client.post(
            f"/api/v1/tenant-modules/tenants/{tenant_id}/modules",
            json={"module_id": module_id, "is_active": True},
            headers={"Authorization": f"Bearer {token}"},
        )
        # Remover
        response = await client.delete(
            f"/api/v1/tenant-modules/tenants/{tenant_id}/modules/{module_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        # Verificar que ya no está
        list_res = await client.get(
            f"/api/v1/tenant-modules/tenants/{tenant_id}/modules",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = list_res.json()
        assert not any(m["module_id"] == module_id for m in data)

    async def test_remove_nonexistent_assignment(self, client: AsyncClient, db_session):
        """DELETE de asignación inexistente retorna 404."""
        token = await _get_auth_token(client, db_session)
        tenant_id, module_id = await _setup_tenant_and_module(client, token)

        response = await client.delete(
            f"/api/v1/tenant-modules/tenants/{tenant_id}/modules/{module_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def test_assign_to_nonexistent_tenant(self, client: AsyncClient, db_session):
        """POST a tenant inexistente retorna 404."""
        token = await _get_auth_token(client, db_session)
        _, module_id = await _setup_tenant_and_module(client, token)

        response = await client.post(
            "/api/v1/tenant-modules/tenants/nonexistent/modules",
            json={"module_id": module_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def test_assign_nonexistent_module(self, client: AsyncClient, db_session):
        """POST con módulo inexistente retorna 404."""
        token = await _get_auth_token(client, db_session)
        tenant_id, _ = await _setup_tenant_and_module(client, token)

        response = await client.post(
            f"/api/v1/tenant-modules/tenants/{tenant_id}/modules",
            json={"module_id": "nonexistent-module"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
