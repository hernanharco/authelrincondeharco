"""
Tests unitarios de CompanyProfileService (Fase 1).

Patrón de test_user_services.py: repositorio mockeado con AsyncMock
(spec de la interface), sin BD. Cubre cada método público por happy
path, permiso denegado (403) y no encontrado (404) donde aplica.
"""
import pytest
from unittest.mock import AsyncMock

from fastapi import HTTPException
from pydantic import ValidationError

from app.interfaces.company.ICompanyProfileRepository import (
    ICompanyProfileRepository,
)
from app.models.user import User
from app.schemas.company import CompanyProfileCreate, CompanyProfileUpdate
from app.services.company.CompanyProfileService import CompanyProfileService
from app.types.enums import UserRole, UserStatus

pytestmark = pytest.mark.asyncio

PROFILE = {"id": 1, "user_id": 1, "company_name": "ACME"}


def make_user(**overrides) -> User:
    """Usuario de prueba sin tocar la BD."""
    defaults = dict(
        id=1,
        username="owner",
        email="owner@example.com",
        full_name="Owner",
        password_hash="$2b$12$hashed_password",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        is_active=True,
        is_locked=False,
        failed_login_attempts=0,
        origin="manual",
    )
    defaults.update(overrides)
    return User(**defaults)


@pytest.fixture
def company_repository():
    return AsyncMock(spec=ICompanyProfileRepository)


@pytest.fixture
def company_service(company_repository):
    return CompanyProfileService(company_repository=company_repository)


@pytest.fixture
def owner_user():
    """Propietario del perfil (id 1) — USER, no admin."""
    return make_user(id=1)


@pytest.fixture
def admin_user():
    """Admin sobre cualquier perfil (id 1)."""
    return make_user(
        id=1, username="admin", email="admin@example.com", role=UserRole.ADMIN
    )


@pytest.fixture
def plain_user():
    """Usuario sin permisos (id 2)."""
    return make_user(id=2, username="plain", email="plain@example.com")


