"""
Tests para servicios de usuarios (reescritos en Fase 1 contra la API actual).
Cubren UserService y la lógica de negocio delegada (validación, consulta, actualización).

Unidad pura: repositorio mockeado (AsyncMock), sin BD.
Todos los métodos exigen `current_user`; `delete_user` es borrado físico
y devuelve el `User` eliminado; `get_stats` tiene la forma canónica.
"""
import pytest
from unittest.mock import AsyncMock, call

from fastapi import HTTPException

from app.interfaces.user.IUserRepository import IUserRepository
from app.models.user import User
from app.services.user.UserService import UserService
from app.types.enums import UserRole, UserStatus

pytestmark = pytest.mark.asyncio

# Forma canónica de get_stats (decisión de producto, Fase 1)
STATS_KEYS = {"total", "by_role", "by_status", "by_origin", "locked_accounts", "new_this_week"}


def make_user(**overrides) -> User:
    """Usuario de prueba sin tocar la BD."""
    defaults = dict(
        id=1,
        username="testuser",
        email="test@example.com",
        full_name="Test User",
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
def user_repository():
    return AsyncMock(spec=IUserRepository)


@pytest.fixture
def user_service(user_repository):
    # db no se usa: con el repo mockeado ninguna ruta toca la sesión.
    return UserService(db=AsyncMock(), user_repository=user_repository)


@pytest.fixture
def admin_user():
    """Usuario con permisos de admin sobre el resto (id 1)."""
    return make_user(id=1, username="admin", email="admin@example.com", role=UserRole.ADMIN)


@pytest.fixture
def target_user():
    """Objetivo típico de las operaciones (id 2)."""
    return make_user(id=2)


class TestUserService:
    """Tests para UserService — cada método recibe current_user explícito."""

    # ── Lecturas ────────────────────────────────────────────────

    async def test_get_user_by_id_success(
        self, user_service, user_repository, admin_user, target_user
    ):
        user_repository.get_by_id.return_value = target_user

        result = await user_service.get_user_by_id(2, admin_user)

        assert result is target_user
        assert result.username == "testuser"
        user_repository.get_by_id.assert_awaited_once_with(2)

    async def test_get_user_by_id_not_found(
        self, user_service, user_repository, admin_user
    ):
        user_repository.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await user_service.get_user_by_id(999, admin_user)

        assert exc_info.value.status_code == 404

    async def test_get_user_by_id_forbidden_for_plain_user(
        self, user_service, user_repository, target_user
    ):
        """Un USER solo puede verse a sí mismo: ver a otro lanza 403."""
        other_user = make_user(id=99, username="other")

        with pytest.raises(HTTPException) as exc_info:
            await user_service.get_user_by_id(2, other_user)

        assert exc_info.value.status_code == 403
        user_repository.get_by_id.assert_not_awaited()

    async def test_get_users_with_filters(
        self, user_service, user_repository, admin_user, target_user
    ):
        mock_users = [target_user, make_user(id=3, username="other")]
        user_repository.get_all.return_value = mock_users

        result = await user_service.get_users(
            skip=0, limit=10, search="test", role=UserRole.USER, current_user=admin_user
        )

        assert result == mock_users
        user_repository.get_all.assert_awaited_once_with(
            skip=0, limit=10, search="test", role=UserRole.USER
        )

    async def test_get_users_requires_authentication(self, user_service):
        """Sin current_user la lista se rechaza con 401."""
        with pytest.raises(HTTPException) as exc_info:
            await user_service.get_users(skip=0, limit=10)

        assert exc_info.value.status_code == 401

    # ── Creación ────────────────────────────────────────────────

    async def test_create_user_success(
        self, user_service, user_repository, admin_user, target_user
    ):
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "full_name": "New User",
            "password": "newpass123",
        }
        user_repository.exists_by_username.return_value = False
        user_repository.exists_by_email.return_value = False
        user_repository.create.return_value = target_user

        result = await user_service.create_user(user_data, admin_user)

        assert result is target_user
        user_repository.create.assert_awaited_once()
        created = user_repository.create.await_args.args[0]
        assert "password" not in created
        assert created["password_hash"].startswith("$2b$")
        assert created["role"] == UserRole.USER
        assert created["status"] == UserStatus.ACTIVE

    async def test_create_user_duplicate_username(
        self, user_service, user_repository, admin_user
    ):
        user_repository.exists_by_username.return_value = True

        with pytest.raises(HTTPException) as exc_info:
            await user_service.create_user(
                {"username": "existinguser", "email": "new@example.com"}, admin_user
            )

        assert exc_info.value.status_code == 400
        user_repository.create.assert_not_awaited()

    async def test_create_user_duplicate_email(
        self, user_service, user_repository, admin_user
    ):
        user_repository.exists_by_username.return_value = False
        user_repository.exists_by_email.return_value = True

        with pytest.raises(HTTPException) as exc_info:
            await user_service.create_user(
                {"username": "newuser", "email": "existing@example.com"}, admin_user
            )

        assert exc_info.value.status_code == 400
        user_repository.create.assert_not_awaited()

    async def test_create_user_forbidden_for_non_admin(
        self, user_service, user_repository
    ):
        plain_user = make_user(id=99, username="plain")

        with pytest.raises(HTTPException) as exc_info:
            await user_service.create_user(
                {"username": "x", "email": "x@example.com"}, plain_user
            )

        assert exc_info.value.status_code == 403
        user_repository.create.assert_not_awaited()

    # ── Actualización ───────────────────────────────────────────

    async def test_update_user_success(
        self, user_service, user_repository, admin_user, target_user
    ):
        update_data = {"full_name": "Updated Name"}
        user_repository.get_by_id.return_value = target_user
        user_repository.update.return_value = target_user

        result = await user_service.update_user(2, update_data, admin_user)

        assert result is target_user
        user_repository.update.assert_awaited_once_with(2, update_data)

    async def test_update_user_not_found(self, user_service, user_repository, admin_user):
        user_repository.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await user_service.update_user(999, {"full_name": "X"}, admin_user)

        assert exc_info.value.status_code == 404
        user_repository.update.assert_not_awaited()

    # ── Borrado físico (decisión de producto, Fase 1) ───────────

    async def test_delete_user_returns_deleted_user(
        self, user_service, user_repository, admin_user, target_user
    ):
        """Borrado FÍSICO: repo borra y devuelve el User; el servicio lo retorna tal cual."""
        user_repository.get_by_id.return_value = target_user
        user_repository.delete.return_value = target_user

        result = await user_service.delete_user(2, admin_user)

        assert isinstance(result, User)
        assert result is target_user
        assert result.username == "testuser"
        user_repository.delete.assert_awaited_once_with(2)

    async def test_delete_user_not_found(self, user_service, user_repository, admin_user):
        user_repository.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await user_service.delete_user(999, admin_user)

        assert exc_info.value.status_code == 404
        user_repository.delete.assert_not_awaited()

    async def test_delete_user_race_guard(
        self, user_service, user_repository, admin_user, target_user
    ):
        """La validación ve al usuario pero el repo devuelve None al borrar → 404."""
        user_repository.get_by_id.return_value = target_user
        user_repository.delete.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await user_service.delete_user(2, admin_user)

        assert exc_info.value.status_code == 404

    async def test_delete_user_self_forbidden(
        self, user_service, user_repository, admin_user
    ):
        """Nadie puede eliminarse a sí mismo (can_delete → 403)."""
        user_repository.get_by_id.return_value = admin_user

        with pytest.raises(HTTPException) as exc_info:
            await user_service.delete_user(1, admin_user)

        assert exc_info.value.status_code == 403
        user_repository.delete.assert_not_awaited()

    # ── Roles y estados ─────────────────────────────────────────

    async def test_update_user_role_success(
        self, user_service, user_repository, admin_user, target_user
    ):
        user_repository.get_by_id.return_value = target_user
        user_repository.update.return_value = target_user

        result = await user_service.update_user_role(2, UserRole.MANAGER, admin_user)

        assert result is target_user
        # Asignar un rol válido activa la cuenta automáticamente
        user_repository.update.assert_awaited_once_with(
            2,
            {"role": UserRole.MANAGER, "status": UserStatus.ACTIVE, "is_active": True},
        )

    async def test_update_user_role_self(
        self, user_service, user_repository, admin_user
    ):
        user_repository.get_by_id.return_value = admin_user

        with pytest.raises(HTTPException) as exc_info:
            await user_service.update_user_role(1, UserRole.ADMIN, admin_user)

        assert exc_info.value.status_code == 400
        user_repository.update.assert_not_awaited()

    async def test_update_user_status_success(
        self, user_service, user_repository, admin_user, target_user
    ):
        user_repository.get_by_id.return_value = target_user
        user_repository.update.return_value = target_user

        result = await user_service.update_user_status(2, UserStatus.SUSPENDED, admin_user)

        assert result is target_user
        # status e is_active se actualizan juntos
        user_repository.update.assert_awaited_once_with(
            2, {"status": UserStatus.SUSPENDED, "is_active": False}
        )

    async def test_update_user_lock(
        self, user_service, user_repository, admin_user, target_user
    ):
        user_repository.get_by_id.return_value = target_user
        user_repository.update.return_value = target_user

        result = await user_service.update_user_lock(2, True, admin_user)
        assert result is target_user

        result = await user_service.update_user_lock(2, False, admin_user)
        assert result is target_user

        assert user_repository.update.await_args_list == [
            call(2, {"is_locked": True}),
            call(2, {"is_locked": False}),
        ]

    async def test_update_user_lock_forbidden_for_non_admin(
        self, user_service, user_repository, target_user
    ):
        plain_user = make_user(id=99, username="plain")
        user_repository.get_by_id.return_value = target_user

        with pytest.raises(HTTPException) as exc_info:
            await user_service.update_user_lock(2, True, plain_user)

        assert exc_info.value.status_code == 403
        user_repository.update.assert_not_awaited()

    async def test_update_user_notes(
        self, user_service, user_repository, admin_user, target_user
    ):
        user_repository.get_by_id.return_value = target_user
        user_repository.update.return_value = target_user

        notes = "Usuario activo y verificado"
        result = await user_service.update_user_notes(2, notes, admin_user)

        assert result is target_user
        user_repository.update.assert_awaited_once_with(2, {"notes": notes})

    # ── Consultas y estadísticas ────────────────────────────────

    async def test_get_pending_users(
        self, user_service, user_repository, admin_user, target_user
    ):
        mock_pending = [target_user]
        user_repository.get_pending_users.return_value = mock_pending

        result = await user_service.get_pending_users(admin_user)

        assert result == mock_pending
        user_repository.get_pending_users.assert_awaited_once_with()

    async def test_get_stats(self, user_service, user_repository, admin_user):
        """Forma canónica de get_stats (decisión de producto, Fase 1)."""
        mock_stats = {
            "total": 100,
            "by_role": {"USER": 80, "ADMIN": 10, "NONE": 10},
            "by_status": {"ACTIVE": 85, "PENDING": 15},
            "by_origin": {"google": 50, "manual": 50},
            "locked_accounts": 3,
            "new_this_week": 7,
        }
        user_repository.get_stats.return_value = mock_stats

        result = await user_service.get_stats(admin_user)

        assert result == mock_stats
        assert set(result.keys()) == STATS_KEYS
        user_repository.get_stats.assert_awaited_once_with()

    async def test_get_users_by_origin(
        self, user_service, user_repository, admin_user
    ):
        mock_origins = [
            {"origin": "google", "count": 50},
            {"origin": "manual", "count": 30},
        ]
        user_repository.get_users_by_origin.return_value = mock_origins

        result = await user_service.get_users_by_origin(admin_user)

        assert result == mock_origins
        user_repository.get_users_by_origin.assert_awaited_once_with()
