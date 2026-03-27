"""
Interface de Servicio de Autenticación - Principio de Segregación de Interfaces
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
from app.models.user import User


class IAuthService(ABC):
    """
    Interface para servicios de autenticación.
    Define el contrato que deben cumplir todas las implementaciones de autenticación.
    """

    @abstractmethod
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Autentica un usuario con credenciales tradicionales.

        Args:
            username: Nombre de usuario o email
            password: Contraseña en texto plano

        Returns:
            Usuario autenticado o None si falla
        """
        pass

    @abstractmethod
    async def authenticate_with_google(
        self, token: str, origin: str
    ) -> Tuple[User, str, int]:
        """
        Autentica un usuario con Google OAuth.

        Args:
            token: Token de Google
            origin: Origen de la autenticación

        Returns:
            Tupla con (usuario, token_jwt, expires_in)

        Raises:
            HTTPException: Si la autenticación falla
        """
        pass

    @abstractmethod
    async def create_access_token(self, user: User) -> Tuple[str, int]:
        """
        Crea un token de acceso JWT.

        Args:
            user: Usuario autenticado

        Returns:
            Tupla con (token, expires_in)
        """
        pass

    @abstractmethod
    async def revoke_token(self, token: str) -> bool:
        """
        Revoca un token de acceso.

        Args:
            token: Token a revocar

        Returns:
            True si se revocó correctamente
        """
        pass
