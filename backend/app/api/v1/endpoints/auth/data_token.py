"""
Data Token — JWT con scope Supabase/PostgREST.

El hub JWT lleva `role` = rol de aplicación (p.ej. SUPERADMIN). PostgREST
interpreta el claim `role` como ROL DE POSTGRES, así que rechaza ese token con
`42501 role ... does not exist`. Este endpoint emite un SEGUNDO token para que
el spoke lo use como cabecera `Authorization` frente a Supabase, con el rol
literal `authenticated`.

El token de datos se construye SIEMPRE en el servidor a partir del usuario
autenticado: nunca se leen claims del body de la petición.
"""

import os
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.api.v1.dependencies import get_token_service
from app.api.v1.endpoints.auth.sessions import get_session_id_claim
from app.core.config import settings
from app.core.crypto import get_public_key
from app.core.security import get_current_active_user, oauth2_scheme
from app.db.session import get_db
from app.interfaces.auth.ITokenService import ITokenService
from app.models.user import User
from app.models.user_session import UserSession
from app.schemas.auth import TokenResponse

# ── Vida del data token ────────────────────────────────────────────────────
# `app/core/config.py` queda fuera de las superficies de edición de esta
# tarea, así que el TTL vive aquí como constante de módulo. Se conserva el
# patrón env→valor del repo (igual que ACCESS_TOKEN_EXPIRE_MINUTES): se puede
# sobrescribir con la variable de entorno DATA_TOKEN_EXPIRE_SECONDS (segundos).
DATA_TOKEN_EXPIRE_SECONDS: int = int(os.getenv("DATA_TOKEN_EXPIRE_SECONDS", "900"))

# Literales del token de datos. El rol es SIEMPRE el rol de Postgres que
# PostgREST espera para usuarios autenticados; jamás se copia el rol de
# aplicación del usuario (SUPERADMIN/ADMIN/...).
DATA_TOKEN_ROLE = "authenticated"
DATA_TOKEN_TYPE = "data"

router = APIRouter()


async def get_hub_token_claims(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    """
    Claims decodificados del hub JWT que autentica la petición.

    El token ya fue validado por `get_current_active_user` (misma cabecera
    Authorization); aquí solo se re-lee su payload para heredar el claim
    `tenant` que mintió `/users/select-tenant`. Si la decodificación fallara
    se devuelve `{}`: el 401 lo garantiza la dependencia de usuario.
    """
    try:
        return jwt.decode(
            token,
            get_public_key(),
            algorithms=[settings.algorithm],
            audience=settings.jwt_audience,
        )
    except JWTError:
        return {}


@router.post("/data-token", response_model=TokenResponse)
async def data_token(
    user: User = Depends(get_current_active_user),
    token_service: ITokenService = Depends(get_token_service),
    hub_claims: dict[str, Any] = Depends(get_hub_token_claims),
    sid: str | None = Depends(get_session_id_claim),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Minta un data token con scope Supabase para el usuario autenticado.

    Requiere un hub JWT válido (Authorization: Bearer). No se lee ningún body:
    los claims se construyen solo en el servidor desde el usuario.

    Claims emitidos:
        sub    → str(user.id) (igual que el hub token)
        role   → "authenticated" (rol Postgres que espera PostgREST)
        type   → "data"
        tenant → {id, slug, name} heredado del hub JWT (select-tenant)
        exp/iat/jti → los pone TokenService (RS256, kid authcore-key-1)

    Returns:
        access_token, token_type ("bearer") y expires_in (segundos)

    Raises:
        HTTPException: 401 si el hub token falta, es inválido o ha expirado
    """
    # ── Sesión persistente: si el hub trae `sid`, la sesión debe estar viva ─
    # (S9, persistent-mobile-session). Es el punto donde el cierre remoto se
    # hace efectivo en ≤15 min: el spoke pide data-token con esa cadencia.
    # Los hubs SIN `sid` (otros spokes, frontend del hub) no se verifican (S5).
    if sid:
        row = await db.get(UserSession, sid)
        now = datetime.now(timezone.utc)
        expires_at = row.expires_at if row is not None else None
        if expires_at is not None and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if (
            row is None
            or row.revoked_at is not None
            or (expires_at is not None and expires_at <= now)
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sesión revocada o expirada",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # last_seen_at best-effort (no en cada request, solo al rotar datos)
        await db.execute(
            update(UserSession)
            .where(UserSession.id == sid)
            .values(last_seen_at=func.now())
        )
        await db.commit()

    # ── Claims mínimos: identidad mínima + rol Postgres literal ──
    token_data: dict[str, object] = {
        "sub": str(user.id),
        "role": DATA_TOKEN_ROLE,
        "type": DATA_TOKEN_TYPE,
    }

    # ── Sesión: el data token hereda el claim sid (re-minteo, S9) ──
    if sid:
        token_data["sid"] = sid

    # ── Tenant: hereda el claim del hub JWT entrante (A11) ──────
    # La spoke pide el tenant explícitamente vía /users/select-tenant, y ese
    # hub JWT (con el claim `tenant`) es el que llega a este endpoint. NO se
    # lee el campo legacy users.tenant_id: es NULL en producción (la membresía
    # vive en la tabla M:N user_tenants) y usarlo dejaba el data token SIN
    # tenant → el RLS de la spoke no matcheaba → 0 filas sin error.
    # Tampoco se resuelve la membresía a ciegas: un usuario con varias
    # membresías sería ambiguo, y eso lo decide la spoke (A11).
    tenant_claim = hub_claims.get("tenant")
    if isinstance(tenant_claim, dict) and tenant_claim.get("id") is not None:
        token_data["tenant"] = {
            "id": tenant_claim["id"],
            "slug": tenant_claim.get("slug"),
            "name": tenant_claim.get("name"),
        }

    # ── Firma RS256 con exp/iat/jti incluidos por TokenService ───
    issued_at = datetime.now(timezone.utc)
    access_token, expires_at = await token_service.create_access_token(
        token_data, expires_delta=DATA_TOKEN_EXPIRE_SECONDS
    )
    expires_in = int((expires_at - issued_at).total_seconds())

    return TokenResponse(
        access_token=access_token, token_type="bearer", expires_in=expires_in
    )
