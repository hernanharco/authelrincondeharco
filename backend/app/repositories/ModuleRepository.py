"""
ModuleRepository — Acceso a datos de modules.
Implementa IModuleRepository.
Usa SQLAlchemy 2.0 style async.
"""
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.module import Module
from app.interfaces.module.IModuleRepository import IModuleRepository


class ModuleRepository(IModuleRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, module_id: str) -> Optional[Module]:
        result = await self.db.execute(select(Module).where(Module.id == module_id))
        return result.scalar_one_or_none()

    async def get_all(
        self, skip: int = 0, limit: int = 100, active_only: bool = False
    ) -> List[Module]:
        stmt = select(Module)
        if active_only:
            stmt = stmt.where(Module.is_active == True)
        stmt = stmt.order_by(Module.id).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def exists_by_id(self, module_id: str) -> bool:
        result = await self.db.execute(
            select(Module.id).where(Module.id == module_id).limit(1)
        )
        return result.first() is not None

    async def create(self, module_data: dict) -> Module:
        module = Module(**module_data)
        self.db.add(module)
        await self.db.commit()
        await self.db.refresh(module)
        return module

    async def update(self, module_id: str, data: dict) -> Optional[Module]:
        module = await self.get_by_id(module_id)
        if not module:
            return None
        for key, value in data.items():
            if hasattr(module, key) and value is not None:
                setattr(module, key, value)
        await self.db.commit()
        await self.db.refresh(module)
        return module

    async def delete(self, module_id: str) -> Optional[Module]:
        module = await self.get_by_id(module_id)
        if not module:
            return None
        await self.db.delete(module)
        await self.db.commit()
        return module

    async def count(self) -> int:
        result = await self.db.execute(select(func.count(Module.id)))
        return result.scalar() or 0
