"""
Security utilities for authentication and authorization.
"""

import bcrypt
from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, UserRole

# --- CLASE PERSONALIZADA PARA COOKIES ---

class OAuth2PasswordBearerWithCookie(OAuth2PasswordBearer):
    """
    Busca el token primero en Cookies httpOnly y luego en Authorization header.
    Permite que Swagger y Postman sigan funcionando con Bearer token.
    """
    async def __call__(self, request: Request) -> Optional[str]:
        token: str = request.cookies.get("access_token")
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

# --- TOKENS JWT ---

def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

# --- DEPENDENCIAS BASE ---

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales o la sesión ha expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
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