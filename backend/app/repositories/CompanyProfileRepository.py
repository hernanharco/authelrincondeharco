"""
Repositorio de Perfiles de Empresa.
Implementa ICompanyProfileRepository.
Responsabilidad única: acceso a datos de CompanyProfile.
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.company_profile import CompanyProfile
from app.interfaces.company.ICompanyProfileRepository import ICompanyProfileRepository


class CompanyProfileRepository(ICompanyProfileRepository):

    def __init__(self, db: Session):
        self.db = db

    async def get_by_user_id(self, user_id: int) -> Optional[CompanyProfile]:
        return (
            self.db.query(CompanyProfile)
            .filter(CompanyProfile.user_id == user_id)
            .first()
        )

    async def create(self, user_id: int, data: Dict[str, Any]) -> CompanyProfile:
        profile = CompanyProfile(user_id=user_id, **data)
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
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
        self.db.commit()
        self.db.refresh(profile)
        return profile

    async def delete(self, user_id: int) -> bool:
        profile = await self.get_by_user_id(user_id)
        if not profile:
            return False
        self.db.delete(profile)
        self.db.commit()
        return True

    async def exists(self, user_id: int) -> bool:
        return (
            self.db.query(CompanyProfile.id)
            .filter(CompanyProfile.user_id == user_id)
            .first()
            is not None
        )
