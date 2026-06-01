"""
Security utilities for authentication and authorization.
Usa RS256: firma con clave privada, verifica con clave pública.
Incluye iat (issued at) y jti (JWT ID) para trazabilidad de tokens.
"""

import uuid
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.crypto import get_private_key, get_public_key
from app.db.session import get_db
from app.models.user import User, UserRole

# --- CLASE PERSONALIZADA PARA COOKIES ---

class OAuth2PasswordBearerWithCookie(OAuth2PasswordBearer):
    """
    Busca el token primero en Cookies httpOnly y luego en Authorization header.
    Permite que Swagger y Postman sigan funcionando con Bearer token.
    """
    async def __call__(self, request: Request) -> Optional[str]:
        token: str = request.cookies.get("session") or request.cookies.get("access_token")
        if not token:
            token = await super().__call__(request)
        return token

oauth2_scheme = OAuth2PasswordBearerWithCookie(
    tokenUrl=f"{settings.API_V1_STR}/auth/login-form"
)

# --- CONTRASEÑAS ---

def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False

# --- TOKENS JWT (RS256) ---

def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Crea un JWT firmado con RSA (RS256) incluyendo iat y jti."""
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": now,
        "jti": str(uuid.uuid4()),
    }
    private_key = get_private_key()
    return jwt.encode(to_encode, private_key, algorithm=settings.algorithm)

# --- DEPENDENCIAS BASE (ASYNC) ---

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales o la sesión ha expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        public_key = get_public_key()
        payload = jwt.decode(token, public_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    return current_user

# --- GUARDIANES POR ROL ---
# Jerarquía: SUPERADMIN > ADMIN > MANAGER > USER > VIEWER

def get_current_superadmin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Solo el administrador del SaaS puede acceder."""
    if current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de SuperAdmin"
        )
    return current_user

def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Dueños de negocio y superiores pueden acceder."""
    if current_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de Admin o superior"
        )
    return current_user

def get_current_manager_or_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Managers, admins y superiores pueden acceder."""
    if current_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de Manager o superior"
        )
    return current_user