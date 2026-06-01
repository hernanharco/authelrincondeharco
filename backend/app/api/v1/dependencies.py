"""
Dependencias de Inyección - Principio de Inversión de Dependencias
"""
from functools import lru_cache
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.db.session import get_db
from app.services.auth.TokenService import TokenService
from app.services.auth.GoogleOAuthService import GoogleOAuthService
from app.services.auth.AuthService import AuthService
from app.services.user.UserService import UserService
from app.repositories.UserRepository import UserRepository
from app.interfaces.auth.ITokenService import ITokenService
from app.interfaces.auth.IOAuthService import IOAuthService
from app.interfaces.auth.IAuthService import IAuthService
from app.interfaces.user.IUserService import IUserService
from app.interfaces.user.IUserRepository import IUserRepository
from app.interfaces.company.ICompanyProfileRepository import ICompanyProfileRepository
from app.repositories.CompanyProfileRepository import CompanyProfileRepository
from app.services.company.CompanyProfileService import CompanyProfileService

# Servicios Singleton (cacheados para rendimiento)
@lru_cache()
def get_token_service() -> ITokenService:
    """
    Obtiene el servicio de tokens (singleton).
    """
    return TokenService()


@lru_cache()
def get_oauth_service() -> IOAuthService:
    """
    Obtiene el servicio de OAuth (singleton).
    """
    return GoogleOAuthService()


def get_user_repository(db: AsyncSession = Depends(get_db)) -> IUserRepository:
    """
    Obtiene el repositorio de usuarios.
    """
    return UserRepository(db)


def get_auth_service(
    token_service: ITokenService = Depends(get_token_service),
    oauth_service: IOAuthService = Depends(get_oauth_service),
    user_repository: IUserRepository = Depends(get_user_repository)
) -> IAuthService:
    """
    Obtiene el servicio de autenticación con todas sus dependencias.
    NOTA: No recibe `db` porque AuthService delega toda la
    persistencia en user_repository (Principio de Inversión de Dependencias).
    """
    return AuthService(token_service, oauth_service, user_repository)


def get_user_service(
    db: AsyncSession = Depends(get_db),
    user_repository: IUserRepository = Depends(get_user_repository)
) -> IUserService:
    """
    Obtiene el servicio de usuarios con sus dependencias.
    """
    return UserService(db, user_repository)


def get_company_profile_repository(
    db: AsyncSession = Depends(get_db),
) -> ICompanyProfileRepository:
    """Obtiene el repositorio de perfiles de empresa."""
    return CompanyProfileRepository(db)


def get_company_profile_service(
    company_repository: ICompanyProfileRepository = Depends(get_company_profile_repository),
) -> CompanyProfileService:
    """Obtiene el servicio de perfiles de empresa."""
    return CompanyProfileService(company_repository)


# Dependencias de seguridad existentes (mantenidas para compatibilidad)
from app.core.security import (
    get_current_user,
    get_current_active_user,
    get_current_admin_user,
    get_current_manager_or_admin,
    get_current_superadmin_user
)
