"""
Endpoint de Login - Principio de Responsabilidad Única
Protegido con rate limiting para prevenir ataques de fuerza bruta.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from urllib.parse import urlparse

from app.schemas.user import UserLoginResponse
from app.schemas.auth import LoginRequest
from app.interfaces.auth.IAuthService import IAuthService
from app.api.v1.dependencies import get_auth_service
from app.core.config import settings
from app.core.ratelimit import limiter, LIMIT_LOGIN
from app.api.v1.endpoints.auth.google import FRONTEND_URL

router = APIRouter()

@router.post("/login", response_model=UserLoginResponse)
@limiter.limit(LIMIT_LOGIN)
async def login(
    request: Request,
    response: Response,
    credentials: LoginRequest,
    auth_service: IAuthService = Depends(get_auth_service),
):
    """
    Endpoint de login tradicional.

    Args:
        credentials: Credenciales del usuario
        auth_service: Servicio de autenticación inyectado

    Returns:
        Token de acceso y datos del usuario

    Raises:
        HTTPException: Si las credenciales son inválidas
    """
    try:
        # Autenticar usuario
        user = await auth_service.authenticate_user(
            credentials.username,
            credentials.password,
            # Contraseña correcta + cuenta inactiva → 403 PENDING_APPROVAL
            # (diferente de las credenciales inválidas → 401 de abajo)
            raise_on_pending=True,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
            )

        # Generar token
        token, expires_in = await auth_service.create_access_token(user)

        # Setear cookie httpOnly (mismos parámetros que el callback Google)
        is_prod = settings.is_production
        frontend_host = urlparse(FRONTEND_URL).hostname or "localhost"
        cookie_domain = f".{frontend_host.split('.', 1)[1]}" if is_prod else "localhost"
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            max_age=expires_in,
            path="/",
            samesite="none" if is_prod else "lax",
            secure=is_prod,
            domain=cookie_domain,
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
