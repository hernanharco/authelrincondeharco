"""
app/api/v1/endpoints/auth/google.py
Endpoint Google OAuth - flujo redirect con popup
"""
import json
import urllib.parse
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from app.services.auth.AuthService import AuthService
from app.core.config import settings
from app.api.v1.dependencies import get_auth_service

router = APIRouter()

FRONTEND_ORIGIN = "http://localhost:4321"
REDIRECT_URI = "http://localhost:8001/api/v1/auth/callback"


@router.get("/google")
async def google_login():
    """Inicia el flujo OAuth redirigiendo a Google."""
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
    """Google redirige aquí. Procesa el código y envía postMessage al frontend."""
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
                    "role": user.role.value if hasattr(user.role, "value") else user.role,
                },
            },
        }
        content = f"""<!DOCTYPE html>
<html>
  <body>
    <script>
      window.opener.postMessage({json.dumps(auth_data)}, "{FRONTEND_ORIGIN}");
      window.close();
    </script>
  </body>
</html>"""
        return HTMLResponse(content=content)

    except Exception as e:
        error_str = str(e)
        # Detectar PENDING_APPROVAL del HTTPException
        if "PENDING_APPROVAL" in error_str:
            msg = "PENDING_APPROVAL"
        else:
            msg = error_str

        error_data = {"type": "AUTH_ERROR", "error": msg}
        return HTMLResponse(
            content=f"""<!DOCTYPE html>
<html>
  <body>
    <script>
      window.opener.postMessage({json.dumps(error_data)}, "{FRONTEND_ORIGIN}");
      window.close();
    </script>
  </body>
</html>""",
            status_code=200,  # 200 para que el popup no bloquee el script
        )
