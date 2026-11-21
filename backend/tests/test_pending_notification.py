"""
Feature pending-request-insight — T2 (S3, S4, S5, S6).

Cubre el aviso por correo a los administradores cuando entra una solicitud de
autorización: destinatarios resueltos por rol, agrupación de una hora,
marcado tras el envío y fail-open.
"""

import uuid
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.main import app
from app.models.user import User
from app.services.email.PendingRequestNotifier import (
    DASHBOARD_PATH,
    NOTIFICATION_WINDOW,
    PendingRequestNotifier,
)
from app.types.enums import UserRole, UserStatus

pytestmark = pytest.mark.asyncio

RESEND_URL = "https://api.resend.com/emails"
T0 = datetime(2026, 3, 12, 9, 0, tzinfo=timezone.utc)


# ── Helpers ─────────────────────────────────────────────────────


async def seed_user(db_session: AsyncSession, **overrides) -> User:
    defaults = dict(
        username=f"user{uuid.uuid4().hex[:8]}",
        email=f"{uuid.uuid4().hex[:8]}@example.com",
        full_name="Pending User",
        password_hash="",
        role=UserRole.NONE,
        status=UserStatus.PENDING,
        is_active=False,
        is_locked=False,
        origin="rincom",
    )
    defaults.update(overrides)
    user = User(**defaults)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def seed_admin(
    db_session: AsyncSession,
    role: UserRole = UserRole.ADMIN,
    is_active: bool = True,
    email: str | None = None,
) -> User:
    return await seed_user(
        db_session,
        username=f"admin{uuid.uuid4().hex[:6]}",
        email=email or f"admin{uuid.uuid4().hex[:6]}@example.com",
        role=role,
        status=UserStatus.ACTIVE if is_active else UserStatus.INACTIVE,
        is_active=is_active,
    )


class ResendRecorder:
    """Intercepta sólo la llamada a Resend y guarda los payloads."""

    def __init__(self, error: Exception | None = None):
        self.calls: list[dict] = []
        self.error = error

    async def handle(self, url: str, **kwargs) -> httpx.Response:
        if url != RESEND_URL:
            raise AssertionError(f"POST inesperado: {url}")
        self.calls.append({"url": url, **kwargs})
        if self.error is not None:
            raise self.error
        return httpx.Response(
            200, json={"id": "email_1"}, request=httpx.Request("POST", url)
        )

    @property
    def last_payload(self) -> dict:
        assert self.calls, "no se hizo ninguna llamada a Resend"
        return self.calls[-1]["json"]

    @property
    def recipients(self) -> list[str]:
        return self.last_payload["to"]


@pytest.fixture
def resend(monkeypatch):
    monkeypatch.setattr(settings, "resend_api_key", "re_test_key_123")

    def _install(error: Exception | None = None) -> ResendRecorder:
        recorder = ResendRecorder(error=error)

        async def fake_post(self, url, **kwargs):
            return await recorder.handle(url, **kwargs)

        monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
        return recorder

    return _install


async def unnotified(db_session: AsyncSession) -> list[User]:
    result = await db_session.execute(
        select(User).where(
            User.status == UserStatus.PENDING,
            User.approval_notified_at.is_(None),
        )
    )
    return list(result.scalars().all())


# ── S3/S5: se envía, y a quién ─────────────────────────────────


