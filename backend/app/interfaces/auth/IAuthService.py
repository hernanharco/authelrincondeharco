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
    async def authenticate_user(
        self, username: str, password: str, raise_on_pending: bool = False
    ) -> Optional[User]:
        """
        Autentica un usuario con credenciales tradicionales.

        Args:
            username: Nombre de usuario o email
            password: Contraseña en texto plano
            raise_on_pending: Cuando True y la contraseña es correcta pero la
                cuenta está inactiva, lanza 403 PENDING_APPROVAL en vez de
                devolver None (lo usa el endpoint de login para que el estado
                de aprobación manual no se confunda con credenciales malas).
                Con False se mantiene el comportamiento histórico: None.

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
