"""
EmailService — correos transaccionales vía Resend (api.resend.com).

Responsabilidad única: resolver destinatario/CTA y entregar el correo de
aprobación de acceso. Reglas de la feature approval-email:
- Sin RESEND_API_KEY no se hace ninguna llamada HTTP: se loguea y se omite.
- Sin website_url en el tenant (o sin tenant) el CTA cae al login del hub.
- Lanza en fallo de red/HTTP: el caller (UserUpdateService) decide — la
  aprobación NUNCA falla por el correo (fail-open).
"""
import logging
from typing import Optional

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.tenant import Tenant
from app.models.user import User
from app.services.email.approval_email_template import (
    approval_html,
    approval_subject,
    approval_text,
)

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"
LOGIN_FALLBACK_APP = "AuthCore"
LOGIN_PATH = "/login"


class EmailService:
    """SRP: entregar el correo de aprobación de una cuenta."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _tenant_of_origin(self, user: User) -> Optional[Tenant]:
        """Tenant activo cuyo slug coincide con users.origin (case-insensitive).

        Mismo criterio que MembershipService.assign_by_origin.
        """
        if not user.origin:
            return None
        result = await self.db.execute(
            select(Tenant).where(
                func.lower(Tenant.slug) == user.origin.lower(),
                Tenant.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    def _cta_url(self, tenant: Optional[Tenant]) -> Optional[str]:
        """URL del CTA: sitio de la aplicación solicitada, si no, login del hub."""
        if tenant is not None and tenant.website_url:
            return tenant.website_url
        frontend = (settings.frontend_origin or "").rstrip("/")
        if not frontend:
            logger.error(
                "Sin FRONTEND_ORIGIN no hay URL de login: correo omitido"
            )
            return None
        return f"{frontend}{LOGIN_PATH}"

    async def send_approval_email(self, user: User) -> bool:
        """
        Envía el correo de bienvenida de aprobación con CTA a la aplicación.

        Returns:
            True si Resend aceptó el correo; False si se omitió (sin API key,
            sin email del usuario o sin URL de destino).

        Raises:
            httpx.HTTPError: fallo de red o respuesta no-2xx de Resend.
        """
        if not settings.resend_api_key:
            logger.warning(
                "RESEND_API_KEY sin configurar: correo de aprobación "
                "del user %s omitido",
                user.id,
            )
            return False
        if not user.email:
            logger.warning(
                "user %s sin email: correo de aprobación omitido", user.id
            )
            return False

        tenant = await self._tenant_of_origin(user)
        cta_url = self._cta_url(tenant)
        if cta_url is None:
            return False
        app_name = tenant.name if tenant is not None else LOGIN_FALLBACK_APP

        payload = {
            "from": settings.emails_from,
            "to": [user.email],
            "subject": approval_subject(app_name),
            "html": approval_html(user.full_name or user.username, app_name, cta_url),
            "text": approval_text(user.full_name or user.username, app_name, cta_url),
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                RESEND_API_URL,
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                json=payload,
            )
        response.raise_for_status()
        logger.info("Correo de aprobación enviado a user %s (%s)", user.id, user.email)
        return True
