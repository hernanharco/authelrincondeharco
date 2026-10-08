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


class TenantUsageResponse(BaseModel):
    """Ranking de uso por tenant (GET /tenants/usage).

    Conteos derivados de la membresía user_tenants + users;
    `ultimo_acceso` es nullable (tenant sin miembros con logins).
    """

    slug: str
    name: str
    personas: int
    admins: int
    activas_30d: int
    activos: int
    ultimo_acceso: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TenantMemberResponse(BaseModel):
    """Miembro de un tenant con su rol de MEMBRESÍA (GET /tenants/{id}/users).

    `role_tenant` es el rol en user_tenants, NO el rol global users.role.
    """

    id: int
    username: str
    email: str
    role_tenant: str
    status: str
    login_count: int
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


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
