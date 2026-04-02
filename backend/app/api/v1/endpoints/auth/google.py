"""
app/api/v1/endpoints/auth/google.py
Endpoint Google OAuth - flujo redirect con popup
"""

import json
import urllib.parse
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from app.services.auth.AuthService import AuthService
from app.core.config import settings
from app.api.v1.dependencies import get_auth_service

router = APIRouter()

# Usamos configuración centralizada desde settings
FRONTEND_ORIGIN = settings.frontend_origin or "http://localhost:4321"
REDIRECT_URI = f"{settings.backend_url}/api/v1/auth/callback"


@router.get("/google")
async def google_login():
    auth_params = {
        "client_id": settings.google_client_id,
        "redirect_uri": REDIRECT_URI,
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
    def make_html(data: dict) -> str:
        return f"""<!DOCTYPE html>
<html>
  <body>
    <script>
      window.opener.postMessage({json.dumps(data)}, "{FRONTEND_ORIGIN}");
      window.close();
    </script>
  </body>
</html>"""

    try:
        user, internal_token, expires_in = auth_service.process_google_login(
            code=code, redirect_uri=REDIRECT_URI
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
        return HTMLResponse(content=make_html(auth_data))

    except HTTPException as e:
        # HTTPException capturada explicitamente
        msg = e.detail if isinstance(e.detail, str) else str(e.detail)
        error_data = {"type": "AUTH_ERROR", "error": msg}
        return HTMLResponse(content=make_html(error_data), status_code=200)

    except Exception as e:
        error_data = {"type": "AUTH_ERROR", "error": str(e)}
        return HTMLResponse(content=make_html(error_data), status_code=200)
