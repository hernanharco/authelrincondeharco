"""
Schemas de sesiones persistentes (feature persistent-mobile-session).
Contrato congelado: odd/tasks/persistent-mobile-session.md, "API contract".
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SessionCreateResponse(BaseModel):
    """POST /auth/sessions → el refresh solo se devuelve UNA vez."""

    session_id: str = Field(..., description="UUID de la sesión (claim sid)")
    refresh_token: str = Field(
        ..., description="Refresh token opaco (se guarda solo su hash)"
    )
    refresh_expires_in: int = Field(
        ..., description="Vida del refresh en segundos (90 d)"
    )


class SessionRefreshResponse(BaseModel):
    """POST /auth/refresh → hub nuevo + refresh rotado."""

    access_token: str = Field(..., description="Hub JWT con claim sid")
    expires_in: int = Field(..., description="Vida del hub en segundos (120 min)")
    refresh_token: str = Field(
        ..., description="Refresh rotado (el anterior queda revocado)"
    )
    refresh_expires_in: int = Field(
        ..., description="Vida del nuevo refresh en segundos"
    )


class SessionInfo(BaseModel):
    """GET /auth/sessions → una sesión vigente del usuario."""

    id: str
    created_at: datetime
    last_seen_at: Optional[datetime] = None
    user_agent: Optional[str] = None
    current: bool = Field(
        ..., description="True si es la sesión del sid del hub recibido"
    )


class RevokeAllResponse(BaseModel):
    """DELETE /auth/sessions → cuántas sesiones se revocaron."""

    revoked: int


SessionList = List[SessionInfo]
