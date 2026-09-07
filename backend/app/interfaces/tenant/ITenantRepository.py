"""
Interface de Repositorio de Tenants - Principio de Segregación de Interfaces
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from app.models.tenant import Tenant


class ITenantRepository(ABC):
    """
    Interface para repositorio de tenants.
    Define el contrato para operaciones de base de datos de tenants.
    """

    @abstractmethod
    async def get_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """Obtiene un tenant por ID (UUID)."""
        pass

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Optional[Tenant]:
        """Obtiene un tenant por slug."""
        pass

    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> List[Tenant]:
        """Lista tenants con paginación."""
        pass

    @abstractmethod
    async def exists_by_slug(self, slug: str) -> bool:
        """Verifica si existe un tenant por slug."""
        pass

    @abstractmethod
    async def create(self, tenant_data: dict) -> Tenant:
        """Crea un nuevo tenant."""
        pass

    @abstractmethod
    async def update(self, tenant_id: str, data: dict) -> Optional[Tenant]:
        """Actualiza un tenant existente."""
        pass

    @abstractmethod
    async def delete(self, tenant_id: str) -> Optional[Tenant]:
        """Elimina un tenant."""
        pass

    @abstractmethod
    async def count(self) -> int:
        """Cuenta el total de tenants."""
        pass
