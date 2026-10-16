# app/api/v1/endpoints/auth/google.py
import json
import logging
from typing import List
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


def _host_matches(host: str, allowed_domain: str) -> bool:
    """True si `host` es el propio dominio declarado o un subdominio estricto.

    `rincom.es.evil.com` NO matchea `rincom.es` (el sufijo no engaña).
    """
    clean_host = host.lower().rstrip(".")
    allowed = allowed_domain.lower().strip().rstrip(".")
    if allowed.startswith("*."):
        allowed = allowed[2:]
    if not allowed:
        return False
    return clean_host == allowed or clean_host.endswith(f".{allowed}")


def _allowed_redirect_hosts() -> List[str]:
    """Dominios que pueden recibir el hub token: los declarados en
    ALLOWED_REDIRECT_ORIGINS + el host del frontend propio del hub.
    """
    hosts = [str(h) for h in (settings.allowed_redirect_origins or [])]
    hub_host = (urlparse(FRONTEND_URL).hostname or "").lower()
    if hub_host:
        hosts.append(hub_host)
    return hosts


def _is_allowed_redirect(url: str) -> bool:
    """S3 (apk-login-deeplink): el token solo sale hacia un host permitido.

    - https obligatorio en producción (http queda para dev local).
    - `https://bueno@evil.com` no engaña: se valida el hostname real.
    """
    parsed = urlparse(url)
    if parsed.username or parsed.password:
        return False
    # Un puerto explícito solo se tolera fuera de producción (dev usa
    # localhost:5173 / :4321); en prod, rincom.es:8443 no es rincom.es.
    try:
        port = parsed.port
    except ValueError:
        return False
    if settings.is_production and port not in (None, 443, 80):
        return False
    scheme = (parsed.scheme or "").lower()
    if scheme == "https":
        pass
    elif scheme == "http":
        if settings.is_production:
            return False
    else:
        return False
    host = parsed.hostname
    if not host:
        return False
    return any(_host_matches(host, allowed) for allowed in _allowed_redirect_hosts())


def _is_allowed_app_redirect(url: str) -> bool:
    """T6: URL de esquema propio (p. ej. `riderdefensa://auth/callback`) que
    está declarada en ALLOWED_REDIRECT_APP_URLS.

    El esquema de app es el único camino confiable para devolver el token
    cuando el login corre en el navegador de un APK: el navegador no maneja
    el esquema ⇒ el sistema operativo abre la app que lo declara. Se valida
    esquema + host + path (exacto o subcamino) contra la lista declarada.
    """
    allowed = [str(u) for u in (settings.allowed_redirect_app_urls or [])]
    if not allowed:
        return False
    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()
    if not scheme or scheme in ("http", "https"):
        return False
    # Mismo criterio que la rama web: ni userinfo (`riderdefensa://x@auth/…`)
    # ni puertos fuera del default.
    if parsed.username or parsed.password:
        return False
    try:
        if parsed.port is not None:
            return False
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    path = parsed.path or ""
    for entry in allowed:
        ref = urlparse(entry)
        if (ref.scheme or "").lower() != scheme:
            continue
        if (ref.hostname or "").lower() != host:
            continue
        ref_path = ref.path or ""
        if path == ref_path or path.startswith(f"{ref_path}/"):
            return True
    return False


def _get_frontend_redirect(state: str = "") -> str:
    """
    Extrae el redirect_to del state de OAuth.
    redirect_to puede ser URL completa (http://...) o ruta relativa (/dashboard).
    Si es completa, se usa directamente SOLO si su host está permitido
    (_is_allowed_redirect); si no, se cae al login del hub: el hub JWT nunca
    sale hacia un dominio no declarado. Si es relativa, se antepone FRONTEND_URL.
    """
    default = f"{FRONTEND_URL}/dashboard"
    if not state:
        return default
    try:
        payload = json.loads(state)
        redirect_to = payload.get("redirect_to", "")
        if not redirect_to:
            return default
        scheme = (urlparse(redirect_to).scheme or "").lower()
        if scheme and scheme not in ("http", "https"):
            if _is_allowed_app_redirect(redirect_to):
                return redirect_to
            logging.warning(
                "⛔ redirect_to rechazado (esquema de app no permitido): %s",
                redirect_to,
            )
            return f"{FRONTEND_URL}/login"
        # URL absoluta http(s): se valida contra la allowlist y se usa directa.
        # El esquema se compara en minúsculas (urlparse ya lo normaliza), así
        # que `HTTPS://…` no se cuela por la rama "relativa".
        if scheme in ("http", "https"):
            if _is_allowed_redirect(redirect_to):
                return redirect_to
            logging.warning(
                "⛔ redirect_to rechazado (host no permitido): %s", redirect_to
            )
            return f"{FRONTEND_URL}/login"
        # Si es ruta relativa, anteponer FRONTEND_URL
        return f"{FRONTEND_URL}{redirect_to}"
    except (json.JSONDecodeError, TypeError):
        return default


def _status_or_error_redirect(state: str, query: str) -> RedirectResponse:
    """
    Redirect de post-login no exitoso (pending / error) con `query` ya codificada
    ("status=pending" o "error=...").

    Si el flujo vino de un spoke — es decir, `_get_frontend_redirect(state)`
    resuelve a un redirect_to con origin distinto de FRONTEND_URL — se
    redirige a ese redirect_to conservando la query que el spoke entiende.
    Si no hay redirect_to (o es same-origin/relativo), se mantiene el destino
    histórico: FRONTEND_URL/login. Nunca se añade el token.
    """
    redirect_dest = _get_frontend_redirect(state)
    if redirect_dest.startswith(FRONTEND_URL):
        redirect_dest = f"{FRONTEND_URL}/login"
    separator = "&" if "?" in redirect_dest else "?"
    return RedirectResponse(url=f"{redirect_dest}{separator}{query}")


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
            return _status_or_error_redirect(state, "status=pending")

        logging.error(f"❌ Error en Google Callback: {e.detail}")
        return _status_or_error_redirect(
            state, f"error={urlencode({'detail': str(e.detail)})}"
        )
    except Exception as e:
        logging.error(f"❌ Error en Google Callback: {str(e)}")
        return _status_or_error_redirect(
            state, f"error={urlencode({'detail': 'Error técnico al procesar el login'})}"
        )
