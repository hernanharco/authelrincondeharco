"""
ruta. backend/api/v1/endpoints/auth/google.py
Endpoint de Google OAuth - Principio de Responsabilidad Única
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.user import UserLoginResponse
from app.schemas.auth import GoogleLoginRequest
from app.interfaces.auth.IAuthService import IAuthService
from app.api.v1.dependencies import get_auth_service

router = APIRouter()


@router.post("/google", response_model=UserLoginResponse)
async def login_with_google(
    google_data: GoogleLoginRequest,
    auth_service: IAuthService = Depends(get_auth_service),
):
    """
    Endpoint de login con Google OAuth.

    Args:
        google_data: Token de Google y origen
        auth_service: Servicio de autenticación inyectado

    Returns:
        Token de acceso y datos del usuario

    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
    """
    try:
        # Autenticar con Google
        user, token, expires_in = await auth_service.authenticate_with_google(
            google_data.token, google_data.origin or "google"
        )

        return UserLoginResponse(
            access_token=token, token_type="bearer", expires_in=expires_in, user=user
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en el servidor",
        )
