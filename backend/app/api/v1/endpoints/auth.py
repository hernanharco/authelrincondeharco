from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.auth_service import AuthService
from app.schemas.user import GoogleLogin, UserLoginResponse
from app.core.config import settings

router = APIRouter()

@router.post("/google", response_model=UserLoginResponse, status_code=status.HTTP_200_OK)
async def google_login(
    response: Response,
    data: GoogleLogin,
    db: Session = Depends(get_db)
):
    auth_service = AuthService(db)

    # Ahora recibimos los 3 valores del servicio
    user, internal_token, expires_in = auth_service.login_with_google(
        token=data.token,
        origin=data.origin
    )

    # Cookie HTTP-only
    is_prod = settings.ENVIRONMENT == "production"
    response.set_cookie(
        key="access_token",
        value=internal_token,
        httponly=True,
        secure=is_prod,
        samesite="lax" if not is_prod else "none",
        max_age=expires_in,
        path="/",
    )

    return UserLoginResponse(
        access_token=internal_token,
        token_type="bearer",
        expires_in=expires_in,
        user=user
    )