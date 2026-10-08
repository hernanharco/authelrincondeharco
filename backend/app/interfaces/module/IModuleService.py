"""
Interface de Servicio de Modules - Principio de Segregación de Interfaces
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from app.models.module import Module


class IModuleService(ABC):
    """
    Interface para servicio de modules.
    Define el contrato para la lógica de negocio.
    """

    @abstractmethod
    async def get_by_id(self, module_id: str) -> Optional[Module]:
        pass

    @abstractmethod
    async def get_all(
        self, skip: int = 0, limit: int = 100, active_only: bool = False
    ) -> List[Module]:
        pass

    @abstractmethod
    async def create(
        self, module_id: str, name: str, description: str = None, is_active: bool = True
    ) -> Module:
        pass

    @abstractmethod
    async def update(
        self,
        module_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[Module]:
        pass

    @abstractmethod
    async def delete(self, module_id: str) -> Optional[Module]:
        pass
