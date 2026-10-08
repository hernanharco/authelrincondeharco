"""
Dev Login — Solo funciona en modo development.
Permite login sin credenciales para facilitar el desarrollo local.
"""
import os
from fastapi import APIRouter, HTTPException, status
from app.schemas.user import UserLoginResponse
from app.core.config import settings

router = APIRouter()


@router.post("/dev-login", response_model=UserLoginResponse)
async def dev_login():
    """
    Login automático para desarrollo.
    Solo funciona cuando ENVIRONMENT=development.
    Crea un usuario admin si no existe y retorna un JWT.
    """
    # ── Guardia de seguridad ──────────────────────────────────────
    if settings.is_production:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev login no disponible en producción",
        )

    from app.db.session import AsyncSessionLocal
    from app.models.user import User
    from app.models.tenant import Tenant
    from app.models.module import Module
    from app.models.tenant_module import TenantModule
    from app.types.enums import UserRole, UserStatus
    from app.core.security import get_password_hash
    from app.services.auth.TokenService import TokenService
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        # ── Buscar o crear usuario admin ──────────────────────────
        result = await session.execute(
            select(User).where(User.username == "dev_admin")
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                username="dev_admin",
                email="dev@authcore.dev",
                full_name="Dev Admin",
                password_hash=get_password_hash("dev_no_use_in_prod"),
                role=UserRole.SUPERADMIN,
                status=UserStatus.ACTIVE,
                is_active=True,
                origin="dev-login",
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        elif user.email != "dev@authcore.dev":
            # Corregir email si no es el correcto
            user.email = "dev@authcore.dev"
            await session.commit()

        # ── Asignar tenant de ejemplo si no tiene ─────────────────
        if not user.tenant_id:
            # Buscar o crear tenant "rincom"
            result = await session.execute(
                select(Tenant).where(Tenant.slug == "rincom")
            )
            tenant = result.scalar_one_or_none()
            if not tenant:
                import uuid
                tenant = Tenant(id=str(uuid.uuid4()), slug="rincom", name="El Rincón de Harco")
                session.add(tenant)
                await session.commit()
                await session.refresh(tenant)

            # Asignar tenant al usuario
            user.tenant_id = tenant.id
            await session.commit()

            # Asignar módulos al tenant si no tiene
            result = await session.execute(
                select(TenantModule).where(TenantModule.tenant_id == tenant.id)
            )
            existing = result.scalars().first()
            if not existing:
                # Crear módulos si no existen
                for mod_id, mod_name in [("radar", "Sistema Radar WhatsApp"), ("inventory", "Inventario Tiendas")]:
                    result = await session.execute(select(Module).where(Module.id == mod_id))
                    if not result.scalar_one_or_none():
                        session.add(Module(id=mod_id, name=mod_name))
                await session.commit()

                # Asignar ambos módulos al tenant
                for mod_id in ["radar", "inventory"]:
                    session.add(TenantModule(
                        tenant_id=tenant.id,
                        module_id=mod_id,
                        is_active=True,
                        settings={"enabled_providers": ["vinted", "micolet"]} if mod_id == "inventory" else {},
                    ))
                await session.commit()

        # ── Refrescar usuario con relaciones ──────────────────────
        await session.refresh(user)

        # ── Generar JWT ──────────────────────────────────────────
        token_service = TokenService()

        # Construir payload con tenant + modules
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "type": "access",
        }

        # Incluir tenant si tiene
        if user.tenant_id:
            result = await session.execute(select(Tenant).where(Tenant.id == user.tenant_id))
            tenant = result.scalar_one_or_none()
            if tenant:
                token_data["tenant"] = {"id": tenant.id, "slug": tenant.slug, "name": tenant.name}

                # Incluir modules activos
                result = await session.execute(
                    select(TenantModule).where(
                        TenantModule.tenant_id == tenant.id,
                        TenantModule.is_active == True,
                    )
                )
                modules = result.scalars().all()
                if modules:
                    modules_dict = {}
                    for tm in modules:
                        mod_data = {"enabled": True}
                        if tm.settings:
                            mod_data.update(tm.settings)
                        modules_dict[tm.module_id] = mod_data
                    token_data["modules"] = modules_dict

        from datetime import datetime, timezone
        token, expires_at = await token_service.create_access_token(token_data)
        expires_in = int((expires_at - datetime.now(timezone.utc)).total_seconds())

        return UserLoginResponse(
            access_token=token,
            token_type="bearer",
            expires_in=expires_in,
            user=user,
        )
