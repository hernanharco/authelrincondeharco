"""
Interface de OAuth - Principio de Segregación de Interfaces
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.models.user import User


class IOAuthService(ABC):
    """
    Interface para servicios de OAuth.
    Maneja solo la integración con proveedores OAuth externos.
    """

    @abstractmethod
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verifica un token OAuth con el proveedor externo.

        Args:
            token: Token OAuth a verificar

        Returns:
            Información del usuario desde el proveedor

        Raises:
            HTTPException: Si el token es inválido
        """
        pass

    @abstractmethod
    async def get_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información del usuario desde el proveedor OAuth.

        Args:
            token: Token OAuth válido

        Returns:
            Información del usuario o None si no se puede obtener
        """
        pass

    @abstractmethod
    async def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Intercambia un authorization code por tokens y devuelve info del usuario.
        Authorization Code Flow (server-side).

        Args:
            code: Authorization code de Google
            redirect_uri: URI de redirección registrada

        Returns:
            Información del usuario (email, name, etc.)

        Raises:
            HTTPException: Si el intercambio falla
        """
        pass

    @abstractmethod
    async def create_user_from_oauth(self, user_info: Dict[str, Any]) -> Optional[User]:
        """
        Crea o actualiza un usuario a partir de información OAuth.

        Args:
            user_info: Información del usuario desde OAuth

        Returns:
            Usuario creado/actualizado o None si falla
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Obtiene el nombre del proveedor OAuth.

        Returns:
            Nombre del proveedor (ej: 'google', 'github', etc.)
        """
        pass
