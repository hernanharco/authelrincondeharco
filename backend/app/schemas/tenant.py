"""
Schemas Pydantic para Tenant.
Separación: Response (lo que el API devuelve) / Create / Update (lo que recibe).
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# --- RESPUESTAS ---


class TenantResponse(BaseModel):
    id: str
    slug: str
    name: str
    is_active: bool
    website_url: Optional[str] = None
    admin_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TenantListResponse(BaseModel):
    tenants: list[TenantResponse]
    total: int


# --- ENTRADAS ---


class TenantCreate(BaseModel):
    slug: str = Field(
        ...,
        min_length=2,
        max_length=50,
        pattern=r"^[a-z0-9-]+$",
        description="Identificador corto (solo minúsculas, números, guiones)",
    )
    name: str = Field(..., min_length=1, max_length=255)
    is_active: bool = True
    website_url: Optional[str] = None
    admin_url: Optional[str] = None


class TenantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    website_url: Optional[str] = None
    admin_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
