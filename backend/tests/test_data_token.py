"""
Tests para POST /api/v1/auth/data-token (data token con scope Supabase).

Contexto: el hub JWT lleva `role` = rol de aplicación (p.ej. SUPERADMIN) y
PostgREST interpreta ese claim como ROL DE POSTGRES, por lo que lo rechaza con
`42501 role ... does not exist`. Este endpoint debe emitir un segundo token
con `role: "authenticated"`, `type: "data"` y SIN datos de identidad (el spoke
ya tiene el hub JWT y este token se guarda en el navegador).

Patrones de fixtures/estilo derivados de tests/conftest.py y
tests/test_auth_endpoints.py — ese archivo NO se modifica.
"""
import base64
import uuid
from datetime import timedelta

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import status
from jose import jwt

from app.core.config import settings
from app.core.crypto import get_public_key
from app.core.security import create_access_token, get_password_hash
from app.models.tenant import Tenant
from app.models.user import User, UserRole, UserStatus
from app.services.auth.TokenService import TokenService

pytestmark = pytest.mark.asyncio

DATA_TOKEN_URL = "/api/v1/auth/data-token"
# Roles de aplicación que NUNCA deben aparecer en el data token
APP_ROLES = {role.value for role in UserRole}


# ── Helpers ─────────────────────────────────────────────────────

async def _create_tenant(db_session, slug: str = "spoke") -> Tenant:
    """Crea un tenant de prueba y lo persiste."""
    tenant = Tenant(id=str(uuid.uuid4()), slug=slug, name="Spoke Tenant")
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


