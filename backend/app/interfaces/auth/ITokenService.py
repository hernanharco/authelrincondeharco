"""
Interface de Servicio de Tokens - Principio de Segregación de Interfaces
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple
from datetime import datetime


class ITokenService(ABC):
    """
    Interface para servicios de gestión de tokens JWT.
    Maneja solo la creación, validación y revocación de tokens.
    """

    @abstractmethod
    async def create_access_token(
        self, data: Dict[str, Any], expires_delta: Optional[int] = None
    ) -> Tuple[str, datetime]:
        """
        Crea un token de acceso JWT.

        Args:
            data: Datos a incluir en el token
            expires_delta: Tiempo de expiración en segundos

        Returns:
            Tupla con (token, expires_at)
        """
        pass

    @abstractmethod
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verifica y decodifica un token JWT.

        Args:
            token: Token JWT a verificar

        Returns:
            Payload del token o None si es inválido
        """
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> Optional[Tuple[str, datetime]]:
        """
        Refresca un token de acceso usando un refresh token.

        Args:
            refresh_token: Token de refresco

        Returns:
            Nuevo access token y fecha de expiración o None si falla
        """
        pass

    @abstractmethod
    async def revoke_token(self, token: str) -> bool:
        """
        Revoca un token (añade a blacklist).

        Args:
            token: Token a revocar

        Returns:
            True si se revocó correctamente
        """
        pass

    @abstractmethod
    async def is_token_revoked(self, token: str) -> bool:
        """
        Verifica si un token está revocado.

        Args:
            token: Token a verificar

        Returns:
            True si el token está revocado
        """
        pass
