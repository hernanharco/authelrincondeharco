"""
Endpoints de Perfil de Empresa.
CRUD de CompanyProfile — datos maestros que consumen otros proyectos.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.user import User
from app.schemas.company import (
    CompanyProfileResponse,
    CompanyProfileCreate,
    CompanyProfileUpdate,
)
from app.services.company.CompanyProfileService import CompanyProfileService
from app.api.v1.dependencies import get_company_profile_service
from app.core.security import get_current_active_user, get_current_admin_user

router = APIRouter()


# ── Endpoint público (sin autenticación) para landing pages ──

class CompanyProfilePublic(BaseModel):
    """Versión pública del perfil de empresa — solo datos para mostrar en landing page."""
    company_name: str
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    contact_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


@router.get(
    "/{user_id}/public",
    response_model=CompanyProfilePublic,
    include_in_schema=True,
)
async def get_public_company_profile(
    user_id: int,
    company_service: CompanyProfileService = Depends(get_company_profile_service),
):
    """
    Endpoint PÚBLICO — no requiere autenticación.
    Devuelve datos básicos de la empresa para mostrar en landing pages.
    No expone datos sensibles (iban, cif, etc.).
    """
    return await company_service.get_public_profile(user_id)


@router.get("/me", response_model=CompanyProfileResponse)
async def get_my_company_profile(
    company_service: CompanyProfileService = Depends(get_company_profile_service),
    current_user: User = Depends(get_current_active_user),
):
    """Obtiene el perfil de empresa del usuario autenticado."""
    return await company_service.get_profile(current_user.id, current_user)


@router.get("/", response_model=List[Dict[str, Any]])
async def list_company_profiles(
    company_service: CompanyProfileService = Depends(get_company_profile_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Lista todos los perfiles de empresa. Solo admin."""
    return await company_service.get_all_profiles(current_user)


@router.get("/{user_id}", response_model=CompanyProfileResponse)
async def get_company_profile(
    user_id: int,
    company_service: CompanyProfileService = Depends(get_company_profile_service),
    current_user: User = Depends(get_current_active_user),
):
    """Obtiene el perfil de empresa de un usuario."""
    return await company_service.get_profile(user_id, current_user)


@router.post(
    "/{user_id}",
    response_model=CompanyProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_company_profile(
    user_id: int,
    profile_data: CompanyProfileCreate,
    company_service: CompanyProfileService = Depends(get_company_profile_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Crea un perfil de empresa para un usuario. Solo admin."""
    return await company_service.create_profile(user_id, profile_data, current_user)


@router.put("/me", response_model=CompanyProfileResponse)
async def update_my_company_profile(
    profile_data: CompanyProfileUpdate,
    company_service: CompanyProfileService = Depends(get_company_profile_service),
    current_user: User = Depends(get_current_active_user),
):
    """Crea o actualiza el perfil de empresa del usuario autenticado (idempotente)."""
    return await company_service.upsert_profile(
        current_user.id, profile_data, current_user
    )


@router.put("/{user_id}", response_model=CompanyProfileResponse)
async def update_company_profile(
    user_id: int,
    profile_data: CompanyProfileUpdate,
    company_service: CompanyProfileService = Depends(get_company_profile_service),
    current_user: User = Depends(get_current_active_user),
):
    """Actualiza el perfil de empresa de un usuario específico."""
    return await company_service.update_profile(user_id, profile_data, current_user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company_profile(
    user_id: int,
    company_service: CompanyProfileService = Depends(get_company_profile_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Elimina el perfil de empresa de un usuario. Solo admin."""
    await company_service.delete_profile(user_id, current_user)


@router.put(
    "/{user_id}/upsert",
    response_model=CompanyProfileResponse,
)
async def upsert_company_profile(
    user_id: int,
    profile_data: CompanyProfileUpdate,
    company_service: CompanyProfileService = Depends(get_company_profile_service),
    current_user: User = Depends(get_current_active_user),
):
    """Crea o actualiza un perfil de empresa (idempotente)."""
    return await company_service.upsert_profile(user_id, profile_data, current_user)
