"""
Seed script — Inserta tenants, modules y asignaciones iniciales.
Ejecutar una sola vez después de crear las tablas.

Uso:
  cd backend
  poetry run python -m scripts.seed_tenants
"""
import asyncio
import uuid
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.tenant import Tenant
from app.models.module import Module
from app.models.tenant_module import TenantModule


# ══════════════════════════════════════════════════════════════════
# DATOS INICIALES
# ══════════════════════════════════════════════════════════════════

TENANTS = [
    {"slug": "rincom", "name": "El Rincón de Harco"},
    {"slug": "nanatamoda", "name": "Nanata Moda"},
    {"slug": "tiendanan", "name": "TiendaNan"},
    {"slug": "tapiceriarincon", "name": "Tapicería Rincón"},
    {"slug": "cafemitierra", "name": "Café Mi Tierra"},
]

MODULES = [
    {
        "id": "radar",
        "name": "Sistema Radar WhatsApp",
        "description": "Asistente WhatsApp con IA para atención al cliente",
    },
    {
        "id": "inventory",
        "name": "Inventario Tiendas",
        "description": "Scraping y gestión de inventario multi-proveedor",
    },
]

# (tenant_slug, module_id, is_active, settings)
TENANT_MODULES = [
    ("rincom", "radar", True, {"phone": "+34634405549"}),
    ("nanatamoda", "radar", True, {}),
    ("nanatamoda", "inventory", True, {"enabled_providers": ["vinted", "micolet"], "sync_interval_minutes": 15}),
    ("tiendanan", "radar", True, {}),
    ("tiendanan", "inventory", True, {"enabled_providers": ["amway"], "sync_interval_minutes": 60}),
]


async def seed():
    async with AsyncSessionLocal() as session:
        # ── Tenants ──────────────────────────────────────────────
        tenant_map = {}  # slug → id
        for t in TENANTS:
            result = await session.execute(
                select(Tenant).where(Tenant.slug == t["slug"])
            )
            tenant = result.scalar_one_or_none()
            if not tenant:
                tenant = Tenant(id=str(uuid.uuid4()), **t)
                session.add(tenant)
                print(f"  ✅ Tenant creado: {t['slug']}")
            else:
                print(f"  ⏭️  Tenant ya existe: {t['slug']}")
            tenant_map[t["slug"]] = tenant.id

        await session.commit()

        # ── Modules ──────────────────────────────────────────────
        for m in MODULES:
            result = await session.execute(
                select(Module).where(Module.id == m["id"])
            )
            module = result.scalar_one_or_none()
            if not module:
                module = Module(**m)
                session.add(module)
                print(f"  ✅ Módulo creado: {m['id']}")
            else:
                print(f"  ⏭️  Módulo ya existe: {m['id']}")

        await session.commit()

        # ── TenantModules ────────────────────────────────────────
        for slug, module_id, is_active, settings in TENANT_MODULES:
            tenant_id = tenant_map[slug]
            result = await session.execute(
                select(TenantModule).where(
                    TenantModule.tenant_id == tenant_id,
                    TenantModule.module_id == module_id,
                )
            )
            tm = result.scalar_one_or_none()
            if not tm:
                tm = TenantModule(
                    tenant_id=tenant_id,
                    module_id=module_id,
                    is_active=is_active,
                    settings=settings,
                )
                session.add(tm)
                print(f"  ✅ Asignación: {slug} → {module_id} (active={is_active})")
            else:
                print(f"  ⏭️  Asignación ya existe: {slug} → {module_id}")

        await session.commit()
        print("\n🎉 Seed completado.")


if __name__ == "__main__":
    print("🌱 Insertando datos iniciales...\n")
    asyncio.run(seed())
