"""
Modelos de datos — registrados aquí para que Base.metadata los conozca.
Importar este módulo en main.py antes de create_all() asegura que
todas las tablas se creen correctamente.
"""
from app.models.user import User
from app.models.company_profile import CompanyProfile
from app.models.tenant import Tenant
from app.models.module import Module
from app.models.tenant_module import TenantModule

__all__ = ["User", "CompanyProfile", "Tenant", "Module", "TenantModule"]
