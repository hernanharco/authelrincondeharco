"""
Servicio de Autenticación - Principio de Responsabilidad Única
"""

from typing import Optional, Tuple
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import verify_password
from app.interfaces.auth.IAuthService import IAuthService
from app.interfaces.auth.ITokenService import ITokenService
from app.interfaces.auth.IOAuthService import IOAuthService
from app.interfaces.user.IUserRepository import IUserRepository
from app.types.enums import UserRole, UserStatus


class AuthService(IAuthService):
    """
    Implementación concreta del servicio de autenticación.
    Orquesta los diferentes servicios para autenticación completa.
    """

    def __init__(
        self,
        db: Session,
        token_service: ITokenService,
        oauth_service: IOAuthService,
        user_repository: IUserRepository,
    ):
        self.db = db
        self.token_service = token_service
        self.oauth_service = oauth_service
        self.user_repository = user_repository

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Autentica un usuario con credenciales tradicionales.
        """
        # Buscar usuario por username o email
        user = await self.user_repository.get_by_username(username)
        if not user:
            user = await self.user_repository.get_by_email(username)

        if not user:
            return None

        # Verificar contraseña
        if not verify_password(password, user.password_hash):
            return None

        # Verificar estado de la cuenta
        if not user.is_active or user.is_locked:
            return None

        return user

    async def authenticate_with_google(
        self, token: str, origin: str
    ) -> Tuple[User, str, int]:
        """
        Autentica un usuario con Google OAuth.
        """
        try:
            # 1. Validar token con Google
            user_info = await self.oauth_service.verify_token(token)
            email = user_info.get("email")

            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se pudo obtener el email del usuario",
                )

            # 2. Buscar o crear usuario en BD
            user = await self.user_repository.get_by_email(email)

            if not user:
                # Generar username único desde el email
                base_username = email.split("@")[0]
                username = base_username
                suffix = 1
                while await self.user_repository.exists_by_username(username):
                    username = f"{base_username}{suffix}"
                    suffix += 1

                user = await self.user_repository.create({
                    "email": email,
                    "username": username,
                    "full_name": user_info.get("name", ""),
                    "password_hash": "",          # Sin contraseña para usuarios OAuth
                    "role": UserRole.USER,
                    "status": UserStatus.ACTIVE,
                    "is_active": True,
                    "origin": "google",
                })

            # 3. Verificar estado de la cuenta
            if not user.is_active or user.is_locked:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cuenta desactivada o bloqueada.",
                )

            # 4. Generar JWT interno
            internal_token, expires_in = await self.create_access_token(user)

            return user, internal_token, expires_in

        except HTTPException:
            raise
        except Exception as e:
            import traceback
            traceback.print_exc()  # ← añade esta línea
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error en autenticación: {str(e)}",
            )

    async def create_access_token(self, user: User) -> Tuple[str, int]:
        """
        Crea un token de acceso JWT.
        """
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "type": "access",
        }

        token, expires_at = await self.token_service.create_access_token(token_data)
        expires_in = int((expires_at - datetime.utcnow()).total_seconds())

        return token, expires_in

    async def revoke_token(self, token: str) -> bool:
        """
        Revoca un token de acceso.
        """
        return await self.token_service.revoke_token(token)
