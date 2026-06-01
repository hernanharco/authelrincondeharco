"""
Modelos de datos — registrados aquí para que Base.metadata los conozca.
Importar este módulo en main.py antes de create_all() asegura que
todas las tablas se creen correctamente.
"""
from app.models.user import User
from app.models.company_profile import CompanyProfile

__all__ = ["User", "CompanyProfile"]
