"""
Interface de Repositorio de Perfiles de Empresa.
Define el contrato para operaciones de base de datos de CompanyProfile.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.models.company_profile import CompanyProfile


class ICompanyProfileRepository(ABC):

    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> Optional[CompanyProfile]:
        """Obtiene el perfil de empresa de un usuario."""
        pass

    @abstractmethod
    async def create(
        self, user_id: int, data: Dict[str, Any]
    ) -> CompanyProfile:
        """Crea un perfil de empresa para un usuario."""
        pass

    @abstractmethod
    async def update(
        self, user_id: int, data: Dict[str, Any]
    ) -> Optional[CompanyProfile]:
        """Actualiza el perfil de empresa de un usuario. Devuelve None si no existe."""
        pass

    @abstractmethod
    async def delete(self, user_id: int) -> bool:
        """Elimina el perfil de empresa de un usuario."""
        pass

    @abstractmethod
    async def exists(self, user_id: int) -> bool:
        """Verifica si un usuario ya tiene perfil de empresa."""
        pass
