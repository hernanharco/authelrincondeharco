"""
PendingRequestNotifier — aviso a los administradores cuando entra una solicitud.

Reglas de la feature pending-request-insight:

- T3/S3: cuando entra una solicitud de autorización nueva, los administradores
  reciben un correo con nombre, email, origen, fecha y ubicación.
- S4: como máximo un correo por hora. El correo incluye TODAS las solicitudes
  que todavía no fueron avisadas (`approval_notified_at IS NULL`), así una
  ráfaga de N solicitudes dentro de la ventana produce un único correo.
- S5: los destinatarios se resuelven en cada envío desde la tabla: usuarios
  con rol SUPERADMIN o ADMIN y `is_active` verdadero. Sin lista hardcodeada
  ni variable de entorno, para que un colaborador ADMIN nuevo reciba los
  avisos sin tocar código.
- S6: fail-open. Un fallo de Resend se loguea y no marca las solicitudes como
  avisadas, de modo que se reintentan en la ventana siguiente. La solicitud
  del usuario nunca cambia por esto.

El marcado (`approval_notified_at`) se hace DESPUÉS de que Resend acepta el
correo: preferimos un aviso duplicado a una alerta perdida.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.services.email.EmailService import EmailService
from app.types.enums import UserRole, UserStatus

logger = logging.getLogger(__name__)

# Ventana de agrupación (S4): un correo por hora como máximo.
NOTIFICATION_WINDOW = timedelta(hours=1)

# Ruta del panel que lista los pendientes.
DASHBOARD_PATH = "/dashboard/pending"

# Roles que reciben el aviso (S5).
NOTIFY_ROLES = (UserRole.SUPERADMIN, UserRole.ADMIN)


class PendingRequestNotifier:
    """SRP: decidir si toca avisar, a quién, y disparar el correo."""

    def __init__(self, db: AsyncSession, email_service: Optional[EmailService] = None):
        self.db = db
        self.email_service = email_service or EmailService(db)

    async def notify_if_due(self, now: Optional[datetime] = None) -> bool:
        """
        Envía el aviso si hay solicitudes sin notificar y la ventana lo permite.

        Args:
            now: instante de referencia (los tests lo fijan; en producción es UTC).

        Returns:
            True sólo si Resend aceptó un correo en esta llamada.
        """
        moment = now or datetime.now(timezone.utc)

        pending_requests = await self._unnotified_requests()
        if not pending_requests:
            return False

        if not await self._window_is_open(moment):
            logger.info(
                "Aviso de pendientes omitido: ya se envió un correo dentro de la "
                "ventana de %s (%s solicitudes esperan la próxima)",
                NOTIFICATION_WINDOW,
                len(pending_requests),
            )
            return False

        recipients = await self._recipients()
        if not recipients:
            logger.warning(
                "Sin destinatarios (SUPERADMIN/ADMIN activos): %s solicitudes "
                "quedan sin avisar",
                len(pending_requests),
            )
            return False

        sent = await self._send(recipients, pending_requests)
        if not sent:
            return False

        await self._mark_notified(pending_requests, moment)
        return True

    async def _unnotified_requests(self) -> List[User]:
        """Solicitudes pendientes que todavía no entraron en ningún aviso."""
        result = await self.db.execute(
            select(User)
            .where(
                User.status == UserStatus.PENDING,
                User.approval_notified_at.is_(None),
            )
            .order_by(User.created_at.asc())
        )
        return list(result.scalars().all())

    async def _window_is_open(self, moment: datetime) -> bool:
        """True si pasó la ventana desde el último aviso enviado."""
        result = await self.db.execute(
            select(func.max(User.approval_notified_at))
        )
        last_digest = result.scalar_one_or_none()
        if last_digest is None:
            return True
        if last_digest.tzinfo is None:
            last_digest = last_digest.replace(tzinfo=timezone.utc)
        return moment - last_digest >= NOTIFICATION_WINDOW

    async def _recipients(self) -> List[str]:
        """Emails de SUPERADMIN/ADMIN activos, sin duplicados ni vacíos."""
        result = await self.db.execute(
            select(User.email).where(
                User.role.in_(NOTIFY_ROLES),
                User.is_active.is_(True),
                User.email.is_not(None),
            )
        )
        seen: set[str] = set()
        recipients: List[str] = []
        for email in result.scalars().all():
            clean = (email or "").strip().lower()
            if not clean or clean in seen:
                continue
            seen.add(clean)
            recipients.append(clean)
        return recipients

    def _dashboard_url(self) -> Optional[str]:
        """URL del panel de pendientes; None si no hay FRONTEND_ORIGIN."""
        origin = (settings.frontend_origin or "").rstrip("/")
        return f"{origin}{DASHBOARD_PATH}" if origin else None

    async def _send(self, recipients: List[str], requests: List[User]) -> bool:
        """Entrega el correo; cualquier fallo se loguea y devuelve False."""
        try:
            return await self.email_service.send_pending_request_email(
                recipients=recipients,
                requests=requests,
                dashboard_url=self._dashboard_url(),
            )
        except Exception as exc:  # noqa: BLE001 — S6: nunca rompe la solicitud
            logger.error(
                "No se pudo enviar el aviso de %s solicitudes a %s: %s",
                len(requests),
                ", ".join(recipients),
                exc,
            )
            return False

    async def _mark_notified(
        self, requests: List[User], moment: datetime
    ) -> None:
        """Marca las solicitudes incluidas para que no se repitan."""
        for user in requests:
            user.approval_notified_at = moment
        await self.db.commit()
