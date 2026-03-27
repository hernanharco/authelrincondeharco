"""
Schemas de Autenticación - Pydantic Models
"""

from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """Schema para login tradicional."""

    username: str = Field(..., description="Nombre de usuario o email")
    password: str = Field(..., min_length=1, description="Contraseña")


class GoogleLoginRequest(BaseModel):
    """Schema para login con Google."""

    token: str = Field(..., description="Token de Google OAuth")
    origin: Optional[str] = Field(
        default="google", description="Origen de la autenticación"
    )


class LoginResponse(BaseModel):
    """Schema para respuesta de login."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenResponse(BaseModel):
    """Schema para respuesta de token."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class PasswordResetRequest(BaseModel):
    """Schema para solicitud de reset de contraseña."""

    email: EmailStr = Field(..., description="Email del usuario")


class PasswordResetConfirm(BaseModel):
    """Schema para confirmación de reset de contraseña."""

    token: str = Field(..., description="Token de reset")
    new_password: str = Field(..., min_length=6, description="Nueva contraseña")


class RefreshTokenRequest(BaseModel):
    """Schema para refresh token."""

    refresh_token: str = Field(..., description="Token de refresco")


class LogoutRequest(BaseModel):
    """Schema para logout."""

    token: Optional[str] = Field(default=None, description="Token a revocar")
