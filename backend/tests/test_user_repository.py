"""
Tests para repositorio de usuarios (reescritos en Fase 1 contra la API actual).
Cubren acceso a datos y operaciones CRUD de UserRepository.

Cambios respecto a la versión saltada:
- 100% async: todos los tests son `async` y usan la fixture `db_session`
  (aiosqlite); las tablas se recrean por test (fixture autouse `db`).
- `create` recibe un dict de campos válidos (no `obj.__dict__`, que incluye
  `_sa_instance_state` y rompe `User(**data)`).
- `delete` es BORRADO FÍSICO: devuelve el `User` eliminado y `get_by_id`
  devuelve `None` después (antes asumía borrado lógico con `is_active=False`).
- `get_stats` usa las claves canónicas: total, by_role, by_status,
  by_origin, locked_accounts, new_this_week (antes: total_users/active_users/
  pending_users, que ya no existen).
- Nuevos en commit 39aec50: `search_users` (ILIKE case-insensitive,
  ordenado por username, con límite) y `get_user_activity_summary`
  (404 HTTPException si el usuario no existe).
- `test_get_pending_users` del viejo suite referenciaba el fixture
  `test_user` sin declararlo (error latente; nunca ejecutó por el skip).
"""
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from fastapi import HTTPException, status

from app.repositories.UserRepository import UserRepository
from app.models.user import UserRole, UserStatus

pytestmark = pytest.mark.asyncio

# Forma canónica de get_stats (decisión de producto, Fase 1)
STATS_KEYS = {"total", "by_role", "by_status", "by_origin", "locked_accounts", "new_this_week"}

# Campos exactos de get_user_activity_summary
ACTIVITY_KEYS = {
    "user_id",
    "username",
    "total_logins",
    "last_login",
    "failed_attempts",
    "is_locked",
    "account_age_days",
    "recent_activity",
}


def make_user_data(**overrides) -> dict:
    """Datos de usuario válidos para UserRepository.create()."""
    defaults = dict(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        password_hash="$2b$12$hashed_password",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        is_active=True,
        is_locked=False,
    )
    defaults.update(overrides)
    return defaults


