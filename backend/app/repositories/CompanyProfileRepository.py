"""
Repositorio de Perfiles de Empresa.
Implementa ICompanyProfileRepository.
Responsabilidad única: acceso a datos de CompanyProfile.
Usa SQLAlchemy 2.0 style async.
"""
from typing import Dict, Any, Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.company_profile import CompanyProfile
from app.models.user import User
from app.interfaces.company.ICompanyProfileRepository import ICompanyProfileRepository


class CompanyProfileRepository(ICompanyProfileRepository):

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: int) -> Optional[CompanyProfile]:
        result = await self.db.execute(
            select(CompanyProfile).where(CompanyProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: int, data: Dict[str, Any]) -> CompanyProfile:
        profile = CompanyProfile(user_id=user_id, **data)
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def update(
        self, user_id: int, data: Dict[str, Any]
    ) -> Optional[CompanyProfile]:
        profile = await self.get_by_user_id(user_id)
        if not profile:
            return None
        for key, value in data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def delete(self, user_id: int) -> bool:
        profile = await self.get_by_user_id(user_id)
        if not profile:
            return False
        await self.db.delete(profile)
        await self.db.commit()
        return True

    async def get_all(self) -> List[Dict[str, Any]]:
        result = await self.db.execute(
            select(CompanyProfile, User)
            .join(User, CompanyProfile.user_id == User.id)
        )
        rows = result.all()
        return [
            {
                "id": profile.id,
                "user_id": profile.user_id,
                "company_name": profile.company_name,
                "cif": profile.cif,
                "address": profile.address,
                "iban": profile.iban,
                "phone": profile.phone,
                "contact_name": profile.contact_name,
                "created_at": profile.created_at,
                "updated_at": profile.updated_at,
                "user_full_name": user.full_name,
                "user_email": user.email,
                "user_username": user.username,
            }
            for profile, user in rows
        ]

    async def exists(self, user_id: int) -> bool:
        result = await self.db.execute(
            select(CompanyProfile.id)
            .where(CompanyProfile.user_id == user_id)
            .limit(1)
        )
        return result.first() is not None
