"""
Tests del correo de aprobación vía Resend (feature approval-email).

Al aprobar (botón Aprobar/Re-aprobar → PATCH /users/{id}/status con ACTIVE)
el usuario recibe un correo profesional con CTA al `website_url` del tenant
de su origen. Reglas:
- Solo la transición → ACTIVE envía correo (rechazos y ACTIVE repetido, no).
- Sin RESEND_API_KEY no se hace ninguna llamada HTTP.
- Un fallo de Resend NUNCA rompe la aprobación (fail-open).
- Sin website_url (o sin tenant) el CTA cae al login del hub.
"""
import uuid

import httpx
import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.tenant import Tenant
from app.models.user import User, UserRole, UserStatus
from app.schemas.user import StatusUpdate

pytestmark = pytest.mark.asyncio

RESEND_URL = "https://api.resend.com/emails"


# ── Helpers (mismo patrón que test_approval_membership) ──────────


async def seed_user(db_session: AsyncSession, **overrides) -> User:
    defaults = dict(
        username=f"user{uuid.uuid4().hex[:8]}",
        email=f"{uuid.uuid4().hex[:8]}@example.com",
        full_name="Approved User",
        password_hash="$2b$12$hashed_password",
        role=UserRole.NONE,
        status=UserStatus.PENDING,
        is_active=False,
        is_locked=False,
    )
    defaults.update(overrides)
    user = User(**defaults)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def seed_tenant(db_session: AsyncSession, slug: str, **overrides) -> Tenant:
    defaults = dict(id=str(uuid.uuid4()), slug=slug, name=f"Tenant {slug}")
    defaults.update(overrides)
    tenant = Tenant(**defaults)
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


def auth_headers(user: User) -> dict:
    from app.core.security import create_access_token

    return {"Authorization": f"Bearer {create_access_token(subject=str(user.id))}"}


async def set_status(
    client: AsyncClient, admin: User, target: User, new_status: UserStatus
) -> httpx.Response:
    return await client.patch(
        f"/api/v1/users/{target.id}/status",
        json=StatusUpdate(status=new_status).model_dump(),
        headers=auth_headers(admin),
    )


async def seed_admin(db_session: AsyncSession) -> User:
    return await seed_user(
        db_session,
        username=f"admin{uuid.uuid4().hex[:6]}",
        email="admin@example.com",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        is_active=True,
    )


# ── Grabador de HTTP: intercepta solo la llamada a Resend ────────


class ResendRecorder:
    def __init__(self, status_code: int = 200, error: Exception | None = None):
        self.calls: list[dict] = []
        self.status_code = status_code
        self.error = error

    async def handle(self, url: str, **kwargs) -> httpx.Response:
        if url != RESEND_URL:
            raise AssertionError(f"POST inesperado: {url}")
        self.calls.append({"url": url, **kwargs})
        if self.error is not None:
            raise self.error
        return httpx.Response(
            self.status_code,
            json={"id": "email_1"},
            request=httpx.Request("POST", url),
        )

    @property
    def payload(self) -> dict:
        assert self.calls, "no se hizo ninguna llamada a Resend"
        return self.calls[0]["json"]


