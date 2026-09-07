"""
Tests para endpoints de Modules.
Cubren CRUD completo y validaciones.
"""
import pytest
from httpx import AsyncClient


async def _get_auth_token(client: AsyncClient, db_session) -> str:
    """Login y retorna el JWT."""
    from app.models.user import User
    from app.types.enums import UserRole, UserStatus
    from app.core.security import get_password_hash

    user = User(
        username="admin_modules",
        email="admin_mod@test.com",
        full_name="Admin Modules",
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


@pytest.mark.asyncio
class TestModuleEndpoints:
    """Tests para CRUD de módulos."""

    async def test_create_module(self, client: AsyncClient, db_session):
        """POST /modules/ crea un módulo nuevo."""
        token = await _get_auth_token(client, db_session)
        response = await client.post(
            "/api/v1/modules/",
            json={"id": "test-mod", "name": "Test Module", "description": "Un módulo de prueba"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "test-mod"
        assert data["name"] == "Test Module"
        assert data["is_active"] is True

    async def test_create_module_duplicate_id(self, client: AsyncClient, db_session):
        """POST /modules/ con ID duplicado retorna 409."""
        token = await _get_auth_token(client, db_session)
        await client.post(
            "/api/v1/modules/",
            json={"id": "dup-mod", "name": "First"},
            headers={"Authorization": f"Bearer {token}"},
        )
        response = await client.post(
            "/api/v1/modules/",
            json={"id": "dup-mod", "name": "Second"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 409

    async def test_list_modules(self, client: AsyncClient, db_session):
        """GET /modules/ lista todos los módulos."""
        token = await _get_auth_token(client, db_session)
        await client.post(
            "/api/v1/modules/",
            json={"id": "list-a", "name": "Module A"},
            headers={"Authorization": f"Bearer {token}"},
        )
        await client.post(
            "/api/v1/modules/",
            json={"id": "list-b", "name": "Module B"},
            headers={"Authorization": f"Bearer {token}"},
        )
        response = await client.get(
            "/api/v1/modules/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    async def test_get_module_by_id(self, client: AsyncClient, db_session):
        """GET /modules/{id} retorna un módulo específico."""
        token = await _get_auth_token(client, db_session)
        await client.post(
            "/api/v1/modules/",
            json={"id": "get-mod", "name": "Get Module"},
            headers={"Authorization": f"Bearer {token}"},
        )
        response = await client.get(
            "/api/v1/modules/get-mod",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["id"] == "get-mod"

    async def test_get_module_not_found(self, client: AsyncClient, db_session):
        """GET /modules/{id} con ID inexistente retorna 404."""
        token = await _get_auth_token(client, db_session)
        response = await client.get(
            "/api/v1/modules/nonexistent",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def test_update_module(self, client: AsyncClient, db_session):
        """PUT /modules/{id} actualiza un módulo."""
        token = await _get_auth_token(client, db_session)
        await client.post(
            "/api/v1/modules/",
            json={"id": "upd-mod", "name": "Old Name"},
            headers={"Authorization": f"Bearer {token}"},
        )
        response = await client.put(
            "/api/v1/modules/upd-mod",
            json={"name": "New Name"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    async def test_delete_module(self, client: AsyncClient, db_session):
        """DELETE /modules/{id} elimina un módulo."""
        token = await _get_auth_token(client, db_session)
        await client.post(
            "/api/v1/modules/",
            json={"id": "del-mod", "name": "Delete Me"},
            headers={"Authorization": f"Bearer {token}"},
        )
        response = await client.delete(
            "/api/v1/modules/del-mod",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        # Verificar que ya no existe
        get_res = await client.get(
            "/api/v1/modules/del-mod",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_res.status_code == 404
