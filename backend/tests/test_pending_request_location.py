"""
Feature pending-request-insight — T1 (S1, S2).

Cubre la captura de la ubicación de la solicitud desde las cabeceras del CDN,
su persistencia al crear el usuario PENDING, la exposición del dato en
`GET /users/pending` y la idempotencia de la migración de columnas.
"""

import uuid

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.geo import RequestLocation, extract_request_location
from app.db.migrations import apply_idempotent_migrations
from app.models.user import User
from app.repositories.UserRepository import UserRepository
from app.services.auth.AuthService import AuthService
from app.types.enums import UserRole, UserStatus

pytestmark = pytest.mark.asyncio


# ── Helpers (mismo patrón que test_approval_email) ──────────────


class FakeHeaders(dict):
    """`request.headers` case-insensitive como Starlette."""

    def get(self, key, default=None):
        for name, value in self.items():
            if name.lower() == key.lower():
                return value
        return default


class FakeRequest:
    def __init__(self, headers: dict, client_ip: str = "203.0.113.7"):
        self.headers = FakeHeaders(headers)
        self.client = type("Client", (), {"host": client_ip})()


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
    )
    defaults.update(overrides)
    user = User(**defaults)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def auth_headers(user: User) -> dict:
    from app.core.security import create_access_token

    return {"Authorization": f"Bearer {create_access_token(subject=str(user.id))}"}


class FakeOAuthService:
    """Devuelve siempre el mismo userinfo de Google."""

    def __init__(self, email: str, name: str = "Google User"):
        self.email = email
        self.name = name

    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        return {"email": self.email, "name": self.name}


# ── S2: lectura de cabeceras ────────────────────────────────────


class TestGeoHeaders:
    async def test_cloudflare_headers_fill_country_city_region_and_ip(self):
        """Cabeceras de Cloudflare → país normalizado a ISO mayúsculas, ciudad y región."""
        request = FakeRequest(
            {
                "CF-IPCountry": "es",
                "CF-IPCity": "Elda",
                "CF-Region": "Valencia",
                "X-Forwarded-For": "1.2.3.4, 10.0.0.1",
            }
        )

        location = extract_request_location(request)

        assert location.country == "ES"
        assert location.city == "Elda"
        assert location.region == "Valencia"
        assert location.ip == "1.2.3.4"

    async def test_cloudflare_url_encoded_city_is_decoded(self):
        """Cloudflare url-encodea CF-IPCity: se guarda el nombre real, no el escape."""
        request = FakeRequest({"CF-IPCity": "Sant%20Vicen%C3%A7%20dels%20Horts"})

        location = extract_request_location(request)

        assert location.city == "Sant Vicenç dels Horts"

    async def test_unknown_country_codes_are_not_persisted(self):
        """'XX' (desconocido) y 'T1' (Tor) no son países: no se guarda el dato."""
        for code in ("XX", "T1"):
            location = extract_request_location(FakeRequest({"CF-IPCountry": code}))
            assert location.country is None

    async def test_country_only_when_city_headers_are_disabled(self):
        """Con sólo CF-IPCountry (sin la Managed Transform de ciudad) se cumple 'por lo menos el país'."""
        location = extract_request_location(FakeRequest({"CF-IPCountry": "AR"}))

        assert location.country == "AR"
        assert location.city is None
        assert location.region is None

    async def test_vercel_headers_are_used_as_fallback(self):
        """Sin cabeceras de Cloudflare se aceptan las de Vercel."""
        location = extract_request_location(
            FakeRequest(
                {"X-Vercel-IP-Country": "fr", "X-Vercel-IP-City": "Paris"}
            )
        )

        assert location.country == "FR"
        assert location.city == "Paris"

    async def test_cloudflare_wins_over_vercel(self):
        """Si vienen las dos familias, gana Cloudflare (el CDN real del deploy)."""
        location = extract_request_location(
            FakeRequest({"CF-IPCountry": "ES", "X-Vercel-IP-Country": "US"})
        )

        assert location.country == "ES"

    async def test_no_headers_leaves_every_field_empty(self):
        """Sin cabeceras de CDN no se inventa ubicación: todo None."""
        location = extract_request_location(FakeRequest({}))

        assert location == RequestLocation(ip="203.0.113.7")

    async def test_missing_request_returns_empty_location(self):
        """Un llamador interno sin petición HTTP no revienta."""
        assert extract_request_location(None) == RequestLocation()

    async def test_city_is_truncated_to_column_length(self):
        """La ciudad nunca excede VARCHAR(128) de la columna."""
        location = extract_request_location(FakeRequest({"CF-IPCity": "x" * 300}))

        assert location.city is not None
        assert len(location.city) == 128

    async def test_as_user_fields_maps_every_persisted_column(self):
        """El mapeo a columnas de `users` usa los nombres del modelo."""
        location = RequestLocation(
            ip="1.2.3.4", country="ES", city="Elda", region="Valencia"
        )

        assert location.as_user_fields() == {
            "last_ip": "1.2.3.4",
            "request_country": "ES",
            "request_city": "Elda",
            "request_region": "Valencia",
        }


