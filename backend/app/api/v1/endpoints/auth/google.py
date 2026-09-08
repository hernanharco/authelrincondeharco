# app/api/v1/endpoints/auth/google.py
import json
import logging
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from app.api.v1.dependencies import get_auth_service
from app.core.config import settings
from app.services.auth.AuthService import AuthService

router = APIRouter()

REDIRECT_URI = f"{settings.backend_url}/api/v1/auth/callback"
FRONTEND_URL = settings.frontend_origin or "http://localhost:4321"


@router.get("/google")
async def google_login(redirect_to: str = "/dashboard"):
    """
    Inicia el flujo de Google OAuth.
    redirect_to se guarda en el state de OAuth para redirigir después del login.
    """
    state_payload = json.dumps({"redirect_to": redirect_to})

    auth_params = {
        "client_id": settings.google_client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
        "state": state_payload,
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(auth_params)}"
    return RedirectResponse(url=auth_url)


def _get_frontend_redirect(state: str = "") -> str:
    """
    Extrae el redirect_to del state de OAuth.
    redirect_to puede ser URL completa (http://...) o ruta relativa (/dashboard).
    Si es completa, se usa directamente. Si es relativa, se antepone FRONTEND_URL.
    """
    default = f"{FRONTEND_URL}/dashboard"
    if not state:
        return default
    try:
        payload = json.loads(state)
        redirect_to = payload.get("redirect_to", "")
        if not redirect_to:
            return default
        # Si ya es URL completa, usarla directamente
        if redirect_to.startswith("http://") or redirect_to.startswith("https://"):
            return redirect_to
        # Si es ruta relativa, anteponer FRONTEND_URL
        return f"{FRONTEND_URL}{redirect_to}"
    except (json.JSONDecodeError, TypeError):
        return default


@router.get("/callback")
async def google_callback(
    code: str,
    state: str = "",
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        # Extraer el origin (sitio de origen) del redirect_to antes de procesar
        origin = None
        if state:
            try:
                payload = json.loads(state)
                redirect_to = payload.get("redirect_to", "")
                if redirect_to.startswith("http"):
                    parsed = urlparse(redirect_to)
                    # Extraer dominio principal: "www.rincom.es" -> "rincom"
                    host = parsed.hostname or ""
                    # Quitar "www." si existe
                    if host.startswith("www."):
                        host = host[4:]
                    # Extraer nombre del dominio antes del TLD: "rincom.es" -> "rincom"
                    origin = host.split(".")[0] if host else None
            except (json.JSONDecodeError, TypeError):
                pass

        user, internal_token, expires_in = await auth_service.process_google_login(
            code=code,
            redirect_uri=REDIRECT_URI,
            origin=origin,
        )

        # Login exitoso — setear cookie y redirigir
        is_prod = settings.is_production
        frontend_host = urlparse(FRONTEND_URL).hostname or "localhost"
        cookie_domain = f".{frontend_host.split('.', 1)[1]}" if is_prod else "localhost"

        # Determinar destino
        redirect_dest = _get_frontend_redirect(state)
        is_superadmin = user.role.value == "SUPERADMIN" if hasattr(user, 'role') else False
        is_authcore_frontend = redirect_dest.startswith(FRONTEND_URL)

        if is_superadmin and is_authcore_frontend:
            # SUPERADMIN en authCore → ir directo al dashboard
            redirect_dest = f"{FRONTEND_URL}/dashboard"
        elif is_authcore_frontend:
            # Usuario normal en authCore → select-tenant
            redirect_dest = f"{FRONTEND_URL}/select-tenant"
        # Si el destino es otro sitio (nanatamoda, rincom, etc.) → mantener el redirect_to original
        # El token se pasa vía cookie o PATH según el caso

        # Crear response con la URL correcta
        if not redirect_dest.startswith(FRONTEND_URL):
            # Cross-origin: pasar token como query param para que el sitio lo reciba
            separator = "&" if "?" in redirect_dest else "?"
            token_url = f"{redirect_dest}{separator}token={internal_token}"
            response = RedirectResponse(url=token_url)
        else:
            response = RedirectResponse(url=redirect_dest)

        # Setear cookie en TODOS los casos
        response.set_cookie(
            key="access_token",
            value=internal_token,
            httponly=True,
            max_age=expires_in,
            path="/",
            samesite="none" if is_prod else "lax",
            secure=is_prod,
            domain=cookie_domain,
        )

        logging.info(f"✅ Login Google exitoso para: {user.email}")
        return response

    except HTTPException as e:
        if e.detail == "PENDING_APPROVAL":
            logging.info(f"⏳ Nuevo usuario registrado vía Google: pendiente de aprobación")
            return RedirectResponse(
                url=f"{FRONTEND_URL}/login?status=pending"
            )

        logging.error(f"❌ Error en Google Callback: {e.detail}")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error={urlencode({'detail': str(e.detail)})}"
        )
    except Exception as e:
        logging.error(f"❌ Error en Google Callback: {str(e)}")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error={urlencode({'detail': 'Error técnico al procesar el login'})}"
        )
