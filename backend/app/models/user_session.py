"""
UserSession model — sesiones persistentes con refresh token (feature
persistent-mobile-session).

Una fila = una "sesión" del cliente (un dispositivo logueado). La vida útil
la da `expires_at` (90 días desde la PRIMERA creación de la familia; la
rotación del refresh NO la extiende — mismo criterio que el cap del spoke).
`revoked_at` marca el cierre (logout local, cierre remoto desde otro
dispositivo o reuse detection). El refresh token nunca se almacena en claro:
solo su SHA-256 hex (`refresh_token_hash`).

`sid` (session id) es el claim que viaja en los hub JWT mintidos desde una
sesión: el id de ESTA fila. `family_id` agrupa las rotaciones de un mismo
login para poder revocar la familia entera ante un refresh reutilizado.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.models.base import Base


class UserSession(Base):
    """Registro de sesión persistente de un usuario."""

    __tablename__ = "user_sessions"

    id = Column(
        String(36),
        primary_key=True,
        comment="UUID de la sesión — es el claim sid de los hub JWT",
    )

    family_id = Column(
        String(36),
        nullable=False,
        index=True,
        comment="Agrupa las rotaciones de un mismo login (reuse detection)",
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK al usuario dueño de la sesión",
    )

    refresh_token_hash = Column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        comment="SHA-256 hex del refresh token — nunca en claro",
    )

    user_agent = Column(
        String(512),
        nullable=True,
        comment="User-Agent reportado al crear la sesión (best-effort)",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Inicio de la familia — de aquí corren los 90 días",
    )

    last_seen_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Última actividad conocida (refresh/data-token, best-effort)",
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="Expiración de la sesión (90 d desde la creación de la familia)",
    )

    revoked_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="NULL = vigente; con valor = revocada (logout/remoto/reuse)",
    )

    def __repr__(self) -> str:
        return (
            f"<UserSession(id={self.id}, user={self.user_id}, "
            f"revoked={self.revoked_at is not None})>"
        )
