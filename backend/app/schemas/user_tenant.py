"""
Schemas Pydantic para UserTenant.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserTenantResponse(BaseModel):
    id: str
    user_id: str
    tenant_id: str
    tenant_slug: str = ""
    tenant_name: str = ""
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserTenantCreate(BaseModel):
    user_id: str
    tenant_id: str
    role: str = "USER"


class SelectTenantRequest(BaseModel):
    tenant_id: str
