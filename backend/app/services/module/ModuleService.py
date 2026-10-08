"""
ModuleService — Lógica de negocio de modules.
Responsabilidad única: orquestar operaciones sobre modules.
"""
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.module import Module
from app.interfaces.module.IModuleRepository import IModuleRepository
from app.interfaces.module.IModuleService import IModuleService


class ModuleService(IModuleService):
    def __init__(self, module_repository: IModuleRepository):
        self.module_repository = module_repository

    async def get_by_id(self, module_id: str) -> Optional[Module]:
        module = await self.module_repository.get_by_id(module_id)
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Módulo con id '{module_id}' no encontrado",
            )
        return module

    async def get_all(
        self, skip: int = 0, limit: int = 100, active_only: bool = False
    ) -> List[Module]:
        return await self.module_repository.get_all(skip, limit, active_only)

    async def create(
        self, module_id: str, name: str, description: str = None, is_active: bool = True
    ) -> Module:
        if await self.module_repository.exists_by_id(module_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un módulo con id '{module_id}'",
            )
        return await self.module_repository.create(
            {"id": module_id, "name": name, "description": description, "is_active": is_active}
        )

    async def update(
        self,
        module_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[Module]:
        await self.get_by_id(module_id)
        return await self.module_repository.update(
            module_id, {"name": name, "description": description, "is_active": is_active}
        )

    async def delete(self, module_id: str) -> Optional[Module]:
        await self.get_by_id(module_id)
        return await self.module_repository.delete(module_id)
