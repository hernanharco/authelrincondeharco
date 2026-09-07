"""
Interface de Servicio de Tenants - Principio de Segregación de Interfaces
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from app.models.tenant import Tenant


class ITenantService(ABC):
    """
    Interface para servicio de tenants.
    Define el contrato para la lógica de negocio.
    """

    @abstractmethod
    async def get_by_id(self, tenant_id: str) -> Optional[Tenant]:
        pass

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Optional[Tenant]:
        pass

    @abstractmethod
    async def get_all(
        self, skip: int = 0, limit: int = 100, active_only: bool = False
    ) -> List[Tenant]:
        pass

    @abstractmethod
    async def create(self, slug: str, name: str, is_active: bool = True) -> Tenant:
        pass

    @abstractmethod
    async def update(
        self, tenant_id: str, name: Optional[str] = None, is_active: Optional[bool] = None
    ) -> Optional[Tenant]:
        pass

    @abstractmethod
    async def delete(self, tenant_id: str) -> Optional[Tenant]:
        pass