class TestPendingNotificationDelivery:
    async def test_first_request_notifies_superadmin_and_admin(
        self, db_session: AsyncSession, resend
    ):
        """S3+S5: SUPERADMIN y ADMIN activos reciben el aviso de la solicitud nueva."""
        superadmin = await seed_admin(
            db_session, role=UserRole.SUPERADMIN, email="super@example.com"
        )
        admin = await seed_admin(db_session, role=UserRole.ADMIN, email="colab@example.com")
        request_user = await seed_user(
            db_session,
            full_name="eliana rincon ossa",
            email="eliana@example.com",
            origin="rincom",
            request_country="ES",
            request_city="Elda",
        )
        recorder = resend()

        sent = await PendingRequestNotifier(db_session).notify_if_due(now=T0)

        assert sent is True
        assert len(recorder.calls) == 1
        assert recorder.recipients == [superadmin.email, admin.email]
        payload = recorder.last_payload
        assert payload["subject"] == "1 solicitud de acceso esperando autorización"
        assert "eliana rincon ossa" in payload["text"]
        assert "eliana@example.com" in payload["text"]
        assert "rincom" in payload["text"]
        assert "Elda, ES" in payload["text"]
        assert f"http://localhost:4321{DASHBOARD_PATH}" in payload["text"]

    async def test_inactive_admin_is_not_a_recipient(
        self, db_session: AsyncSession, resend
    ):
        """S5: `is_active` falso excluye al administrador del aviso."""
        active = await seed_admin(
            db_session, role=UserRole.SUPERADMIN, email="active@example.com"
        )
        await seed_admin(
            db_session, role=UserRole.ADMIN, is_active=False, email="gone@example.com"
        )
        await seed_user(db_session, email="solicitante@example.com")
        recorder = resend()

        assert await PendingRequestNotifier(db_session).notify_if_due(now=T0) is True

        assert recorder.recipients == [active.email]

    async def test_plain_user_is_not_a_recipient(
        self, db_session: AsyncSession, resend
    ):
        """S5: sólo SUPERADMIN/ADMIN reciben el aviso, no cualquier usuario activo."""
        await seed_user(
            db_session,
            email="usuario@example.com",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            is_active=True,
        )
        await seed_user(db_session, email="solicitante@example.com")
        recorder = resend()

        assert await PendingRequestNotifier(db_session).notify_if_due(now=T0) is False
        assert recorder.calls == []

    async def test_active_user_is_never_notified(
        self, db_session: AsyncSession, resend
    ):
        """S3: sólo las solicitudes PENDING entran en el aviso."""
        await seed_admin(db_session, email="admin@example.com")
        await seed_user(
            db_session,
            email="yaactivo@example.com",
            status=UserStatus.ACTIVE,
            is_active=True,
        )
        recorder = resend()

        assert await PendingRequestNotifier(db_session).notify_if_due(now=T0) is False
        assert recorder.calls == []


# ── S4: agrupación por intervalo ───────────────────────────────


class TestNotificationWindow:
    async def test_burst_produces_a_single_email_listing_every_request(
        self, db_session: AsyncSession, resend
    ):
        """S4: N solicitudes dentro de la ventana → un solo correo con todas."""
        await seed_admin(db_session, email="admin@example.com")
        for i in range(3):
            await seed_user(
                db_session, full_name=f"Solicitante {i}", email=f"s{i}@example.com"
            )
        recorder = resend()

        assert await PendingRequestNotifier(db_session).notify_if_due(now=T0) is True

        assert len(recorder.calls) == 1
        payload = recorder.last_payload
        assert payload["subject"] == "3 solicitudes de acceso esperando autorización"
        for i in range(3):
            assert f"s{i}@example.com" in payload["text"]

    async def test_request_inside_the_window_waits_and_then_goes_alone(
        self, db_session: AsyncSession, resend
    ):
        """S4: dentro de la hora no se envía; al abrirse la ventana se envía sólo lo pendiente."""
        await seed_admin(db_session, email="admin@example.com")
        first = await seed_user(db_session, email="primero@example.com")
        recorder = resend()
        notifier = PendingRequestNotifier(db_session)

        assert await notifier.notify_if_due(now=T0) is True

        second = await seed_user(db_session, email="segundo@example.com")

        # Dentro de la ventana: no hay correo nuevo.
        assert await notifier.notify_if_due(now=T0 + timedelta(minutes=30)) is False
        assert len(recorder.calls) == 1

        # Pasada la hora: un único correo con la solicitud que faltaba.
        after_window = T0 + NOTIFICATION_WINDOW + timedelta(minutes=1)
        assert await notifier.notify_if_due(now=after_window) is True
        assert len(recorder.calls) == 2
        payload = recorder.last_payload
        assert "segundo@example.com" in payload["text"]
        assert "primero@example.com" not in payload["text"]
        assert payload["subject"] == "1 solicitud de acceso esperando autorización"

    async def test_requests_are_marked_only_after_the_email_is_accepted(
        self, db_session: AsyncSession, resend
    ):
        """S4: la marca `approval_notified_at` se escribe con el envío exitoso."""
        await seed_admin(db_session, email="admin@example.com")
        request_user = await seed_user(db_session, email="marca@example.com")
        resend()

        assert await PendingRequestNotifier(db_session).notify_if_due(now=T0) is True

        refreshed = await db_session.get(User, request_user.id)
        await db_session.refresh(refreshed)
        assert refreshed.approval_notified_at is not None
        assert refreshed.approval_notified_at.replace(tzinfo=timezone.utc) == T0


