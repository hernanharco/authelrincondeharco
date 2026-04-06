# app/api/v1/endpoints/auth/google.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from app.services.auth.AuthService import AuthService
from app.core.config import settings
from app.api.v1.dependencies import get_auth_service
from urllib.parse import urlparse, urlencode
import logging

router = APIRouter()

# Lista blanca de dominios permitidos para evitar ataques de redirección abierta
ALLOWED_ORIGINS = [
    "http://localhost:4321", # Appointment App
    "http://localhost:4322", # Otra App
    "https://tu-dominio-produccion.com"
]

REDIRECT_URI = f"{settings.backend_url}/api/v1/auth/callback"

@router.get("/google")
async def google_login(redirect_to: str = "http://localhost:4321/dashboard"):
    """
    Inicia el flujo. 'redirect_to' ahora debería ser una URL completa 
    enviada desde el frontend.
    """
    auth_params = {
        "client_id": settings.google_client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": redirect_to,  # Guardamos la URL de retorno completa en el state
        "access_type": "offline",
        "prompt": "select_account",
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(auth_params)}"
    return RedirectResponse(url=auth_url)

@router.get("/callback")
async def google_callback(
    code: str, 
    state: str, # Aquí Google nos devuelve la URL completa (ej: http://localhost:4321/dashboard)
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        # 1. Validar el origen de la URL de retorno por seguridad
        parsed_url = urlparse(state)
        origin = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Si el origen no está permitido, usamos el por defecto de settings
        if origin not in ALLOWED_ORIGINS:
            logging.warning(f"Intento de redirección no permitida a: {origin}")
            final_url = f"{settings.frontend_origin}/dashboard"
        else:
            final_url = state

        # 2. Procesar el login con Google
        user, internal_token, expires_in = auth_service.process_google_login(
            code=code, redirect_uri=REDIRECT_URI
        )

        # 3. Preparar respuesta con redirección dinámica
        response = RedirectResponse(url=final_url)

        # 4. Configurar Cookie
        # IMPORTANTE: En localhost con puertos distintos (4321 y 4322), 
        # la cookie se comparte si el dominio es 'localhost'.
        response.set_cookie(
            key="access_token",
            value=internal_token,
            httponly=True,
            max_age=expires_in,
            samesite="lax",
            # En desarrollo (localhost/HTTP) secure debe ser False. 
            # En producción (HTTPS) debe ser True.
            secure=False if "localhost" in settings.backend_url else True,
            path="/"
        )
        return response

    except Exception as e:
        logging.error(f"Error en Google Callback: {str(e)}")
        # En caso de error, intentamos volver al login del origen solicitado
        parsed_url = urlparse(state)
        error_url = f"{parsed_url.scheme}://{parsed_url.netloc}/login?error=auth_failed"
        return RedirectResponse(url=error_url)