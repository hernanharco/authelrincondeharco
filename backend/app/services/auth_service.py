from datetime import datetime, timedelta, timezone
from google.oauth2 import id_token
from google.auth.transport import requests
from google.auth.exceptions import TransportError
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt
from app.core.config import settings
from app.models.user import User


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def login_with_google(self, token: str, origin: str) -> tuple[User, str, int]:
        try:
            # 1. Validar token con Google
            idinfo = id_token.verify_oauth2_token(
                token, requests.Request(), settings.google_client_id
            )

            email = idinfo.get("email")

            # 2. Buscar usuario en BD
            user = self.db.query(User).filter(User.email == email).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Usuario no registrado. Contacte con el administrador.",
                )

            # 3. Verificar estado de la cuenta
            if not user.is_active or user.is_locked:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cuenta desactivada o bloqueada.",
                )

            # 4. Generar JWT interno
            internal_token, expires_in = self._create_access_token(user)

            return user, internal_token, expires_in

        except Exception as e:
            # Manejar diferentes tipos de errores
            if "invalid_token" in str(e) or "token" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token de Google inválido o expirado.",
                )
            elif "network" in str(e).lower() or "connection" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="No se pudo contactar con los servidores de Google.",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error en autenticación: {str(e)}",
                )

    def _create_access_token(self, user: User) -> tuple[str, int]:
        expires_in = settings.access_token_expire_minutes * 60  # en segundos
        expire = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "exp": expire,
        }

        token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
        return token, expires_in
