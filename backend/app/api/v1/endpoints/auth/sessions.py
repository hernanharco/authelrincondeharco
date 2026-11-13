"""
Endpoints de sesiones persistentes (feature persistent-mobile-session).

Cuatro rutas bajo /api/v1/auth:

- POST   /sessions         → crea sesión, devuelve el refresh (una sola vez)
- POST   /auth/refresh     → canjea refresh por hub nuevo + refresh rotado
- GET    /sessions         → lista vigentes con flag `current`
- DELETE /sessions/{id}    → revoca una sesión propia
- DELETE /sessions         → revoca todas menos la del sid (o todas)

El refresh token vive solo como SHA-256; la rotación mantiene la expiración
de la familia (90 d desde el primer login, S4) y un refresh ya revocado que
vuelve a presentarse revoca la familia entera (S8, reuse detection).
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from jose import JWTError, jwt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.core.config import settings
from app.core.crypto import get_public_key
from app.core.security import get_current_active_user, oauth2_scheme
from app.db.session import get_db
from app.models.user import User
from app.models.user_session import UserSession
from app.schemas.auth import RefreshTokenRequest
from app.schemas.session import (
    RevokeAllResponse,
    SessionCreateResponse,
    SessionInfo,
    SessionRefreshResponse,
)
from app.services.auth.TokenService import TokenService

router = APIRouter()

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Refresh inválido, revocado o expirado",
    headers={"WWW-Authenticate": "Bearer"},
)


# ── Helpers ─────────────────────────────────────────────────────


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _new_refresh_token() -> str:
    # token_urlsafe(42) → 56 chars ≈ 256 bits de entropía
    return secrets.token_urlsafe(42)


def _aware(value: datetime) -> datetime:
    """Normaliza datetimes naive (SQLite) a UTC para compararlos."""
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


async def get_session_id_claim(
    token: str = Depends(oauth2_scheme),
) -> Optional[str]:
    """Claim `sid` del hub JWT de la petición, o None si no trae uno.

    El token ya fue validado por la dependencia de usuario de cada endpoint;
    aquí solo se relee el payload. Un hub sin `sid` (otros spokes) → None.
    """
    try:
        payload = jwt.decode(
            token,
            get_public_key(),
            algorithms=[settings.algorithm],
            audience=settings.jwt_audience,
        )
    except JWTError:
        return None
    sid = payload.get("sid")
    return sid if isinstance(sid, str) and sid else None


async def _active_session_or_401(db: AsyncSession, digest: str) -> UserSession:
    """Busca la fila por hash del refresh y valida vigencia (S8/S4)."""
    result = await db.execute(
        select(UserSession).where(UserSession.refresh_token_hash == digest)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise _UNAUTHORIZED
    if row.revoked_at is not None:
        # Reuse detection: un refresh ya revocado ⇒ la familia entera cae.
        await db.execute(
            update(UserSession)
            .where(
                UserSession.family_id == row.family_id,
                UserSession.revoked_at.is_(None),
            )
            .values(revoked_at=func.now())
        )
        await db.commit()
        raise _UNAUTHORIZED
    if _aware(row.expires_at) <= datetime.now(timezone.utc):
        raise _UNAUTHORIZED
    return row


# ── POST /auth/sessions ─────────────────────────────────────────


@router.post("/sessions", response_model=SessionCreateResponse)
async def create_session(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SessionCreateResponse:
    """Crea una sesión persistente para el usuario autenticado.

    Devuelve el refresh token una sola vez; en la BD solo queda su hash.
    La expiración (90 d) se fija aquí y NO cambia con las rotaciones.
    """
    refresh = _new_refresh_token()
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    user_agent = (request.headers.get("user-agent") or "").strip()[:512] or None

    row = UserSession(
        id=session_id,
        family_id=session_id,
        user_id=current_user.id,
        refresh_token_hash=_hash_token(refresh),
        user_agent=user_agent,
        expires_at=now + timedelta(seconds=settings.refresh_session_expire_seconds),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)

    return SessionCreateResponse(
        session_id=session_id,
        refresh_token=refresh,
        refresh_expires_in=settings.refresh_session_expire_seconds,
    )


# ── POST /auth/refresh ──────────────────────────────────────────


@router.post("/refresh", response_model=SessionRefreshResponse)
async def refresh_session(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionRefreshResponse:
    """Canjea un refresh vigente por un hub nuevo (120 min) + refresh rotado.

    La rotación revoca la fila vieja y crea otra con la MISMA expiración de
    familia. El hub nuevo lleva claim `sid` = id de la fila vigente.
    """
    row = await _active_session_or_401(db, _hash_token(data.refresh_token))

    result = await db.execute(select(User).where(User.id == row.user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise _UNAUTHORIZED

    # ── Rotación (S8) ──
    new_refresh = _new_refresh_token()
    new_session_id = str(uuid.uuid4())
    await db.execute(
        update(UserSession)
        .where(UserSession.id == row.id, UserSession.revoked_at.is_(None))
        .values(revoked_at=func.now())
    )
    successor = UserSession(
        id=new_session_id,
        family_id=row.family_id,
        user_id=row.user_id,
        refresh_token_hash=_hash_token(new_refresh),
        user_agent=row.user_agent,
        expires_at=row.expires_at,  # misma expiración: 90 d desde el primer login
        last_seen_at=func.now(),
    )
    db.add(successor)
    await db.commit()

    # ── Hub nuevo con sid (S9) ──
    now = datetime.now(timezone.utc)
    token_service = TokenService()
    token, expires_at = await token_service.create_access_token(
        {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "type": "access",
            "sid": new_session_id,
        }
    )
    expires_in = int((expires_at - now).total_seconds())

    return SessionRefreshResponse(
        access_token=token,
        expires_in=expires_in,
        refresh_token=new_refresh,
        refresh_expires_in=settings.refresh_session_expire_seconds,
    )


# ── GET /auth/sessions ──────────────────────────────────────────


@router.get("/sessions", response_model=List[SessionInfo])
async def list_sessions(
    current_user: User = Depends(get_current_active_user),
    sid: Optional[str] = Depends(get_session_id_claim),
    db: AsyncSession = Depends(get_db),
) -> List[SessionInfo]:
    """Sesiones vigentes (no revocadas ni expiradas) del usuario autenticado."""
    result = await db.execute(
        select(UserSession)
        .where(
            UserSession.user_id == current_user.id,
            UserSession.revoked_at.is_(None),
        )
        .order_by(UserSession.created_at.desc())
    )
    now = datetime.now(timezone.utc)
    rows = [row for row in result.scalars().all() if _aware(row.expires_at) > now]

    return [
        SessionInfo(
            id=row.id,
            created_at=row.created_at,
            last_seen_at=row.last_seen_at,
            user_agent=row.user_agent,
            current=sid is not None and row.id == sid,
        )
        for row in rows
    ]


# ── DELETE /auth/sessions[/{id}] ────────────────────────────────


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Revoca UNA sesión propia. Ajena o inexistente → 404 (sin filtrar)."""
    row = await db.get(UserSession, session_id)
    if row is None or row.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sesión no encontrada"
        )
    if row.revoked_at is None:
        row.revoked_at = func.now()
        db.add(row)
        await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/sessions", response_model=RevokeAllResponse)
async def revoke_other_sessions(
    current_user: User = Depends(get_current_active_user),
    sid: Optional[str] = Depends(get_session_id_claim),
    db: AsyncSession = Depends(get_db),
) -> RevokeAllResponse:
    """Revoca todas las sesiones del usuario salvo la del sid recibido.

    Sin `sid` en el hub (petición de un token legado) revoca todas.
    """
    result = await db.execute(
        select(UserSession).where(
            UserSession.user_id == current_user.id,
            UserSession.revoked_at.is_(None),
        )
    )
    rows = [row for row in result.scalars().all() if row.id != sid]
    if not rows:
        return RevokeAllResponse(revoked=0)

    await db.execute(
        update(UserSession)
        .where(UserSession.id.in_([row.id for row in rows]))
        .values(revoked_at=func.now())
    )
    await db.commit()
    return RevokeAllResponse(revoked=len(rows))
