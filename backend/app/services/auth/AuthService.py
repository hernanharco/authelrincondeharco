"""
backend/app/services/auth/AuthService.py
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
        user = await self.user_repository.get_by_username(username)
        if not user:
            user = await self.user_repository.get_by_email(username)

        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        if not user.is_active or user.is_locked:
            return None

        return user

    async def authenticate_with_google(
        self, token: str, origin: str
    ) -> Tuple[User, str, int]:
        try:
            user_info = await self.oauth_service.verify_token(token)
            email = user_info.get("email")

            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se pudo obtener el email del usuario",
                )

            user = await self.user_repository.get_by_email(email)

            if not user:
                base_username = email.split("@")[0]
                username = base_username
                suffix = 1
                while await self.user_repository.exists_by_username(username):
                    username = f"{base_username}{suffix}"
                    suffix += 1

                user = await self.user_repository.create(
                    {
                        "email": email,
                        "username": username,
                        "full_name": user_info.get("name", ""),
                        "password_hash": "",
                        "role": UserRole.NONE,       # 👈 cambiado
                        "status": UserStatus.PENDING, # 👈 cambiado
                        "is_active": False,           # 👈 cambiado
                        "origin": "google",
                    }
                )
                # Nuevo usuario pendiente — no generar token todavía
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="PENDING_APPROVAL",
                )

            # Usuario existente — verificar estado
            if user.status == UserStatus.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="PENDING_APPROVAL",
                )

            if not user.is_active or user.is_locked:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cuenta desactivada o bloqueada.",
                )

            internal_token, expires_in = await self.create_access_token(user)
            return user, internal_token, expires_in

        except HTTPException:
            raise
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error en autenticación: {str(e)}",
            )

    async def create_access_token(self, user: User) -> Tuple[str, int]:
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
        return await self.token_service.revoke_token(token)

    def process_google_login(
        self, code: str, redirect_uri: str
    ) -> Tuple[User, str, int]:
        from datetime import datetime, timedelta, timezone
        from jose import jwt
        from app.core.config import settings
        import requests as http_requests

        try:
            token_url = "https://oauth2.googleapis.com/token"
            data = {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            }

            response = http_requests.post(token_url, data=data)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error al intercambiar código con Google: {response.text}",
                )

            token_data = response.json()
            access_token = token_data.get("access_token")

            if not access_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No se recibió access_token. Respuesta: {token_data}",
                )

            userinfo_response = http_requests.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if userinfo_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Error al obtener información del usuario de Google",
                )

            userinfo = userinfo_response.json()
            email = userinfo.get("email")
            name = userinfo.get("name", "")

            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se pudo obtener email de Google",
                )

            user = self.db.query(User).filter(User.email == email).first()

            if not user:
                base_username = email.split("@")[0]
                username = base_username
                counter = 1
                while self.db.query(User).filter(User.username == username).first():
                    username = f"{base_username}{counter}"
                    counter += 1

                user = User(
                    username=username,
                    email=email,
                    full_name=name,
                    password_hash="",
                    role=UserRole.NONE,        # 👈 cambiado
                    status=UserStatus.PENDING,  # 👈 cambiado
                    is_active=False,            # 👈 cambiado
                    is_locked=False,
                )
                self.db.add(user)
                self.db.commit()
                self.db.refresh(user)

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="PENDING_APPROVAL",
                )

            # Usuario existente
            if user.status == UserStatus.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="PENDING_APPROVAL",
                )

            if user.is_locked:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cuenta bloqueada. Contacte con el administrador.",
                )

            user.last_login = datetime.now(timezone.utc)
            self.db.commit()

            expires_in = settings.access_token_expire_minutes * 60
            expire = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

            payload = {
                "sub": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role.value if hasattr(user.role, "value") else user.role,
                "exp": expire,
            }

            token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.algorithm)
            return user, token, expires_in

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error en Google OAuth: {str(e)}",
            )