# ── S6: fail-open ──────────────────────────────────────────────


class TestNotificationFailOpen:
    async def test_resend_failure_keeps_requests_unnotified_for_retry(
        self, db_session: AsyncSession, resend
    ):
        """S6: si Resend falla, no hay marca y la solicitud se reintenta."""
        await seed_admin(db_session, email="admin@example.com")
        await seed_user(db_session, email="fallo@example.com")
        resend(error=httpx.ConnectError("resend caído"))

        sent = await PendingRequestNotifier(db_session).notify_if_due(now=T0)

        assert sent is False
        assert len(await unnotified(db_session)) == 1

    async def test_missing_api_key_skips_send_and_keeps_request_pending(
        self, db_session: AsyncSession, monkeypatch
    ):
        """S6: sin RESEND_API_KEY no se envía ni se marca nada."""
        monkeypatch.setattr(settings, "resend_api_key", None)
        await seed_admin(db_session, email="admin@example.com")
        await seed_user(db_session, email="sinkey@example.com")

        assert await PendingRequestNotifier(db_session).notify_if_due(now=T0) is False
        assert len(await unnotified(db_session)) == 1

    async def test_no_recipients_keeps_request_unnotified(
        self, db_session: AsyncSession, resend
    ):
        """S6: sin administradores no se pierde el aviso, se reintenta después."""
        await seed_user(db_session, email="huerfano@example.com")
        recorder = resend()

        assert await PendingRequestNotifier(db_session).notify_if_due(now=T0) is False
        assert recorder.calls == []
        assert len(await unnotified(db_session)) == 1


# ── S6: el endpoint nunca falla por el aviso ───────────────────


class StubAuthService:
    """AuthService que siempre responde PENDING_APPROVAL."""

    def __init__(self, exc: Exception | None = None):
        self.exc = exc

    async def process_google_login(self, **kwargs):
        raise self.exc or HTTPException(status_code=403, detail="PENDING_APPROVAL")


class RecordingNotifier:
    def __init__(self, exc: Exception | None = None):
        self.exc = exc
        self.calls = 0

    async def notify_if_due(self, now=None) -> bool:
        self.calls += 1
        if self.exc:
            raise self.exc
        return True


class TestCallbackTriggersNotice:
    async def test_pending_callback_triggers_the_notice(
        self, client: AsyncClient
    ):
        """S3: el pendiente dispara el aviso, y el solicitante ve status=pending."""
        from app.api.v1.dependencies import (
            get_auth_service,
            get_pending_request_notifier,
        )

        notifier = RecordingNotifier()
        app.dependency_overrides[get_auth_service] = lambda: StubAuthService()
        app.dependency_overrides[get_pending_request_notifier] = lambda: notifier
        try:
            response = await client.get("/api/v1/auth/callback?code=abc")
        finally:
            app.dependency_overrides.pop(get_auth_service, None)
            app.dependency_overrides.pop(get_pending_request_notifier, None)

        assert notifier.calls == 1
        assert "status=pending" in response.headers["location"]

    async def test_notifier_failure_does_not_change_the_pending_response(
        self, client: AsyncClient
    ):
        """S6: un aviso que explota no cambia la respuesta al solicitante."""
        from app.api.v1.dependencies import (
            get_auth_service,
            get_pending_request_notifier,
        )

        notifier = RecordingNotifier(exc=RuntimeError("aviso roto"))
        app.dependency_overrides[get_auth_service] = lambda: StubAuthService()
        app.dependency_overrides[get_pending_request_notifier] = lambda: notifier
        try:
            response = await client.get("/api/v1/auth/callback?code=abc")
        finally:
            app.dependency_overrides.pop(get_auth_service, None)
            app.dependency_overrides.pop(get_pending_request_notifier, None)

        assert notifier.calls == 1
        assert "status=pending" in response.headers["location"]
