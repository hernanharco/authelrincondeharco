"""
Dependencias de Inyección - Principio de Inversión de Dependencias

Orden: Singletons → Repositorios → Servicios → Auth (que depende de todos)
"""
from functools import lru_cache
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.db.session import get_db

# ── Interfaces ────────────────────────────────────────────────────
from app.interfaces.auth.ITokenService import ITokenService
from app.interfaces.auth.IOAuthService import IOAuthService
from app.interfaces.auth.IAuthService import IAuthService
from app.interfaces.user.IUserService import IUserService
from app.interfaces.user.IUserRepository import IUserRepository
from app.interfaces.company.ICompanyProfileRepository import ICompanyProfileRepository
from app.interfaces.tenant.ITenantRepository import ITenantRepository
from app.interfaces.tenant.ITenantService import ITenantService
from app.interfaces.module.IModuleRepository import IModuleRepository
from app.interfaces.module.IModuleService import IModuleService

# ── Implementaciones ──────────────────────────────────────────────
from app.services.auth.TokenService import TokenService
from app.services.auth.GoogleOAuthService import GoogleOAuthService
from app.services.auth.AuthService import AuthService
from app.services.user.UserService import UserService
from app.repositories.UserRepository import UserRepository
from app.repositories.CompanyProfileRepository import CompanyProfileRepository
from app.services.company.CompanyProfileService import CompanyProfileService
from app.repositories.TenantRepository import TenantRepository
from app.services.tenant.TenantService import TenantService
from app.repositories.ModuleRepository import ModuleRepository
from app.services.module.ModuleService import ModuleService
from app.repositories.TenantModuleRepository import TenantModuleRepository
from app.services.tenant.TenantModuleService import TenantModuleService


# ══════════════════════════════════════════════════════════════════
# SINGLETONS (cacheados)
# ══════════════════════════════════════════════════════════════════

@lru_cache()
def get_token_service() -> ITokenService:
    return TokenService()


@lru_cache()
def get_oauth_service() -> IOAuthService:
    return GoogleOAuthService()


# ══════════════════════════════════════════════════════════════════
# REPOSITORIES (nuevos por request, dependen de db)
# ══════════════════════════════════════════════════════════════════

def get_user_repository(db: AsyncSession = Depends(get_db)) -> IUserRepository:
    return UserRepository(db)


def get_company_profile_repository(
    db: AsyncSession = Depends(get_db),
) -> ICompanyProfileRepository:
    return CompanyProfileRepository(db)


def get_tenant_repository(db: AsyncSession = Depends(get_db)) -> ITenantRepository:
    return TenantRepository(db)


def get_module_repository(db: AsyncSession = Depends(get_db)) -> IModuleRepository:
    return ModuleRepository(db)


def get_tenant_module_repository(db: AsyncSession = Depends(get_db)):
    return TenantModuleRepository(db)


# ══════════════════════════════════════════════════════════════════
# SERVICES (dependen de repositories)
# ══════════════════════════════════════════════════════════════════

def get_user_service(
    db: AsyncSession = Depends(get_db),
    user_repository: IUserRepository = Depends(get_user_repository),
) -> IUserService:
    return UserService(db, user_repository)


def get_company_profile_service(
    company_repository: ICompanyProfileRepository = Depends(get_company_profile_repository),
) -> CompanyProfileService:
    return CompanyProfileService(company_repository)


def get_tenant_service(
    tenant_repository: ITenantRepository = Depends(get_tenant_repository),
) -> TenantService:
    return TenantService(tenant_repository)


def get_module_service(
    module_repository: IModuleRepository = Depends(get_module_repository),
) -> ModuleService:
    return ModuleService(module_repository)


def get_tenant_module_service(
    tenant_module_repository=Depends(get_tenant_module_repository),
    tenant_repository: ITenantRepository = Depends(get_tenant_repository),
    module_repository: IModuleRepository = Depends(get_module_repository),
) -> TenantModuleService:
    return TenantModuleService(tenant_module_repository, tenant_repository, module_repository)


# ══════════════════════════════════════════════════════════════════
# AUTH SERVICE (depende de todos los anteriores)
# ══════════════════════════════════════════════════════════════════

def get_auth_service(
    token_service: ITokenService = Depends(get_token_service),
    oauth_service: IOAuthService = Depends(get_oauth_service),
    user_repository: IUserRepository = Depends(get_user_repository),
    tenant_repository: ITenantRepository = Depends(get_tenant_repository),
    tenant_module_service: TenantModuleService = Depends(get_tenant_module_service),
) -> IAuthService:
    """
    Servicio de autenticación con soporte multitenant.
    Incluye tenant_repository y tenant_module_service para enriquecer el JWT
    con la info del tenant y sus módulos activos.
    """
    return AuthService(
        token_service, oauth_service, user_repository,
        tenant_repository=tenant_repository,
        tenant_module_service=tenant_module_service,
    )


# ══════════════════════════════════════════════════════════════════
# SEGURIDAD (compatibilidad)
# ══════════════════════════════════════════════════════════════════

from app.core.security import (
    get_current_user,
    get_current_active_user,
    get_current_admin_user,
    get_current_manager_or_admin,
    get_current_superadmin_user,
)
