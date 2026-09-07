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

        # Login exitoso — setear cookie y redirigir al frontend
        is_prod = settings.is_production
        frontend_url = _get_frontend_redirect(state)

        # El dominio de la cookie se deriva del FRONTEND_URL actual
        # (ej: auth.rincom.es -> .rincom.es, auth.elrincondeharco.com -> .elrincondeharco.com)
        frontend_host = urlparse(FRONTEND_URL).hostname or "localhost"
        cookie_domain = f".{frontend_host.split('.', 1)[1]}" if is_prod else "localhost"
        response = RedirectResponse(url=frontend_url)
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

        # Si el redirect_to apunta a un origen diferente al de authCore
        # (ej: Portfolio en localhost:4322), NO podemos confiar en que la cookie
        # se comparta entre puertos, o que Astro maneje bien los query params.
        # Pasamos el token en el PATH de la URL (ej: /api/auth/callback/{token})
        # El frontend receptor debe leerlo, validarlo y setear su propia cookie.
        if not frontend_url.startswith(FRONTEND_URL):
            # Reemplazar /api/auth/callback por /api/auth/callback/{token}
            if "/api/auth/callback" in frontend_url:
                token_path = frontend_url.replace("/api/auth/callback", f"/api/auth/callback/{internal_token}")
            else:
                # Fallback: agregar token como query param (poco probable que se use)
                parsed = list(urlparse(frontend_url))
                query = parse_qs(parsed[4])
                query["token"] = internal_token
                parsed[4] = urlencode(query, doseq=True)
                token_path = urlunparse(parsed)
            response = RedirectResponse(url=token_path)
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
