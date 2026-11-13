"""
Tests para las sesiones persistentes: POST /auth/sessions, POST /auth/refresh,
GET/DELETE /auth/sessions y la enforcement de `sid` en data-token/select-tenant.

Feature: odd/tasks/persistent-mobile-session.md (S4, S5, S8, S9 + API contract).
Patrones de fixtures/estilo derivados de tests/test_data_token.py — ese archivo
NO se modifica.
"""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import status
from jose import jwt
from sqlalchemy import select

from app.core.config import settings
from app.core.crypto import get_public_key
from app.core.security import get_password_hash
from app.models.tenant import Tenant
from app.models.user import User, UserRole, UserStatus
from app.models.user_session import UserSession
from app.services.auth.TokenService import TokenService

pytestmark = pytest.mark.asyncio

SESSIONS_URL = "/api/v1/auth/sessions"
REFRESH_URL = "/api/v1/auth/refresh"
REFRESH_EXPIRE_SECONDS = 7776000  # 90 días (contract)


# ── Helpers ─────────────────────────────────────────────────────


async def _create_user(db_session, *, username: str = "sessuser") -> User:
    user = User(
        username=username,
        email=f"{username}@test.com",
        full_name="Session User",
        password_hash=get_password_hash("testpass"),
        role=UserRole.SUPERADMIN,
        status=UserStatus.ACTIVE,
        is_active=True,
        is_locked=False,
        tenant_id=None,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _hub_token(
    user: User, *, sid: str | None = None, tenant: Tenant | None = None
) -> str:
    """Hub JWT con la misma forma que /login o /select-tenant (RS256)."""
    token_service = TokenService()
    data: dict[str, object] = {
        "sub": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role.value,
        "type": "access",
    }
    if sid is not None:
        data["sid"] = sid
    if tenant is not None:
        data["tenant"] = {"id": tenant.id, "slug": tenant.slug, "name": tenant.name}
    token, _ = await token_service.create_access_token(data)
    return token


def _decode(token: str) -> dict:
    return jwt.decode(
        token,
        get_public_key(),
        algorithms=[settings.algorithm],
        audience=settings.jwt_audience,
    )


async def _create_session(client, user: User, *, sid: str | None = None) -> dict:
    """POST /auth/sessions y devuelve el JSON de la respuesta."""
    hub = await _hub_token(user, sid=sid)
    response = await client.post(
        SESSIONS_URL,
        headers={"Authorization": f"Bearer {hub}", "User-Agent": "TestAgent/1.0"},
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    return response.json()


async def _refresh(client, refresh_token: str):
    return await client.post(REFRESH_URL, json={"refresh_token": refresh_token})


async def _get_row_by_hash(db_session, refresh_token: str) -> UserSession | None:
    digest = hashlib.sha256(refresh_token.encode()).hexdigest()
    result = await db_session.execute(
        select(UserSession).where(UserSession.refresh_token_hash == digest)
    )
    return result.scalar_one_or_none()


# ── Tests ───────────────────────────────────────────────────────


class TestCreateSession:
    async def test_contract_response_and_hashed_storage(self, client, db_session):
        """200 → {session_id, refresh_token, refresh_expires_in}; solo el HASH en BD."""
        user = await _create_user(db_session)
        data = await _create_session(client, user)

        assert set(data.keys()) == {"session_id", "refresh_token", "refresh_expires_in"}
        assert uuid.UUID(data["session_id"])  # uuid válido
        assert (
            isinstance(data["refresh_token"], str) and len(data["refresh_token"]) >= 32
        )
        assert data["refresh_expires_in"] == REFRESH_EXPIRE_SECONDS

        uuid.UUID(data["session_id"])  # noqa: F841 — claridad
        row = await db_session.get(UserSession, data["session_id"])
        assert row is not None
        assert row.user_id == user.id
        assert row.revoked_at is None
        # Nunca el token en claro
        assert (
            row.refresh_token_hash
            == hashlib.sha256(data["refresh_token"].encode()).hexdigest()
        )
        assert data["refresh_token"] not in row.refresh_token_hash
        assert row.user_agent == "TestAgent/1.0"

    async def test_requires_authorization(self, client):
        """Sin cabecera Authorization → 401."""
        response = await client.post(SESSIONS_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestListSessions:
    async def test_lists_own_active_sessions_with_current_flag(
        self, client, db_session
    ):
        """GET → solo sesiones propias vigentes; `current` marca la del sid."""
        user = await _create_user(db_session, username="lista")
        other = await _create_user(db_session, username="otro")
        s1 = await _create_session(client, user)
        s2 = await _create_session(client, user)
        await _create_session(client, other)  # ajena, no debe aparecer

        hub = await _hub_token(user, sid=s1["session_id"])
        response = await client.get(
            SESSIONS_URL, headers={"Authorization": f"Bearer {hub}"}
        )
        assert response.status_code == status.HTTP_200_OK
        items = response.json()

        assert len(items) == 2
        ids = {item["id"] for item in items}
        assert ids == {s1["session_id"], s2["session_id"]}
        by_id = {item["id"]: item for item in items}
        for item in items:
            assert set(item.keys()) == {
                "id",
                "created_at",
                "last_seen_at",
                "user_agent",
                "current",
            }
            assert item["user_agent"] == "TestAgent/1.0"
        assert by_id[s1["session_id"]]["current"] is True
        assert by_id[s2["session_id"]]["current"] is False

    async def test_revoked_and_expired_sessions_are_excluded(self, client, db_session):
        """Revocada o expirada → no se lista."""
        user = await _create_user(db_session, username="excluye")
        s1 = await _create_session(client, user)
        s2 = await _create_session(client, user)

        # Revocar s1 vía DELETE
        hub = await _hub_token(user, sid=s1["session_id"])
        delete = await client.delete(
            f"{SESSIONS_URL}/{s1['session_id']}",
            headers={"Authorization": f"Bearer {hub}"},
        )
        assert delete.status_code == status.HTTP_204_NO_CONTENT

        # Expirar s2 directamente en BD
        row2 = await db_session.get(UserSession, s2["session_id"])
        row2.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db_session.add(row2)
        await db_session.commit()

        response = await client.get(
            SESSIONS_URL, headers={"Authorization": f"Bearer {hub}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    async def test_requires_authorization(self, client):
        response = await client.get(SESSIONS_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRevoke:
    async def test_delete_own_session_204(self, client, db_session):
        """DELETE /sessions/{id} propia → 204 y la fila queda revocada."""
        user = await _create_user(db_session, username="revoca")
        s1 = await _create_session(client, user)
        hub = await _hub_token(user, sid=s1["session_id"])

        response = await client.delete(
            f"{SESSIONS_URL}/{s1['session_id']}",
            headers={"Authorization": f"Bearer {hub}"},
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

        row = await db_session.get(UserSession, s1["session_id"])
        assert row.revoked_at is not None

    async def test_delete_other_users_session_404(self, client, db_session):
        """Sesión de otro usuario → 404 (no se filtra existencia)."""
        user = await _create_user(db_session, username="propia")
        victim = await _create_user(db_session, username="victima")
        victim_session = await _create_session(client, victim)
        hub = await _hub_token(user)

        response = await client.delete(
            f"{SESSIONS_URL}/{victim_session['session_id']}",
            headers={"Authorization": f"Bearer {hub}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

        row = await db_session.get(UserSession, victim_session["session_id"])
        assert row.revoked_at is None  # intacta

    async def test_delete_missing_session_404(self, client, db_session):
        user = await _create_user(db_session, username="faltante")
        hub = await _hub_token(user)
        response = await client.delete(
            f"{SESSIONS_URL}/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {hub}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_all_except_current(self, client, db_session):
        """DELETE /sessions con sid ⇒ revoca todas MENOS la actual; {revoked: n}."""
        user = await _create_user(db_session, username="todas")
        current = await _create_session(client, user)
        await _create_session(client, user)
        await _create_session(client, user)

        hub = await _hub_token(user, sid=current["session_id"])
        response = await client.delete(
            SESSIONS_URL, headers={"Authorization": f"Bearer {hub}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"revoked": 2}

        current_row = await db_session.get(UserSession, current["session_id"])
        assert current_row.revoked_at is None
        others = (
            (
                await db_session.execute(
                    select(UserSession).where(
                        UserSession.user_id == user.id,
                        UserSession.id != current["session_id"],
                    )
                )
            )
            .scalars()
            .all()
        )
        assert others and all(row.revoked_at is not None for row in others)

    async def test_delete_all_without_sid_revokes_everything(self, client, db_session):
        """Hub sin sid ⇒ revoca todas las del usuario."""
        user = await _create_user(db_session, username="sin-sid")
        await _create_session(client, user)
        await _create_session(client, user)

        hub = await _hub_token(user)  # sin sid
        response = await client.delete(
            SESSIONS_URL, headers={"Authorization": f"Bearer {hub}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"revoked": 2}
