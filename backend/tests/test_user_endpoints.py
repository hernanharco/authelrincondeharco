"""
Tests para endpoints de usuarios (reescritos en Fase 1 contra la API actual).
Cubren CRUD, permisos por rol, pendientes, stats, búsqueda y actividad.

Deriva vs la suite original (todo estaba skipeado con pytestmark):
- Fixtures: los usuarios ahora se PERSISTEN con `db_session` (antes los
  fixtures devolvían objetos sin id y nunca se guardaban) y los headers usan
  `create_access_token(subject=str(user.id))` real (antes
  `create_access_token(data={...})` → TypeError contra la firma actual).
- POST /users/ → 200 (la suite vieja asumía 201; el endpoint no declara
  status_code=201).
- DELETE /users/{id} → 200 con el usuario borrado en el cuerpo y 404 al
  volver a pedirlo (borrado FÍSICO, commit 39aec50); USER y MANAGER → 403
  (guard de endpoint admin+).
- GET /users/pending → guard admin+ en endpoint Y en servicio
  (validate_admin_permission): ADMIN 200, SUPERADMIN 200, USER 403.
- GET /users/stats → claves canónicas `total`, `by_role`, `by_status`,
  `by_origin`, `locked_accounts`, `new_this_week` (antes total_users/
  active_users/pending_users, que ya no existen).
- Nuevos desde el commit 39aec50 (antes no probados): GET /users/search
  (q con min_length=2, guard manager+) y GET /users/{id}/activity
  (guard manager+, forma UserActivitySummary).
"""
import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User, UserRole, UserStatus
from app.schemas.user import UserCreate, UserUpdate, RoleUpdate, StatusUpdate

pytestmark = pytest.mark.asyncio

# Forma canónica de get_stats (decisión de producto, Fase 1)
STATS_KEYS = {
    "total",
    "by_role",
    "by_status",
    "by_origin",
    "locked_accounts",
    "new_this_week",
}

# Campos exactos de UserActivitySummary / get_user_activity_summary
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


# ── Helpers ──────────────────────────────────────────────────────


def make_user(**overrides) -> User:
    """Usuario ORM válido para persistir (full_name/password_hash NOT NULL)."""
    if "username" not in overrides or "email" not in overrides:
        raise ValueError("make_user exige username y email únicos por test")
    defaults = dict(
        full_name="Test User",
        # Hash de mentira: estos tests no hacen login con estos usuarios
        password_hash="$2b$12$hashed_password",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        is_active=True,
        is_locked=False,
    )
    defaults.update(overrides)
    return User(**defaults)


async def seed_user(db_session: AsyncSession, **overrides) -> User:
    """Persiste un usuario y lo devuelve con id asignado."""
    user = make_user(**overrides)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def auth_headers(user: User) -> dict:
    """Cabecera Authorization con un JWT RS256 real para un usuario persistido."""
    token = create_access_token(subject=str(user.id))
    return {"Authorization": f"Bearer {token}"}


# ── Tests ────────────────────────────────────────────────────────


