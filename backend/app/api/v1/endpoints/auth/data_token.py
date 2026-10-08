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

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_tenant_repository, get_token_service
from app.core.security import get_current_active_user
from app.interfaces.auth.ITokenService import ITokenService
from app.interfaces.tenant.ITenantRepository import ITenantRepository
from app.models.user import User
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


@router.post("/data-token", response_model=TokenResponse)
async def data_token(
    user: User = Depends(get_current_active_user),
    token_service: ITokenService = Depends(get_token_service),
    tenant_repository: ITenantRepository = Depends(get_tenant_repository),
) -> TokenResponse:
    """
    Minta un data token con scope Supabase para el usuario autenticado.

    Requiere un hub JWT válido (Authorization: Bearer). No se lee ningún body:
    los claims se construyen solo en el servidor desde el usuario.

    Claims emitidos:
        sub    → str(user.id) (igual que el hub token)
        role   → "authenticated" (rol Postgres que espera PostgREST)
        type   → "data"
        tenant → {id, slug, name} SOLO si el usuario tiene tenant
        exp/iat/jti → los pone TokenService (RS256, kid authcore-key-1)

    Returns:
        access_token, token_type ("bearer") y expires_in (segundos)

    Raises:
        HTTPException: 401 si el hub token falta, es inválido o ha expirado
    """
    # ── Claims mínimos: identidad mínima + rol Postgres literal ──
    token_data: dict[str, object] = {
        "sub": str(user.id),
        "role": DATA_TOKEN_ROLE,
        "type": DATA_TOKEN_TYPE,
    }

    # ── Tenant: solo si el usuario tiene uno (no se inventa) ─────
    tenant_id = getattr(user, "tenant_id", None)
    if tenant_id:
        tenant = await tenant_repository.get_by_id(tenant_id)
        if tenant:
            token_data["tenant"] = {
                "id": tenant.id,
                "slug": tenant.slug,
                "name": tenant.name,
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
