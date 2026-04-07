# app/api/v1/endpoints/auth/google.py
import logging
from urllib.parse import urlparse, urlencode

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

from app.api.v1.dependencies import get_auth_service
from app.core.config import settings
from app.services.auth.AuthService import AuthService

router = APIRouter()

# Construimos la URI de redirección que Google tiene registrada en su consola
REDIRECT_URI = f"{settings.backend_url}/api/v1/auth/callback"

@router.get("/google")
async def google_login(redirect_to: str = None):
    """
    Punto de entrada para el login de Google.
    'redirect_to' es la URL del frontend a la que volveremos tras el éxito.
    """
    # Si no viene redirect_to, usamos el origen por defecto definido en .env
    target_url = redirect_to or f"{settings.frontend_origin}/dashboard"
    
    auth_params = {
        "client_id": settings.google_client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": target_url,  # Pasamos la URL de destino en el state
        "access_type": "offline",
        "prompt": "select_account",
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(auth_params)}"
    return RedirectResponse(url=auth_url)

@router.get("/callback")
async def google_callback(
    code: str, 
    state: str, 
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Callback donde Google nos envía el código de autorización.
    """
    try:
        # 1. Validar el origen (Seguridad contra Open Redirect)
        # Usamos la lógica robusta de settings.cors_origins que viene del .env
        parsed_url = urlparse(state)
        origin = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        if origin not in settings.cors_origins:
            logging.warning(f"⚠️ Intento de redirección no permitida a: {origin}")
            # Fallback seguro al dominio principal del frontend
            final_url = f"{settings.frontend_origin}/dashboard"
        else:
            final_url = state

        # 2. Intercambiar código por usuario y token interno
        # Esta lógica vive en tu AuthService siguiendo SRP
        user, internal_token, expires_in = auth_service.process_google_login(
            code=code, 
            redirect_uri=REDIRECT_URI
        )

        # 3. Preparar la respuesta de redirección al frontend
        response = RedirectResponse(url=final_url)

        # 4. Configuración inteligente de la Cookie
        is_prod = settings.is_production
        
        # Extraemos el dominio base para que la cookie sea compartida
        # Ejemplo: de 'auth.elrincondeharco.com' sacamos '.elrincondeharco.com'
        cookie_domain = None
        if is_prod:
            # Puedes ponerlo manual o extraerlo de settings.frontend_origin
            # Importante: El punto inicial permite que funcione en TODOS los subdominios
            cookie_domain = ".elrincondeharco.com" 

        response.set_cookie(
            key="access_token",
            value=internal_token,
            httponly=True,
            max_age=expires_in * 60,
            path="/",
            # Crucial: 'none' requiere 'secure=True'
            samesite="none" if is_prod else "lax",
            secure=is_prod, 
            domain=cookie_domain, # <--- ESTO es lo que falta
        )
        
        logging.info(f"✅ Login exitoso para el usuario: {user.email}")
        return response

    except Exception as e:
        logging.error(f"❌ Error en Google Callback: {str(e)}")
        # En caso de error, devolvemos al usuario al login con un mensaje
        error_redirect = f"{settings.frontend_origin}/login?error=auth_failed"
        return RedirectResponse(url=error_redirect)