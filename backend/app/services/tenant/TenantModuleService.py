"""
TenantModuleService — Lógica de negocio de asignación tenant↔module.
Responsabilidad única: gestionar feature flags por tenant.
"""
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status

from app.models.tenant_module import TenantModule
from app.interfaces.tenant.ITenantModuleRepository import ITenantModuleRepository
from app.interfaces.tenant.ITenantRepository import ITenantRepository
from app.interfaces.module.IModuleRepository import IModuleRepository


class TenantModuleService:
    def __init__(
        self,
        tenant_module_repository: ITenantModuleRepository,
        tenant_repository: ITenantRepository,
        module_repository: IModuleRepository,
    ):
        self.tenant_module_repository = tenant_module_repository
        self.tenant_repository = tenant_repository
        self.module_repository = module_repository

    async def get_by_tenant(self, tenant_id: str) -> List[TenantModule]:
        """Lista todos los módulos de un tenant (activos e inactivos)."""
        # Verificar que el tenant existe
        if not await self.tenant_repository.get_by_id(tenant_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant '{tenant_id}' no encontrado",
            )
        return await self.tenant_module_repository.get_by_tenant(tenant_id)

    async def get_active_modules(self, tenant_id: str) -> List[TenantModule]:
        """Lista solo los módulos activos de un tenant."""
        return await self.tenant_module_repository.get_active_modules_for_tenant(tenant_id)

    async def assign_module(
        self,
        tenant_id: str,
        module_id: str,
        is_active: bool = True,
        settings: Optional[Dict[str, Any]] = None,
    ) -> TenantModule:
        """Asigna un módulo a un tenant (o crea la asignación)."""
        # Verificar que el tenant existe
        if not await self.tenant_repository.get_by_id(tenant_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant '{tenant_id}' no encontrado",
            )
        # Verificar que el módulo existe
        if not await self.module_repository.get_by_id(module_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Módulo '{module_id}' no encontrado",
            )
        # Verificar si ya existe la asignación
        existing = await self.tenant_module_repository.get_by_tenant_and_module(
            tenant_id, module_id
        )
        if existing:
            # Actualizar la existente
            updated = await self.tenant_module_repository.update(
                tenant_id, module_id, {"is_active": is_active, "settings": settings}
            )
            return updated
        # Crear nueva
        return await self.tenant_module_repository.create(
            {"tenant_id": tenant_id, "module_id": module_id, "is_active": is_active, "settings": settings}
        )

    async def update_settings(
        self,
        tenant_id: str,
        module_id: str,
        is_active: Optional[bool] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> TenantModule:
        """Actualiza la configuración de un módulo para un tenant."""
        existing = await self.tenant_module_repository.get_by_tenant_and_module(
            tenant_id, module_id
        )
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asignación tenant='{tenant_id}' module='{module_id}' no encontrada",
            )
        update_data: Dict[str, Any] = {}
        if is_active is not None:
            update_data["is_active"] = is_active
        if settings is not None:
            update_data["settings"] = settings
        updated = await self.tenant_module_repository.update(tenant_id, module_id, update_data)
        return updated

    async def remove_module(self, tenant_id: str, module_id: str) -> TenantModule:
        """Remueve un módulo de un tenant."""
        removed = await self.tenant_module_repository.delete(tenant_id, module_id)
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asignación tenant='{tenant_id}' module='{module_id}' no encontrada",
            )
        return removed

    async def get_modules_dict_for_jwt(self, tenant_id: str) -> Dict[str, Any]:
        """
        Construye el dict de modules para incluir en el JWT.
        Resultado: { "radar": { "enabled": true }, "inventory": { "enabled": true, "providers": ["vinted"] } }
        """
        assignments = await self.tenant_module_repository.get_active_modules_for_tenant(tenant_id)
        modules_dict = {}
        for assignment in assignments:
            module_data: Dict[str, Any] = {"enabled": assignment.is_active}
            if assignment.settings:
                module_data.update(assignment.settings)
            modules_dict[assignment.module_id] = module_data
        return modules_dict
