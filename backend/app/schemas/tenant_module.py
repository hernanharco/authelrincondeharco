"""
Schemas Pydantic para TenantModule.
"""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, ConfigDict


# --- RESPUESTAS ---


class TenantModuleResponse(BaseModel):
    tenant_id: str
    module_id: str
    is_active: bool
    settings: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TenantModuleWithDetails(BaseModel):
    """Respuesta enriquecida con info del tenant y módulo."""
    tenant_id: str
    tenant_slug: str
    tenant_name: str
    module_id: str
    module_name: str
    is_active: bool
    settings: Optional[dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


# --- ENTRADAS ---


class TenantModuleCreate(BaseModel):
    module_id: str = Field(..., min_length=2, max_length=50)
    is_active: bool = True
    settings: Optional[dict[str, Any]] = None


class TenantModuleUpdate(BaseModel):
    is_active: Optional[bool] = None
    settings: Optional[dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class TenantModulesBulkUpdate(BaseModel):
    """Para actualizar múltiples módulos de un tenant de una vez."""
    modules: list[TenantModuleCreate]
