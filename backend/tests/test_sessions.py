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
from app.models.user_tenant import UserTenant
from app.services.auth.TokenService import TokenService

pytestmark = pytest.mark.asyncio

SESSIONS_URL = "/api/v1/auth/sessions"
REFRESH_URL = "/api/v1/auth/refresh"
DATA_TOKEN_URL = "/api/v1/auth/data-token"
SELECT_TENANT_URL = "/api/v1/users/select-tenant"
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


async def _hub_token(user: User, *, sid: str | None = None, tenant: Tenant | None = None) -> str:
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
        select(UserSession).where(
            UserSession.refresh_token_hash == digest
        )
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
        assert isinstance(data["refresh_token"], str) and len(data["refresh_token"]) >= 32
        assert data["refresh_expires_in"] == REFRESH_EXPIRE_SECONDS

        uuid.UUID(data["session_id"])  # noqa: F841 — claridad
        row = await db_session.get(UserSession, data["session_id"])
        assert row is not None
        assert row.user_id == user.id
        assert row.revoked_at is None
        # Nunca el token en claro
        assert row.refresh_token_hash == hashlib.sha256(
            data["refresh_token"].encode()
        ).hexdigest()
        assert data["refresh_token"] not in row.refresh_token_hash
        assert row.user_agent == "TestAgent/1.0"

    async def test_requires_authorization(self, client):
        """Sin cabecera Authorization → 401."""
        response = await client.post(SESSIONS_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRefresh:
    async def test_rotation_returns_new_pair_and_sid_claim(self, client, db_session):
        """Rotación: nuevo refresh, hub nuevo con claim sid, fila vieja revocada."""
        user = await _create_user(db_session, username="rotate")
        first = await _create_session(client, user)

        response = await _refresh(client, first["refresh_token"])
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()

        assert set(data.keys()) == {
            "access_token", "expires_in", "refresh_token", "refresh_expires_in",
        }
        assert "token_type" not in data  # contract: solo los 4 campos
        assert data["refresh_token"] != first["refresh_token"]
        assert data["refresh_expires_in"] == REFRESH_EXPIRE_SECONDS
        assert 7100 <= data["expires_in"] <= 7200  # TTL del hub intacto (S5)

        claims = _decode(data["access_token"])
        assert claims["sub"] == str(user.id)
        assert claims["type"] == "access"
        assert "sid" in claims  # el hub nuevo pertenece a la sesión rotada

        old_row = await _get_row_by_hash(db_session, first["refresh_token"])
        new_row = await _get_row_by_hash(db_session, data["refresh_token"])
        assert old_row is not None and old_row.revoked_at is not None
        assert new_row is not None and new_row.revoked_at is None
        assert new_row.id == claims["sid"]  # sid = id de la sesión vigente
        # Misma familia y misma expiración (90 d desde el primer login, S4/S10)
        assert new_row.family_id == old_row.family_id
        assert new_row.expires_at == old_row.expires_at

    async def test_unknown_token_401(self, client, db_session):
        """Refresh inventado → 401."""
        await _create_user(db_session, username="unknown")
        response = await _refresh(client, "not-a-real-token")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_expired_session_401(self, client, db_session):
        """Sesión con expires_at en el pasado → 401."""
        user = await _create_user(db_session, username="expira")
        created = await _create_session(client, user)
        row = await _get_row_by_hash(db_session, created["refresh_token"])
        row.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        db_session.add(row)
        await db_session.commit()

        response = await _refresh(client, created["refresh_token"])
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_reuse_of_revoked_token_401_and_revokes_family(
        self, client, db_session
    ):
        """S8: presentar un refresh ya rotado ⇒ 401 y la sesión entera (familia)
        queda revocada, incluido el sucesor vigente."""
        user = await _create_user(db_session, username="reuse")
        first = await _create_session(client, user)

        rotated = await _refresh(client, first["refresh_token"])
        assert rotated.status_code == status.HTTP_200_OK
        successor_token = rotated.json()["refresh_token"]

        # Reintento con el token viejo (rotado → revocado)
        reuse = await _refresh(client, first["refresh_token"])
        assert reuse.status_code == status.HTTP_401_UNAUTHORIZED

        # El sucesor vigente también quedó revocado por la reuse detection
        successor = await _refresh(client, successor_token)
        assert successor.status_code == status.HTTP_401_UNAUTHORIZED

        successor_row = await _get_row_by_hash(db_session, successor_token)
        assert successor_row is not None and successor_row.revoked_at is not None

    async def test_inactive_user_401(self, client, db_session):
        """Usuario desactivado → 401 aunque el refresh sea bueno."""
        user = await _create_user(db_session, username="inactivo")
        created = await _create_session(client, user)
        user.is_active = False
        db_session.add(user)
        await db_session.commit()

        response = await _refresh(client, created["refresh_token"])
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
                "id", "created_at", "last_seen_at", "user_agent", "current",
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
            await db_session.execute(
                select(UserSession).where(
                    UserSession.user_id == user.id,
                    UserSession.id != current["session_id"],
                )
            )
        ).scalars().all()
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