# ── S2: persistencia al crear el pendiente ──────────────────────


class TestPendingRequestPersistence:
    async def _service(self, db_session: AsyncSession, email: str) -> AuthService:
        return AuthService(
            token_service=None,
            oauth_service=FakeOAuthService(email),
            user_repository=UserRepository(db_session),
        )

    async def test_new_pending_user_persists_request_location(
        self, db_session: AsyncSession
    ):
        """Solicitud nueva con cabeceras → país, ciudad, región e IP quedan guardados."""
        email = f"{uuid.uuid4().hex[:8]}@example.com"
        service = await self._service(db_session, email)
        location = RequestLocation(
            ip="198.51.100.9", country="ES", city="Elda", region="Valencia"
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.process_google_login(
                "auth-code", "https://api/callback", location=location
            )

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "PENDING_APPROVAL"

        stored = (
            await db_session.execute(select(User).where(User.email == email))
        ).scalar_one()
        assert stored.status == UserStatus.PENDING
        assert stored.request_country == "ES"
        assert stored.request_city == "Elda"
        assert stored.request_region == "Valencia"
        assert stored.last_ip == "198.51.100.9"

    async def test_new_pending_user_without_location_still_created(
        self, db_session: AsyncSession
    ):
        """Sin cabeceras (o llamador interno) el pendiente se crea igual con ubicación NULL."""
        email = f"{uuid.uuid4().hex[:8]}@example.com"
        service = await self._service(db_session, email)

        with pytest.raises(HTTPException) as exc_info:
            await service.process_google_login("auth-code", "https://api/callback")

        assert exc_info.value.detail == "PENDING_APPROVAL"
        stored = (
            await db_session.execute(select(User).where(User.email == email))
        ).scalar_one()
        assert stored.request_country is None
        assert stored.request_city is None
        assert stored.last_ip is None


# ── S1/S2: el dato llega al dashboard ──────────────────────────


class TestPendingEndpointExposesLocation:
    async def test_pending_response_has_created_at_and_request_location(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """GET /users/pending devuelve created_at (S1) y la ubicación guardada (S2)."""
        admin = await seed_user(
            db_session,
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_active=True,
        )
        pending = await seed_user(
            db_session,
            username="pendinggeo",
            email="pendinggeo@example.com",
            request_country="AR",
            request_city="Rosario",
            request_region="Santa Fe",
        )

        response = await client.get(
            "/api/v1/users/pending", headers=auth_headers(admin)
        )

        assert response.status_code == 200
        item = next(u for u in response.json() if u["id"] == pending.id)
        assert item["created_at"] is not None
        assert item["request_country"] == "AR"
        assert item["request_city"] == "Rosario"
        assert item["request_region"] == "Santa Fe"


# ── Migración idempotente ──────────────────────────────────────


class TestIdempotentMigrations:
    async def test_apply_adds_missing_column_and_is_idempotent(
        self, db_session: AsyncSession
    ):
        """Agrega la columna que falta y una segunda ejecución no hace nada."""
        await db_session.execute(text("ALTER TABLE users DROP COLUMN request_country"))
        await db_session.commit()

        conn = await db_session.connection()
        added = await apply_idempotent_migrations(conn)
        assert added == ["request_country"]

        added_again = await apply_idempotent_migrations(conn)
        assert added_again == []

    async def test_apply_is_noop_when_every_column_exists(
        self, db_session: AsyncSession
    ):
        """Sobre una tabla completa (create_all ya creó todo) no hay cambios."""
        conn = await db_session.connection()

        assert await apply_idempotent_migrations(conn) == []