@pytest.fixture
def resend(monkeypatch):
    """API key presente + post de httpx interceptado."""
    monkeypatch.setattr(settings, "resend_api_key", "re_test_key_123")
    recorder = ResendRecorder()

    async def fake_post(self, url, **kwargs):
        return await recorder.handle(url, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    return recorder


# ── Aprobación → correo con CTA al website_url del tenant ────────


class TestApprovalSendsEmail:
    async def test_approve_sends_email_with_tenant_website_cta(
        self, client: AsyncClient, db_session: AsyncSession, resend: ResendRecorder
    ):
        admin = await seed_admin(db_session)
        await seed_tenant(
            db_session, slug="rincom", name="rincom",
            website_url="https://www.rincom.es",
        )
        target = await seed_user(
            db_session,
            origin="rincom",
            email="elianarinconossa@gmail.com",
            full_name="eliana rincon ossa",
        )

        response = await set_status(client, admin, target, UserStatus.ACTIVE)

        assert response.status_code == status.HTTP_200_OK
        # La aprobación sigue respondiendo igual (regresión del contrato)
        assert response.json()["status"] == UserStatus.ACTIVE.value

        assert len(resend.calls) == 1
        payload = resend.payload
        assert payload["to"] == ["elianarinconossa@gmail.com"]
        assert payload["from"] == settings.emails_from
        # Asunto profesional que nombra la aplicación aprobada
        assert "rincom" in payload["subject"]
        assert "aprobado" in payload["subject"].lower()
        # CTA exacto al sitio de la aplicación solicitada
        assert "https://www.rincom.es" in payload["html"]
        # Personalización con el nombre del usuario
        assert "eliana rincon ossa" in payload["html"]
        # Versión texto plano para clientes sin HTML
        assert "https://www.rincom.es" in payload.get("text", "")

    async def test_reapprove_rejected_user_sends_email(
        self, client: AsyncClient, db_session: AsyncSession, resend: ResendRecorder
    ):
        """Re-aprobar (INACTIVE → ACTIVE, botón Re-aprobar) también envía."""
        admin = await seed_admin(db_session)
        await seed_tenant(
            db_session, slug="riderdefensa", name="Rider Defensa",
            website_url="https://riderdefensa.rincom.es",
        )
        target = await seed_user(
            db_session, origin="riderdefensa", status=UserStatus.INACTIVE,
            email="reaprobada@example.com",
        )

        response = await set_status(client, admin, target, UserStatus.ACTIVE)

        assert response.status_code == status.HTTP_200_OK
        assert len(resend.calls) == 1
        assert resend.payload["to"] == ["reaprobada@example.com"]
        assert "https://riderdefensa.rincom.es" in resend.payload["html"]


# ── No-envíos ─────────────────────────────────────────────────────


class TestApprovalEmailNotSent:
    async def test_reject_does_not_send_email(
        self, client: AsyncClient, db_session: AsyncSession, resend: ResendRecorder
    ):
        admin = await seed_admin(db_session)
        target = await seed_user(db_session, origin="rincom")

        response = await set_status(client, admin, target, UserStatus.INACTIVE)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == UserStatus.INACTIVE.value
        assert resend.calls == []

    async def test_already_active_user_does_not_resend(
        self, client: AsyncClient, db_session: AsyncSession, resend: ResendRecorder
    ):
        admin = await seed_admin(db_session)
        target = await seed_user(
            db_session, origin="rincom", status=UserStatus.ACTIVE, is_active=True
        )

        response = await set_status(client, admin, target, UserStatus.ACTIVE)

        assert response.status_code == status.HTTP_200_OK
        assert resend.calls == []

    async def test_missing_api_key_makes_no_http_call(
        self, client: AsyncClient, db_session: AsyncSession, monkeypatch
    ):
        monkeypatch.setattr(settings, "resend_api_key", None)
        calls: list[str] = []

        async def fake_post(self, url, **kwargs):
            calls.append(url)
            return httpx.Response(
                200, json={}, request=httpx.Request("POST", url)
            )

        monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
        admin = await seed_admin(db_session)
        target = await seed_user(db_session, origin="rincom")

        response = await set_status(client, admin, target, UserStatus.ACTIVE)

        assert response.status_code == status.HTTP_200_OK
        assert calls == []


# ── Fail-open: Resend caído no rompe la aprobación ───────────────


class TestApprovalSurvivesEmailFailure:
    async def test_resend_error_keeps_approval_working(
        self, client: AsyncClient, db_session: AsyncSession, monkeypatch
    ):
        monkeypatch.setattr(settings, "resend_api_key", "re_test_key_123")
        recorder = ResendRecorder(error=httpx.ConnectError("boom"))

        async def fake_post(self, url, **kwargs):
            return await recorder.handle(url, **kwargs)

        monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
        admin = await seed_admin(db_session)
        target = await seed_user(db_session, origin="rincom")

        response = await set_status(client, admin, target, UserStatus.ACTIVE)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == UserStatus.ACTIVE.value
        assert response.json()["is_active"] is True


# ── Fallback del CTA cuando no hay website_url ───────────────────


class TestCtaFallback:
    async def test_tenant_without_website_url_falls_back_to_login(
        self, client: AsyncClient, db_session: AsyncSession, resend: ResendRecorder
    ):
        admin = await seed_admin(db_session)
        await seed_tenant(db_session, slug="rincom", name="rincom")
        target = await seed_user(db_session, origin="rincom")

        response = await set_status(client, admin, target, UserStatus.ACTIVE)

        assert response.status_code == status.HTTP_200_OK
        expected = f"{settings.frontend_origin.rstrip('/')}/login"
        assert expected in resend.payload["html"]

    async def test_unknown_origin_falls_back_to_login(
        self, client: AsyncClient, db_session: AsyncSession, resend: ResendRecorder
    ):
        """origin sin tenant: correo igual, CTA al login del hub (S5-like)."""
        admin = await seed_admin(db_session)
        target = await seed_user(db_session, origin="sitioinexistente")

        response = await set_status(client, admin, target, UserStatus.ACTIVE)

        assert response.status_code == status.HTTP_200_OK
        expected = f"{settings.frontend_origin.rstrip('/')}/login"
        assert expected in resend.payload["html"]