class TestDataTokenSidEnforcement:
    async def test_revoked_session_yields_401(self, client, db_session):
        """S9: hub con sid de sesión revocada → 401 en data-token."""
        user = await _create_user(db_session, username="muerta")
        created = await _create_session(client, user)
        rotated = await _refresh(client, created["refresh_token"])
        assert rotated.status_code == status.HTTP_200_OK
        live_hub = rotated.json()["access_token"]  # sid de la sesión rotada

        # Revocar la sesión entera (la del sid del hub vigente)
        row = await _get_row_by_hash(
            db_session, rotated.json()["refresh_token"]
        )
        row.revoked_at = datetime.now(timezone.utc)
        db_session.add(row)
        await db_session.commit()

        response = await client.post(
            DATA_TOKEN_URL, headers={"Authorization": f"Bearer {live_hub}"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_live_session_passes_and_data_token_carries_sid(
        self, client, db_session
    ):
        """S9: sid vigente → 200 y el data token hereda el claim sid."""
        user = await _create_user(db_session, username="viva")
        created = await _create_session(client, user)
        rotated = await _refresh(client, created["refresh_token"])
        live_hub = rotated.json()["access_token"]

        response = await client.post(
            DATA_TOKEN_URL, headers={"Authorization": f"Bearer {live_hub}"}
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        claims = _decode(response.json()["access_token"])
        row = await _get_row_by_hash(db_session, rotated.json()["refresh_token"])
        assert claims["sid"] == row.id

    async def test_hub_without_sid_is_unaffected(self, client, db_session):
        """S5: hub sin sid (otros spokes) → pasa sin chequeo, como antes."""
        user = await _create_user(db_session, username="legado")
        hub = await _hub_token(user)
        response = await client.post(
            DATA_TOKEN_URL, headers={"Authorization": f"Bearer {hub}"}
        )
        assert response.status_code == status.HTTP_200_OK
        claims = _decode(response.json()["access_token"])
        assert "sid" not in claims


class TestSelectTenantCopiesSid:
    async def test_select_tenant_preserves_sid(self, client, db_session):
        """S9: select-tenant re-mintea el hub conservando el sid de la sesión."""
        tenant = Tenant(id=str(uuid.uuid4()), slug="riderdefensa", name="Rider")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        user = await _create_user(db_session, username="cambia")
        membership = UserTenant(
            id=str(uuid.uuid4()), user_id=user.id, tenant_id=tenant.id, role="ADMIN"
        )
        db_session.add(membership)
        await db_session.commit()

        created = await _create_session(client, user)
        rotated = await _refresh(client, created["refresh_token"])
        live_hub = rotated.json()["access_token"]
        sid = _decode(live_hub)["sid"]

        response = await client.post(
            SELECT_TENANT_URL,
            json={"tenant_id": tenant.id},
            headers={"Authorization": f"Bearer {live_hub}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        claims = _decode(response.json()["access_token"])
        assert claims["sid"] == sid  # copiado, no perdido
        assert claims["tenant"]["id"] == tenant.id