async def _create_user(
    db_session,
    *,
    role: UserRole = UserRole.SUPERADMIN,
    tenant_id: str | None = None,
    username: str = "datauser",
) -> User:
    """Crea un usuario activo (opcionalmente con tenant) y lo persiste."""
    user = User(
        username=username,
        email=f"{username}@test.com",
        full_name="Data User",
        password_hash=get_password_hash("testpass"),
        role=role,
        status=UserStatus.ACTIVE,
        is_active=True,
        is_locked=False,
        tenant_id=tenant_id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _hub_token(user: User, *, tenant: Tenant | None = None) -> str:
    """Mintea un hub JWT con la MISMA forma que /login (TokenService, RS256)."""
    token_service = TokenService()
    data: dict[str, object] = {
        "sub": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role.value,
        "type": "access",
    }
    if tenant is not None:
        data["tenant"] = {
            "id": tenant.id,
            "slug": tenant.slug,
            "name": tenant.name,
        }
    token, _ = await token_service.create_access_token(data)
    return token


def _decode(token: str) -> dict:
    """Decodifica y verifica un JWT con la clave pública del hub."""
    return jwt.decode(token, get_public_key(), algorithms=[settings.algorithm])


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


async def _mint_data_token(client, user: User, *, tenant: Tenant | None = None) -> dict:
    """POST al endpoint con un hub JWT válido y devuelve el JSON de la respuesta."""
    hub = await _hub_token(user, tenant=tenant)
    response = await client.post(
        DATA_TOKEN_URL, headers={"Authorization": f"Bearer {hub}"}
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    return response.json()


# ── Tests ───────────────────────────────────────────────────────

class TestDataToken:
    """POST /api/v1/auth/data-token"""

    async def test_success_returns_exactly_three_fields(
        self, client, db_session
    ):
        """200 → solo access_token, token_type y expires_in (900s por defecto)."""
        user = await _create_user(db_session)
        data = await _mint_data_token(client, user)

        assert set(data.keys()) == {"access_token", "token_type", "expires_in"}
        assert data["token_type"] == "bearer"
        assert isinstance(data["expires_in"], int)
        # Vida por defecto: 900 segundos (DATA_TOKEN_EXPIRE_SECONDS)
        assert 895 <= data["expires_in"] <= 900

    async def test_claims_role_type_sub_and_tenant(
        self, client, db_session
    ):
        """Claims: role=authenticated, type=data, sub=user.id, tenant preservado."""
        tenant = await _create_tenant(db_session)
        user = await _create_user(db_session, tenant_id=tenant.id)
        data = await _mint_data_token(client, user, tenant=tenant)

        claims = _decode(data["access_token"])
        assert claims["role"] == "authenticated"
        assert claims["type"] == "data"
        assert claims["sub"] == str(user.id)
        # El mismo objeto {id, slug, name} que lleva el hub token
        assert claims["tenant"] == {
            "id": tenant.id,
            "slug": tenant.slug,
            "name": tenant.name,
        }
        # exp / iat / jti los pone TokenService
        assert isinstance(claims["exp"], int)
        assert isinstance(claims["iat"], int)
        assert claims["jti"]
        assert claims["exp"] - claims["iat"] == pytest.approx(900, abs=5)

    async def test_app_role_does_not_leak(self, client, db_session):
        """El rol de la aplicación (SUPERADMIN/ADMIN/...) NO se emite."""
        user = await _create_user(db_session, role=UserRole.SUPERADMIN)
        assert user.role.value in APP_ROLES  # el usuario SÍ es SUPERADMIN

        data = await _mint_data_token(client, user)
        claims = _decode(data["access_token"])

        assert claims["role"] == "authenticated"
        assert claims["role"] not in APP_ROLES
        assert claims["role"] != user.role.value

    async def test_no_identity_claims(self, client, db_session):
        """Sin email/username/company_name/modules: identidad la da el hub JWT."""
        tenant = await _create_tenant(db_session, slug="sin-identidad")
        user = await _create_user(
            db_session, tenant_id=tenant.id, username="sinidentidad"
        )
        data = await _mint_data_token(client, user, tenant=tenant)
        claims = _decode(data["access_token"])

        for leaked in ("email", "username", "company_name", "modules", "full_name"):
            assert leaked not in claims, f"claim '{leaked}' no debe viajar"

    async def test_tenant_omitted_when_user_has_none(self, client, db_session):
        """Usuario sin tenant → el claim tenant se OMITE (no se inventa)."""
        user = await _create_user(db_session, username="sin-tenant")
        assert user.tenant_id is None

        data = await _mint_data_token(client, user)
        claims = _decode(data["access_token"])

        assert "tenant" not in claims

    async def test_missing_authorization_header(self, client):
        """Sin cabecera Authorization → 401 (formato de error estándar del repo)."""
        response = await client.post(DATA_TOKEN_URL)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    async def test_garbage_token_is_rejected(self, client, db_session):
        """Token que no es JWT → 401."""
        user = await _create_user(db_session, username="basura")
        response = await client.post(
            DATA_TOKEN_URL, headers={"Authorization": "Bearer not-a-jwt-at-all"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_wrong_signature_is_rejected(self, client, db_session):
        """JWT firmado con otra clave RSA → 401."""
        user = await _create_user(db_session, username="firma-mala")
        other_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        )
        other_pem = other_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode()
        forged = jwt.encode(
            {"sub": str(user.id), "role": "authenticated", "type": "data"},
            other_pem,
            algorithm="RS256",
        )
        response = await client.post(
            DATA_TOKEN_URL, headers={"Authorization": f"Bearer {forged}"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_expired_hub_token_is_rejected(self, client, db_session):
        """Hub JWT expirado → 401."""
        user = await _create_user(db_session, username="expirado")
        expired = create_access_token(
            subject=str(user.id), expires_delta=timedelta(hours=-1)
        )
        response = await client.post(
            DATA_TOKEN_URL, headers={"Authorization": f"Bearer {expired}"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_signature_roundtrip_via_jwks(self, client, db_session):
        """La firma del data token se verifica con la clave del JWKS (crypto real)."""
        user = await _create_user(db_session, username="jwks")
        data = await _mint_data_token(client, user)

        # Cabecera con el kid que publica el hub
        header = jwt.get_unverified_header(data["access_token"])
        assert header["kid"] == "authcore-key-1"
        assert header["alg"] == "RS256"

        jwks_response = await client.get("/.well-known/jwks.json")
        assert jwks_response.status_code == status.HTTP_200_OK
        keys = jwks_response.json()["keys"]
        assert len(keys) == 1
        jwk = keys[0]
        assert jwk["kid"] == "authcore-key-1"

        n = int.from_bytes(_b64url_decode(jwk["n"]), "big")
        e = int.from_bytes(_b64url_decode(jwk["e"]), "big")
        public_pem = (
            rsa.RSAPublicNumbers(e=e, n=n)
            .public_key()
            .public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            .decode()
        )
        claims = jwt.decode(data["access_token"], public_pem, algorithms=["RS256"])
        assert claims["sub"] == str(user.id)
        assert claims["role"] == "authenticated"

    async def test_request_body_claims_are_ignored(self, client, db_session):
        """Triangulación: el body NO se lee; los claims vienen solo del usuario."""
        user = await _create_user(db_session, username="spoof")
        hub = await _hub_token(user)
        response = await client.post(
            DATA_TOKEN_URL,
            json={
                "role": "SUPERADMIN",
                "sub": "999",
                "type": "access",
                "tenant": {"id": "evil", "slug": "evil", "name": "evil"},
                "email": "attacker@evil.com",
            },
            headers={"Authorization": f"Bearer {hub}"},
        )

        assert response.status_code == status.HTTP_200_OK
        claims = _decode(response.json()["access_token"])
        assert claims["role"] == "authenticated"
        assert claims["sub"] == str(user.id)
        assert claims["type"] == "data"
        assert "tenant" not in claims
        assert "email" not in claims
