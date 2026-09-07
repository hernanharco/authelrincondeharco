"""
Interface de Repositorio de TenantModules - Principio de Segregación de Interfaces
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from app.models.tenant_module import TenantModule


class ITenantModuleRepository(ABC):
    """
    Interface para repositorio de tenant_modules.
    """

    @abstractmethod
    async def get_by_tenant_and_module(
        self, tenant_id: str, module_id: str
    ) -> Optional[TenantModule]:
        """Obtiene la asignación de un módulo a un tenant."""
        pass

    @abstractmethod
    async def get_by_tenant(self, tenant_id: str) -> List[TenantModule]:
        """Obtiene todos los módulos asignados a un tenant."""
        pass

    @abstractmethod
    async def get_by_module(self, module_id: str) -> List[TenantModule]:
        """Obtiene todos los tenants que tienen un módulo."""
        pass

    @abstractmethod
    async def get_active_modules_for_tenant(self, tenant_id: str) -> List[TenantModule]:
        """Obtiene solo los módulos activos de un tenant."""
        pass

    @abstractmethod
    async def create(self, data: dict) -> TenantModule:
        """Asigna un módulo a un tenant."""
        pass

    @abstractmethod
    async def update(
        self, tenant_id: str, module_id: str, data: dict
    ) -> Optional[TenantModule]:
        """Actualiza la configuración de un módulo para un tenant."""
        pass

    @abstractmethod
    async def delete(self, tenant_id: str, module_id: str) -> Optional[TenantModule]:
        """Remueve un módulo de un tenant."""
        pass

    @abstractmethod
    async def exists(self, tenant_id: str, module_id: str) -> bool:
        """Verifica si un tenant tiene un módulo asignado."""
        pass
