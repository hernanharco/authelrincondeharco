"""
Interface de Repositorio de Modules - Principio de Segregación de Interfaces
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from app.models.module import Module


class IModuleRepository(ABC):
    """
    Interface para repositorio de modules.
    Define el contrato para operaciones de base de datos de modules.
    """

    @abstractmethod
    async def get_by_id(self, module_id: str) -> Optional[Module]:
        """Obtiene un module por ID."""
        pass

    @abstractmethod
    async def get_all(
        self, skip: int = 0, limit: int = 100, active_only: bool = False
    ) -> List[Module]:
        """Lista modules con paginación."""
        pass

    @abstractmethod
    async def exists_by_id(self, module_id: str) -> bool:
        """Verifica si existe un module por ID."""
        pass

    @abstractmethod
    async def create(self, module_data: dict) -> Module:
        """Crea un nuevo module."""
        pass

    @abstractmethod
    async def update(self, module_id: str, data: dict) -> Optional[Module]:
        """Actualiza un module existente."""
        pass

    @abstractmethod
    async def delete(self, module_id: str) -> Optional[Module]:
        """Elimina un module."""
        pass

    @abstractmethod
    async def count(self) -> int:
        """Cuenta el total de modules."""
        pass