class TestUserRepository:
    """Tests para UserRepository"""

    @pytest_asyncio.fixture
    async def user_repository(self, db_session):
        """Instancia de UserRepository sobre la sesión async de tests"""
        return UserRepository(db_session)

    @pytest.fixture
    def test_user(self):
        """Datos del usuario de prueba (no persistidos hasta `create`)"""
        return make_user_data()

    # ── CRUD básico ─────────────────────────────────────────────

    async def test_create_user(self, user_repository, test_user):
        """Test crear usuario en base de datos"""
        result = await user_repository.create(test_user)

        assert result is not None
        assert result.id is not None
        assert result.username == test_user["username"]
        assert result.email == test_user["email"]

    async def test_get_by_id_success(self, user_repository, test_user):
        """Test obtener usuario por ID"""
        created = await user_repository.create(test_user)

        result = await user_repository.get_by_id(created.id)

        assert result is not None
        assert result.id == created.id
        assert result.username == test_user["username"]

    async def test_get_by_id_not_found(self, user_repository):
        """Test obtener usuario por ID que no existe"""
        result = await user_repository.get_by_id(99999)

        assert result is None

    async def test_get_by_username_success(self, user_repository, test_user):
        """Test obtener usuario por username"""
        await user_repository.create(test_user)

        result = await user_repository.get_by_username(test_user["username"])

        assert result is not None
        assert result.username == test_user["username"]

    async def test_get_by_username_not_found(self, user_repository):
        """Test obtener usuario por username que no existe"""
        result = await user_repository.get_by_username("nonexistent")

        assert result is None

    async def test_get_by_email_success(self, user_repository, test_user):
        """Test obtener usuario por email"""
        await user_repository.create(test_user)

        result = await user_repository.get_by_email(test_user["email"])

        assert result is not None
        assert result.email == test_user["email"]

    async def test_get_by_email_not_found(self, user_repository):
        """Test obtener usuario por email que no existe"""
        result = await user_repository.get_by_email("nonexistent@example.com")

        assert result is None

    async def test_exists_by_username_true(self, user_repository, test_user):
        """Test verificar existencia por username - existe"""
        await user_repository.create(test_user)

        result = await user_repository.exists_by_username(test_user["username"])

        assert result is True

    async def test_exists_by_username_false(self, user_repository):
        """Test verificar existencia por username - no existe"""
        result = await user_repository.exists_by_username("nonexistent")

        assert result is False

    async def test_exists_by_email_true(self, user_repository, test_user):
        """Test verificar existencia por email - existe"""
        await user_repository.create(test_user)

        result = await user_repository.exists_by_email(test_user["email"])

        assert result is True

    async def test_exists_by_email_false(self, user_repository):
        """Test verificar existencia por email - no existe"""
        result = await user_repository.exists_by_email("nonexistent@example.com")

        assert result is False

    # ── Listado y filtros ───────────────────────────────────────

    async def test_get_all_with_filters(self, user_repository):
        """Test listar usuarios con filtros de rol, búsqueda y paginación"""
        users_data = [
            make_user_data(username="user1", email="user1@example.com", full_name="User One"),
            make_user_data(
                username="admin1",
                email="admin1@example.com",
                full_name="Admin One",
                role=UserRole.ADMIN,
            ),
            make_user_data(),  # testuser
        ]
        for data in users_data:
            await user_repository.create(data)

        # Sin filtros (las tablas se recrean por test: exactamente 3)
        result_all = await user_repository.get_all()
        assert len(result_all) == 3

        # Filtro por rol
        result_users = await user_repository.get_all(role=UserRole.USER)
        assert {u.username for u in result_users} == {"user1", "testuser"}

        # Filtro por búsqueda (ilike sobre username/email/full_name)
        result_search = await user_repository.get_all(search="user")
        assert {u.username for u in result_search} == {"user1", "testuser"}

        # Paginación
        assert len(await user_repository.get_all(skip=0, limit=2)) == 2
        assert len(await user_repository.get_all(skip=2, limit=2)) == 1

    async def test_get_pending_users(self, user_repository):
        """Test obtener usuarios pendientes"""
        await user_repository.create(
            make_user_data(
                username="pending",
                email="pending@example.com",
                full_name="Pending User",
                role=UserRole.NONE,
                status=UserStatus.PENDING,
            )
        )
        await user_repository.create(make_user_data())  # usuario activo

        result = await user_repository.get_pending_users()

        assert len(result) == 1
        assert result[0].status == UserStatus.PENDING
        assert result[0].username == "pending"

    # ── Update ──────────────────────────────────────────────────

    async def test_update_user(self, user_repository, test_user):
        """Test actualizar usuario"""
        created = await user_repository.create(test_user)

        update_data = {"full_name": "Updated Name", "email": "updated@example.com"}
        result = await user_repository.update(created.id, update_data)

        assert result is not None
        assert result.full_name == "Updated Name"
        assert result.email == "updated@example.com"
        # El resto de campos no cambia
        assert result.username == test_user["username"]

    async def test_update_user_not_found(self, user_repository):
        """Test actualizar usuario que no existe"""
        result = await user_repository.update(99999, {"full_name": "Updated Name"})

        assert result is None

    # ── Delete (físico) ─────────────────────────────────────────

    async def test_delete_user_physical(self, user_repository, test_user):
        """Test eliminar usuario: borrado FÍSICO, la fila desaparece"""
        created = await user_repository.create(test_user)

        result = await user_repository.delete(created.id)

        # delete() devuelve el User eliminado (no bool)
        assert result is not None
        assert result.username == test_user["username"]

        # Tras el delete la fila ya no existe (no es borrado lógico)
        assert await user_repository.get_by_id(created.id) is None
        assert await user_repository.get_by_username(test_user["username"]) is None

    async def test_delete_user_not_found(self, user_repository):
        """Test eliminar usuario que no existe (devuelve None)"""
        result = await user_repository.delete(99999)

        assert result is None

    # ── Estadísticas y origen ───────────────────────────────────

    async def test_get_stats(self, user_repository):
        """Test obtener estadísticas con las claves canónicas exactas"""
        await user_repository.create(
            make_user_data(username="active", email="active@example.com", full_name="Active User")
        )
        await user_repository.create(
            make_user_data(
                username="pending",
                email="pending@example.com",
                full_name="Pending User",
                role=UserRole.NONE,
                status=UserStatus.PENDING,
            )
        )
        await user_repository.create(make_user_data())  # testuser

        result = await user_repository.get_stats()

        assert set(result.keys()) == STATS_KEYS
        assert result["total"] == 3
        assert result["by_role"] == {UserRole.USER: 2, UserRole.NONE: 1}
        assert result["by_status"] == {UserStatus.ACTIVE: 2, UserStatus.PENDING: 1}
        assert result["by_origin"] == {"unknown": 3}  # origin NULL agrupa como "unknown"
        assert result["locked_accounts"] == 0
        assert result["new_this_week"] == 3  # creados hace instantes

    async def test_get_users_by_origin(self, user_repository):
        """Test obtener usuarios agrupados por origen"""
        await user_repository.create(
            make_user_data(
                username="googleuser",
                email="google@example.com",
                full_name="Google User",
                origin="google",
            )
        )
        await user_repository.create(
            make_user_data(
                username="manualuser",
                email="manual@example.com",
                full_name="Manual User",
                origin="manual",
            )
        )
        await user_repository.create(make_user_data())  # sin origin → "unknown"

        result = await user_repository.get_users_by_origin()

        assert isinstance(result, list)
        # Sin ORDER BY: comparamos ordenado por origin
        assert sorted(result, key=lambda item: item["origin"]) == [
            {"origin": "google", "count": 1},
            {"origin": "manual", "count": 1},
            {"origin": "unknown", "count": 1},
        ]

    # ── search_users (nuevo en 39aec50) ─────────────────────────

    async def test_search_users_case_insensitive(self, user_repository):
        """Test búsqueda por username, email y full_name sin respetar mayúsculas"""
        await user_repository.create(
            make_user_data(username="alpha", email="alpha@example.com", full_name="Alpha One")
        )
        await user_repository.create(
            make_user_data(username="bravo", email="bravo@example.com", full_name="Bravo Two")
        )

        # Query en mayúsculas contra username en minúsculas
        result = await user_repository.search_users("ALPH")
        assert [u.username for u in result] == ["alpha"]

        # Coincidencia parcial por email
        result = await user_repository.search_users("bravo@example")
        assert [u.username for u in result] == ["bravo"]

        # Coincidencia por full_name, case-insensitive
        result = await user_repository.search_users("alpha one")
        assert [u.username for u in result] == ["alpha"]

    async def test_search_users_orders_by_username(self, user_repository):
        """Test que search_users ordena por username ascendente"""
        for name in ("charlie", "alpha", "bravo"):  # insertados fuera de orden
            await user_repository.create(
                make_user_data(username=name, email=f"{name}@example.com")
            )

        # "a" aparece en los tres usernames
        result = await user_repository.search_users("a")

        assert [u.username for u in result] == ["alpha", "bravo", "charlie"]

    async def test_search_users_respects_limit(self, user_repository):
        """Test que search_users respeta el límite (default 50)"""
        for name in ("sort1", "sort2", "sort3"):
            await user_repository.create(
                make_user_data(username=name, email=f"{name}@example.com")
            )

        result = await user_repository.search_users("sort", limit=2)
        # Orden por username + corte en el límite
        assert [u.username for u in result] == ["sort1", "sort2"]

        # Sin límite explícito caben los tres (default 50)
        assert len(await user_repository.search_users("sort")) == 3

    async def test_search_users_no_match(self, user_repository, test_user):
        """Test search_users sin coincidencias devuelve lista vacía"""
        await user_repository.create(test_user)

        result = await user_repository.search_users("no-such-user")

        assert result == []

    # ── get_user_activity_summary (nuevo en 39aec50) ────────────

    async def test_get_user_activity_summary(self, user_repository):
        """Test resumen de actividad: conjunto exacto de claves y valores"""
        created = await user_repository.create(
            make_user_data(
                login_count=7,
                failed_login_attempts=3,
                last_login=datetime.now(timezone.utc) - timedelta(days=1),
            )
        )

        summary = await user_repository.get_user_activity_summary(created.id)

        assert set(summary.keys()) == ACTIVITY_KEYS
        assert summary["user_id"] == created.id
        assert summary["username"] == "testuser"
        assert summary["total_logins"] == 7
        assert summary["failed_attempts"] == 3
        assert summary["is_locked"] is False
        assert summary["account_age_days"] >= 0
        assert summary["last_login"] is not None
        assert summary["recent_activity"] is True  # login dentro de los últimos 7 días

    async def test_get_user_activity_summary_old_login(self, user_repository):
        """Test resumen: login fuera de la ventana de 7 días y cuenta bloqueada"""
        created = await user_repository.create(
            make_user_data(
                is_locked=True,
                login_count=0,
                last_login=datetime.now(timezone.utc) - timedelta(days=10),
            )
        )

        summary = await user_repository.get_user_activity_summary(created.id)

        assert summary["is_locked"] is True
        assert summary["recent_activity"] is False
        assert summary["total_logins"] == 0
        assert summary["failed_attempts"] == 0

    async def test_get_user_activity_summary_without_login(self, user_repository):
        """Test resumen de usuario que nunca inició sesión"""
        created = await user_repository.create(make_user_data())

        summary = await user_repository.get_user_activity_summary(created.id)

        assert summary["last_login"] is None
        assert summary["recent_activity"] is False

    async def test_get_user_activity_summary_not_found(self, user_repository):
        """Test resumen de actividad de usuario inexistente → 404"""
        with pytest.raises(HTTPException) as exc_info:
            await user_repository.get_user_activity_summary(99999)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
