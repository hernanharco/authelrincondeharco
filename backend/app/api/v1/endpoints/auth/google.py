"""
ruta: backend/api/v1/endpoints/auth/google.py
Endpoint Google OAuth - flujo redirect con popup
"""

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
import json
import urllib.parse

from app.db.session import get_db
from app.services.auth.AuthService import AuthService
from app.core.config import settings
from app.api.v1.dependencies import get_auth_service

router = APIRouter()


@router.get("/google")
async def google_login():
    """Inicia el flujo OAuth redirigiendo a Google."""
    redirect_uri = "http://localhost:8001/api/v1/auth/callback"

    auth_params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    }

    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(auth_params)}"
    return RedirectResponse(url=auth_url)


@router.get("/callback", response_class=HTMLResponse)
async def google_callback(
    code: str, auth_service: AuthService = Depends(get_auth_service)
):
    """Google redirige aquí. Procesa el código y envía postMessage al frontend."""
    frontend_origin = "http://localhost:4321"

    try:
        user, internal_token, expires_in = auth_service.process_google_login(
            code=code, redirect_uri="http://localhost:8001/api/v1/auth/callback"
        )

        auth_data = {
            "type": "AUTH_SUCCESS",
            "payload": {
                "token": internal_token,
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "role": (
                        user.role.value if hasattr(user.role, "value") else user.role
                    ),
                },
            },
        }

        content = f"""<!DOCTYPE html>
<html>
  <body>
    <p>Autenticación exitosa. Redirigiendo...</p>
    <script>
      window.opener.postMessage({json.dumps(auth_data)}, "{frontend_origin}");
      window.close();
    </script>
  </body>
</html>"""
        return HTMLResponse(content=content)

    except Exception as e:
        error_data = {"type": "AUTH_ERROR", "error": str(e)}
        return HTMLResponse(
            content=f"""<script>
  window.opener.postMessage({json.dumps(error_data)}, "{frontend_origin}");
  window.close();
</script>""",
            status_code=400,
        )
