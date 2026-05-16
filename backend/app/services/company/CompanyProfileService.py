"""
Servicio de Perfil de Empresa.
Responsabilidad única: lógica de negocio del perfil de empresa.

Reglas:
- 1 usuario = 1 perfil de empresa (creación única, actualización multiple)
- Solo el usuario propietario o un admin pueden ver/editar el perfil
- Los datos son maestros: otros proyectos los consumen vía API
"""

from typing import Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.interfaces.company.ICompanyProfileRepository import ICompanyProfileRepository
from app.schemas.company import CompanyProfileCreate, CompanyProfileUpdate


class CompanyProfileService:

    def __init__(self, db: Session, company_repository: ICompanyProfileRepository):
        self.db = db
        self.company_repository = company_repository

    async def get_profile(self, user_id: int, current_user: User) -> Dict[str, Any]:
        """Obtiene el perfil de empresa de un usuario."""
        self._validate_view_permission(user_id, current_user)
        profile = await self.company_repository.get_by_user_id(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil de empresa no encontrado",
            )
        return profile

    async def create_profile(
        self, user_id: int, profile_data: CompanyProfileCreate, current_user: User
    ) -> Dict[str, Any]:
        """Crea un perfil de empresa para un usuario."""
        self._validate_admin_permission(current_user, "crear perfiles de empresa")

        if await self.company_repository.exists(user_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El usuario ya tiene un perfil de empresa",
            )

        return await self.company_repository.create(
            user_id, profile_data.model_dump(exclude_unset=True)
        )

    async def update_profile(
        self, user_id: int, profile_data: CompanyProfileUpdate, current_user: User
    ) -> Dict[str, Any]:
        """Actualiza el perfil de empresa de un usuario."""
        self._validate_view_permission(user_id, current_user)

        profile = await self.company_repository.update(
            user_id, profile_data.model_dump(exclude_unset=True)
        )
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil de empresa no encontrado",
            )
        return profile

    async def delete_profile(self, user_id: int, current_user: User) -> None:
        """Elimina el perfil de empresa de un usuario."""
        self._validate_admin_permission(current_user, "eliminar perfiles de empresa")

        deleted = await self.company_repository.delete(user_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil de empresa no encontrado",
            )

    async def upsert_profile(
        self, user_id: int, profile_data: CompanyProfileUpdate, current_user: User
    ) -> Dict[str, Any]:
        """
        Crea o actualiza un perfil de empresa (idempotente).
        Útil para integraciones donde no se sabe si el perfil ya existe.
        """
        self._validate_view_permission(user_id, current_user)

        if await self.company_repository.exists(user_id):
            return await self.company_repository.update(
                user_id, profile_data.model_dump(exclude_unset=True)
            )

        create_data = CompanyProfileCreate(
            company_name=profile_data.company_name or "",
            **profile_data.model_dump(exclude_unset=True, exclude={"company_name"}),
        )
        return await self.company_repository.create(
            user_id, create_data.model_dump(exclude_unset=True)
        )

    # --- Validaciones de permisos ---

    def _validate_view_permission(self, target_user_id: int, current_user: User) -> None:
        """El usuario puede ver su propio perfil, o un admin puede ver cualquier perfil."""
        from app.domain.user_domain import UserDomain
        domain = UserDomain(current_user)
        if current_user.id != target_user_id and not domain.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver este perfil de empresa",
            )

    def _validate_admin_permission(self, current_user: User, action: str) -> None:
        """Solo admins pueden realizar esta acción."""
        from app.domain.user_domain import UserDomain
        domain = UserDomain(current_user)
        if not domain.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes permiso para {action}",
            )