class TestUserEndpoints:
    """Tests para endpoints de usuarios"""

    # ── Lecturas ────────────────────────────────────────────────

    async def test_get_current_user(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """GET /users/me devuelve el usuario del token"""
        user = await seed_user(
            db_session, username="testuser", email="test@example.com"
        )
        response = await client.get("/api/v1/users/me", headers=auth_headers(user))

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == user.username
        assert data["email"] == user.email

    async def test_get_users_as_admin(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """GET /users/ como administrador → 200 con listado"""
        admin = await seed_user(
            db_session,
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
        )
        await seed_user(db_session, username="testuser", email="test@example.com")

        response = await client.get("/api/v1/users/", headers=auth_headers(admin))

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    async def test_get_users_as_user_forbidden(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """GET /users/ como usuario normal → 403 (guard manager+ del endpoint)"""
        user = await seed_user(
            db_session, username="plainuser", email="plain@example.com"
        )
        response = await client.get("/api/v1/users/", headers=auth_headers(user))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_get_users_with_filters(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """GET /users/ con filtros de rol, búsqueda y paginación"""
        admin = await seed_user(
            db_session,
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
        )
        await seed_user(db_session, username="testuser", email="test@example.com")
        headers = auth_headers(admin)

        response = await client.get("/api/v1/users/?role=USER", headers=headers)
        assert response.status_code == status.HTTP_200_OK

        response = await client.get("/api/v1/users/?search=test", headers=headers)
        assert response.status_code == status.HTTP_200_OK

        response = await client.get("/api/v1/users/?skip=0&limit=5", headers=headers)
        assert response.status_code == status.HTTP_200_OK

    async def test_get_user_by_id_success(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """GET /users/{id} como administrador → 200"""
        admin = await seed_user(
            db_session,
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
        )
        target = await seed_user(
            db_session, username="testuser", email="test@example.com"
        )

        response = await client.get(
            f"/api/v1/users/{target.id}", headers=auth_headers(admin)
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == target.id
        assert data["username"] == target.username

    async def test_get_user_by_id_not_found(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """GET /users/{id} inexistente → 404"""
        admin = await seed_user(
            db_session,
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
        )
        response = await client.get("/api/v1/users/99999", headers=auth_headers(admin))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ── Creación ────────────────────────────────────────────────

    async def test_create_user_as_admin(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """POST /users/ como administrador → 200 (la suite vieja asumía 201)"""
        admin = await seed_user(
            db_session,
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
        )
        user_data = UserCreate(
            username="newuser",
            email="newuser@example.com",
            full_name="New User",
            password="newpass123",
            role=UserRole.USER,
        )

        response = await client.post(
            "/api/v1/users/",
            json=user_data.model_dump(),
            headers=auth_headers(admin),
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["role"] == UserRole.USER.value

    async def test_create_user_duplicate_username(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """POST /users/ con username duplicado → 400"""
        admin = await seed_user(
            db_session,
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
        )
        await seed_user(db_session, username="testuser", email="test@example.com")
        user_data = UserCreate(
            username="testuser",  # Duplicado
            email="different@example.com",
            full_name="Different User",
            password="newpass123",
        )

        response = await client.post(
            "/api/v1/users/",
            json=user_data.model_dump(),
            headers=auth_headers(admin),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "ya existe" in response.json()["detail"]

    async def test_create_user_as_user_forbidden(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """POST /users/ como usuario normal → 403 (guard admin+ del endpoint)"""
        user = await seed_user(
            db_session, username="plainuser", email="plain@example.com"
        )
        user_data = UserCreate(
            username="newuser",
            email="newuser@example.com",
            full_name="New User",
            password="newpass123",
        )

        response = await client.post(
            "/api/v1/users/",
            json=user_data.model_dump(),
            headers=auth_headers(user),
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    # ── Actualización ───────────────────────────────────────────

    async def test_update_user_as_admin(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """PUT /users/{id} como administrador → 200 con los cambios"""
        admin = await seed_user(
            db_session,
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
        )
        target = await seed_user(
            db_session, username="testuser", email="test@example.com"
        )
        update_data = UserUpdate(
            full_name="Updated Name",
            email="updated@example.com",
        )

        response = await client.put(
            f"/api/v1/users/{target.id}",
            json=update_data.model_dump(exclude_unset=True),
            headers=auth_headers(admin),
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["email"] == "updated@example.com"

    async def test_update_user_role(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """PATCH /users/{id}/role como administrador → 200 con el rol nuevo"""
        admin = await seed_user(
            db_session,
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
        )
        target = await seed_user(
            db_session, username="testuser", email="test@example.com"
        )
        role_data = RoleUpdate(role=UserRole.MANAGER)

        response = await client.patch(
            f"/api/v1/users/{target.id}/role",
            json=role_data.model_dump(),
            headers=auth_headers(admin),
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == UserRole.MANAGER.value

    async def test_update_user_status(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """PATCH /users/{id}/status como administrador → 200 (status + is_active)"""
        admin = await seed_user(
            db_session,
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
        )
        target = await seed_user(
            db_session, username="testuser", email="test@example.com"
        )
        status_data = StatusUpdate(status=UserStatus.SUSPENDED)

        response = await client.patch(
            f"/api/v1/users/{target.id}/status",
            json=status_data.model_dump(),
            headers=auth_headers(admin),
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == UserStatus.SUSPENDED.value
        assert data["is_active"] is False

    # ── Borrado físico (decisión de producto, Fase 1) ───────────

    async def test_delete_user_as_admin(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """DELETE /users/{id} → 200 con el usuario borrado en el cuerpo;
        GET posterior → 404 (borrado FÍSICO, commit 39aec50)."""
        admin = await seed_user(
            db_session,
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
        )
        target = await seed_user(
            db_session, username="testuser", email="test@example.com"
        )
        headers = auth_headers(admin)

        response = await client.delete(
            f"/api/v1/users/{target.id}", headers=headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == target.id
        assert data["username"] == "testuser"

        # El usuario ya no existe
        response = await client.get(f"/api/v1/users/{target.id}", headers=headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_user_as_user_forbidden(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """DELETE /users/{id} como usuario normal → 403"""
        user = await seed_user(
            db_session, username="plainuser", email="plain@example.com"
        )
        target = await seed_user(
            db_session, username="testuser", email="test@example.com"
        )

        response = await client.delete(
            f"/api/v1/users/{target.id}", headers=auth_headers(user)
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_delete_user_as_manager_forbidden(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """DELETE /users/{id} como MANAGER → 403 (solo admin+ elimina)"""
        manager = await seed_user(
            db_session,
            username="manager",
            email="manager@example.com",
            role=UserRole.MANAGER,
        )
        target = await seed_user(
            db_session, username="testuser", email="test@example.com"
        )

        response = await client.delete(
            f"/api/v1/users/{target.id}", headers=auth_headers(manager)
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    # ── Pendientes (guard alineado a admin+ en commit 39aec50) ──

    async def test_get_pending_users_as_admin(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """GET /users/pending como ADMIN → 200 con los pendientes"""
        admin = await seed_user(
            db_session,
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
        )
        await seed_user(
            db_session,
            username="pendinguser",
            email="pending@example.com",
            full_name="Pending User",
            role=UserRole.NONE,
            status=UserStatus.PENDING,
            is_active=False,
        )

        response = await client.get(
            "/api/v1/users/pending", headers=auth_headers(admin)
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert any(u["username"] == "pendinguser" for u in data)

    async def test_get_pending_users_as_superadmin(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """GET /users/pending como SUPERADMIN → 200"""
        superadmin = await seed_user(
            db_session,
            username="superadmin",
            email="superadmin@example.com",
            role=UserRole.SUPERADMIN,
        )

        response = await client.get(
            "/api/v1/users/pending", headers=auth_headers(superadmin)
        )

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)

    async def test_get_pending_users_as_user_forbidden(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """GET /users/pending como usuario normal → 403"""
        user = await seed_user(
            db_session, username="plainuser", email="plain@example.com"
        )

        response = await client.get(
            "/api/v1/users/pending", headers=auth_headers(user)
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    # ── Estadísticas (forma canónica, Fase 1) ───────────────────

    async def test_get_user_stats_as_admin(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """GET /users/stats → 200 con las claves canónicas"""
        admin = await seed_user(
            db_session,
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
        )
        await seed_user(db_session, username="testuser", email="test@example.com")
        await seed_user(
            db_session,
            username="pendinguser",
            email="pending@example.com",
            role=UserRole.NONE,
            status=UserStatus.PENDING,
            is_active=False,
        )

        response = await client.get(
            "/api/v1/users/stats", headers=auth_headers(admin)
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert set(data.keys()) == STATS_KEYS
        assert data["total"] == 3
        assert isinstance(data["by_role"], dict)
        assert isinstance(data["by_status"], dict)

    async def test_get_user_stats_as_user_forbidden(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """GET /users/stats como usuario normal → 403 (guard manager+)"""
        user = await seed_user(
            db_session, username="plainuser", email="plain@example.com"
        )

        response = await client.get(
            "/api/v1/users/stats", headers=auth_headers(user)
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_get_users_by_origin_as_admin(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """GET /users/by-origin → 200 con lista [{origin, count}]"""
        admin = await seed_user(
            db_session,
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
        )
        await seed_user(db_session, username="testuser", email="test@example.com")

        response = await client.get(
            "/api/v1/users/by-origin", headers=auth_headers(admin)
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert data
        assert {"origin", "count"} <= set(data[0].keys())

    # ── Búsqueda y actividad (nuevos desde commit 39aec50) ──────

    async def test_search_users_as_manager(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """GET /users/search?q=... → 200 con SearchResponse (guard manager+)"""
        manager = await seed_user(
            db_session,
            username="manager",
            email="manager@example.com",
            role=UserRole.MANAGER,
        )
        await seed_user(db_session, username="testuser", email="test@example.com")

        response = await client.get(
            "/api/v1/users/search",
            params={"q": "test"},
            headers=auth_headers(manager),
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert set(data.keys()) == {"users", "total_found", "search_query"}
        assert data["search_query"] == "test"
        assert data["total_found"] == len(data["users"])
        assert any(u["username"] == "testuser" for u in data["users"])

    async def test_search_users_as_user_forbidden(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """GET /users/search como usuario normal → 403 (guard manager+)"""
        user = await seed_user(
            db_session, username="plainuser", email="plain@example.com"
        )

        response = await client.get(
            "/api/v1/users/search",
            params={"q": "test"},
            headers=auth_headers(user),
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_get_user_activity_as_manager(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """GET /users/{id}/activity → 200 con la forma UserActivitySummary"""
        manager = await seed_user(
            db_session,
            username="manager",
            email="manager@example.com",
            role=UserRole.MANAGER,
        )
        target = await seed_user(
            db_session, username="testuser", email="test@example.com"
        )

        response = await client.get(
            f"/api/v1/users/{target.id}/activity", headers=auth_headers(manager)
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert set(data.keys()) == ACTIVITY_KEYS
        assert data["user_id"] == target.id
        assert data["username"] == "testuser"
        assert data["failed_attempts"] == 0
        assert data["is_locked"] is False

    async def test_get_user_activity_not_found(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """GET /users/{id}/activity de un usuario inexistente → 404"""
        manager = await seed_user(
            db_session,
            username="manager",
            email="manager@example.com",
            role=UserRole.MANAGER,
        )

        response = await client.get(
            "/api/v1/users/99999/activity", headers=auth_headers(manager)
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
