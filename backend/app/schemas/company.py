"""
Schemas de Perfil de Empresa.
Definen la interfaz pública del CompanyProfile para la API.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class CompanyProfileResponse(BaseModel):
    """Respuesta pública del perfil de empresa."""

    id: int
    user_id: int
    company_name: str
    cif: Optional[str] = None
    address: Optional[str] = None
    iban: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    contact_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CompanyProfileCreate(BaseModel):
    """Schema para creación de perfil de empresa."""

    company_name: str = Field(..., min_length=1, max_length=255)
    cif: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    iban: Optional[str] = Field(None, max_length=34)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    contact_name: Optional[str] = Field(None, max_length=255)


class CompanyProfileUpdate(BaseModel):
    """Schema para actualización de perfil de empresa.
    Todos los campos son opcionales — solo se envían los que cambian.
    """

    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    cif: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    iban: Optional[str] = Field(None, max_length=34)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    contact_name: Optional[str] = Field(None, max_length=255)

