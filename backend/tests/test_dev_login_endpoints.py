"""
Tests para POST /api/v1/auth/dev-login (Fase 1).

El endpoint NO pasa por la dependencia `get_db`: abre su propia sesión con
`app.db.session.AsyncSessionLocal` (función → import en tiempo de llamada).
Estos tests parchean ese sessionmaker con el de tests (sqlite, conftest) —
sin red y sin tocar la BD real; `monkeypatch` restaura el original.

Comportamiento REAL codificado:
- `settings.is_production` True → 403 "Dev login no disponible en producción".
- Fuera de producción crea/retoma el usuario `dev_admin` (SUPERADMIN), le
  asigna el tenant "rincom" con los módulos radar + inventory y devuelve JWT.
- Segunda llamada: reutiliza el usuario; si el email es incorrecto lo corrige;
  si el tenant ya tiene módulos NO los duplica.
"""
import pytest
from sqlalchemy import select

from conftest import AsyncTestingSessionLocal

from app.core.config import settings
from app.models.tenant import Tenant
from app.models.tenant_module import TenantModule
from app.models.user import User, UserStatus

pytestmark = pytest.mark.asyncio

DEV_USER = select(User).where(User.username == "dev_admin")


@pytest.fixture
def patch_dev_session(monkeypatch):
    """Apunta AsyncSessionLocal (usado por el endpoint) a la sesión de tests.

    Sin esto, el endpoint abriría sesión contra la BD real de `DATABASE_URL`.
    """
    monkeypatch.setattr(
        "app.db.session.AsyncSessionLocal", AsyncTestingSessionLocal
    )


class TestDevLoginEndpoint:
    """Cobertura de las ramas de dev_login.py (guardia + flujo completo)."""

    async def test_dev_login_disabled_in_production(self, client, monkeypatch):
        """Guardia de seguridad: 403 cuando is_production es True.

        `is_production` es una property calculada sobre ENVIRONMENT; se
        parchea la property (monkeypatch la restaura) sin mutar settings.
        """
        monkeypatch.setattr(
            type(settings), "is_production", property(lambda self: True)
        )

        response = await client.post("/api/v1/auth/dev-login")

        assert response.status_code == 403
        assert response.json()["detail"] == "Dev login no disponible en producción"

    async def test_dev_login_creates_admin_tenant_and_modules(
        self, client, db_session, patch_dev_session
    ):
        """Primer uso: crea dev_admin, tenant "rincom" y ambos módulos."""
        response = await client.post("/api/v1/auth/dev-login")

        assert response.status_code == 200
        data = response.json()
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0
        assert data["access_token"]
        assert data["user"]["username"] == "dev_admin"
        assert data["user"]["email"] == "dev@authcore.dev"
        assert data["user"]["role"] == "SUPERADMIN"
        assert data["user"]["status"] == "ACTIVE"

        # Usuario persistido y activo
        result = await db_session.execute(DEV_USER)
        user = result.scalar_one()
        assert user.role.value == "SUPERADMIN"
        assert user.status == UserStatus.ACTIVE
        assert user.is_active is True
        assert user.origin == "dev-login"
        assert user.password_hash  # hash real, no texto plano

        # Tenant "rincom" creado y asignado
        assert user.tenant_id is not None
        result = await db_session.execute(
            select(Tenant).where(Tenant.slug == "rincom")
        )
        tenant = result.scalar_one()
        assert tenant.id == user.tenant_id
        assert tenant.name == "El Rincón de Harco"

        # Módulos radar + inventory asignados al tenant (con settings)
        result = await db_session.execute(
            select(TenantModule).where(TenantModule.tenant_id == tenant.id)
        )
        modules = sorted(result.scalars().all(), key=lambda tm: tm.module_id)
        assert [tm.module_id for tm in modules] == ["inventory", "radar"]
        inventory = next(tm for tm in modules if tm.module_id == "inventory")
        assert inventory.settings == {"enabled_providers": ["vinted", "micolet"]}
        assert all(tm.is_active for tm in modules)

    async def test_dev_login_second_call_reuses_user(
        self, client, db_session, patch_dev_session
    ):
        """Segunda llamada con todo ya creado: mismo usuario, sin duplicados."""
        first = await client.post("/api/v1/auth/dev-login")
        second = await client.post("/api/v1/auth/dev-login")

        assert first.status_code == 200
        assert second.status_code == 200
        assert second.json()["user"]["id"] == first.json()["user"]["id"]

        result = await db_session.execute(DEV_USER)
        users = result.scalars().all()
        assert len(users) == 1
        assert users[0].email == "dev@authcore.dev"

        result = await db_session.execute(select(Tenant))
        assert len(result.scalars().all()) == 1

    async def test_dev_login_fixes_email_and_keeps_existing_modules(
        self, client, db_session, patch_dev_session
    ):
        """Ramas: email incorrecto → corregido; tenant existente → reasignado;
        módulos existentes → NO duplicados."""
        first = await client.post("/api/v1/auth/dev-login")
        assert first.status_code == 200

        # Estado previo: email incorrecto + tenant borrado del usuario
        result = await db_session.execute(DEV_USER)
        user = result.scalar_one()
        user.email = "wrong@example.com"
        user.tenant_id = None
        await db_session.commit()

        second = await client.post("/api/v1/auth/dev-login")

        assert second.status_code == 200
        assert second.json()["user"]["email"] == "dev@authcore.dev"

        await db_session.refresh(user)
        assert user.email == "dev@authcore.dev"
        assert user.tenant_id is not None

        # Los módulos del tenant NO se duplican (existing → skip)
        result = await db_session.execute(select(TenantModule))
        modules = result.scalars().all()
        assert sorted(tm.module_id for tm in modules) == ["inventory", "radar"]