class TestCompanyProfileService:
    # ── get_profile ────────────────────────────────────────────

    async def test_get_profile_owner_success(
        self, company_service, company_repository, owner_user
    ):
        company_repository.get_by_user_id.return_value = PROFILE

        result = await company_service.get_profile(1, owner_user)

        assert result == PROFILE
        company_repository.get_by_user_id.assert_awaited_once_with(1)

    async def test_get_profile_admin_views_any_user(
        self, company_service, company_repository, admin_user
    ):
        company_repository.get_by_user_id.return_value = PROFILE

        result = await company_service.get_profile(2, admin_user)

        assert result == PROFILE
        company_repository.get_by_user_id.assert_awaited_once_with(2)

    async def test_get_profile_forbidden_for_plain_user(
        self, company_service, company_repository, plain_user
    ):
        with pytest.raises(HTTPException) as exc_info:
            await company_service.get_profile(1, plain_user)

        assert exc_info.value.status_code == 403
        company_repository.get_by_user_id.assert_not_awaited()

    async def test_get_profile_not_found(
        self, company_service, company_repository, owner_user
    ):
        company_repository.get_by_user_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await company_service.get_profile(1, owner_user)

        assert exc_info.value.status_code == 404

    # ── create_profile ─────────────────────────────────────────

    async def test_create_profile_admin_success(
        self, company_service, company_repository, admin_user
    ):
        company_repository.exists.return_value = False
        company_repository.create.return_value = PROFILE
        data = CompanyProfileCreate(company_name="ACME")

        result = await company_service.create_profile(1, data, admin_user)

        assert result == PROFILE
        company_repository.exists.assert_awaited_once_with(1)
        company_repository.create.assert_awaited_once_with(
            1, {"company_name": "ACME"}
        )

    async def test_create_profile_forbidden_for_plain_user(
        self, company_service, company_repository, plain_user
    ):
        data = CompanyProfileCreate(company_name="ACME")

        with pytest.raises(HTTPException) as exc_info:
            await company_service.create_profile(1, data, plain_user)

        assert exc_info.value.status_code == 403
        company_repository.exists.assert_not_awaited()
        company_repository.create.assert_not_awaited()

    async def test_create_profile_conflict_when_exists(
        self, company_service, company_repository, admin_user
    ):
        company_repository.exists.return_value = True
        data = CompanyProfileCreate(company_name="ACME")

        with pytest.raises(HTTPException) as exc_info:
            await company_service.create_profile(1, data, admin_user)

        assert exc_info.value.status_code == 409
        company_repository.create.assert_not_awaited()

    # ── update_profile ─────────────────────────────────────────

    async def test_update_profile_owner_success(
        self, company_service, company_repository, owner_user
    ):
        updated = {**PROFILE, "company_name": "Nuevo nombre"}
        company_repository.update.return_value = updated
        data = CompanyProfileUpdate(company_name="Nuevo nombre")

        result = await company_service.update_profile(1, data, owner_user)

        assert result == updated
        company_repository.update.assert_awaited_once_with(
            1, {"company_name": "Nuevo nombre"}
        )

    async def test_update_profile_forbidden_for_plain_user(
        self, company_service, company_repository, plain_user
    ):
        data = CompanyProfileUpdate(company_name="X")

        with pytest.raises(HTTPException) as exc_info:
            await company_service.update_profile(1, data, plain_user)

        assert exc_info.value.status_code == 403
        company_repository.update.assert_not_awaited()

    async def test_update_profile_not_found(
        self, company_service, company_repository, owner_user
    ):
        company_repository.update.return_value = None
        data = CompanyProfileUpdate(company_name="X")

        with pytest.raises(HTTPException) as exc_info:
            await company_service.update_profile(1, data, owner_user)

        assert exc_info.value.status_code == 404

    # ── delete_profile ─────────────────────────────────────────

    async def test_delete_profile_admin_success(
        self, company_service, company_repository, admin_user
    ):
        company_repository.delete.return_value = True

        await company_service.delete_profile(2, admin_user)

        company_repository.delete.assert_awaited_once_with(2)

    async def test_delete_profile_forbidden_for_plain_user(
        self, company_service, company_repository, plain_user
    ):
        with pytest.raises(HTTPException) as exc_info:
            await company_service.delete_profile(2, plain_user)

        assert exc_info.value.status_code == 403
        company_repository.delete.assert_not_awaited()

    async def test_delete_profile_not_found(
        self, company_service, company_repository, admin_user
    ):
        company_repository.delete.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await company_service.delete_profile(999, admin_user)

        assert exc_info.value.status_code == 404

    # ── upsert_profile ─────────────────────────────────────────

    async def test_upsert_profile_updates_when_exists(
        self, company_service, company_repository, owner_user
    ):
        updated = {**PROFILE, "company_name": "Renamed"}
        company_repository.exists.return_value = True
        company_repository.update.return_value = updated
        data = CompanyProfileUpdate(company_name="Renamed")

        result = await company_service.upsert_profile(1, data, owner_user)

        assert result == updated
        company_repository.update.assert_awaited_once_with(
            1, {"company_name": "Renamed"}
        )
        company_repository.create.assert_not_awaited()

    async def test_upsert_profile_creates_when_missing(
        self, company_service, company_repository, owner_user
    ):
        company_repository.exists.return_value = False
        company_repository.create.return_value = PROFILE
        data = CompanyProfileUpdate(company_name="ACME Corp", phone="600123123")

        result = await company_service.upsert_profile(1, data, owner_user)

        assert result == PROFILE
        company_repository.create.assert_awaited_once_with(
            1, {"company_name": "ACME Corp", "phone": "600123123"}
        )
        company_repository.update.assert_not_awaited()

    async def test_upsert_profile_forbidden_for_plain_user(
        self, company_service, company_repository, plain_user
    ):
        data = CompanyProfileUpdate(company_name="X")

        with pytest.raises(HTTPException) as exc_info:
            await company_service.upsert_profile(1, data, plain_user)

        assert exc_info.value.status_code == 403
        company_repository.exists.assert_not_awaited()

    async def test_upsert_profile_without_company_name_raises(
        self, company_service, company_repository, owner_user
    ):
        """Documenta el comportamiento REAL (bug de prod reportado, no fixeado):
        sin `company_name`, el servicio construye CompanyProfileCreate con
        company_name="" y la validación min_length=1 de Pydantic revienta →
        en el endpoint sería un 500."""
        company_repository.exists.return_value = False
        data = CompanyProfileUpdate(phone="600123123")

        with pytest.raises(ValidationError):
            await company_service.upsert_profile(1, data, owner_user)

        company_repository.create.assert_not_awaited()

    # ── get_public_profile ─────────────────────────────────────

    async def test_get_public_profile_success(
        self, company_service, company_repository
    ):
        company_repository.get_by_user_id.return_value = PROFILE

        result = await company_service.get_public_profile(1)

        assert result == PROFILE
        company_repository.get_by_user_id.assert_awaited_once_with(1)

    async def test_get_public_profile_not_found(
        self, company_service, company_repository
    ):
        company_repository.get_by_user_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await company_service.get_public_profile(404)

        assert exc_info.value.status_code == 404

    # ── get_all_profiles ───────────────────────────────────────

    async def test_get_all_profiles_admin_success(
        self, company_service, company_repository, admin_user
    ):
        company_repository.get_all.return_value = [PROFILE]

        result = await company_service.get_all_profiles(admin_user)

        assert result == [PROFILE]
        company_repository.get_all.assert_awaited_once_with()

    async def test_get_all_profiles_forbidden_for_plain_user(
        self, company_service, company_repository, plain_user
    ):
        with pytest.raises(HTTPException) as exc_info:
            await company_service.get_all_profiles(plain_user)

        assert exc_info.value.status_code == 403
        company_repository.get_all.assert_not_awaited()
