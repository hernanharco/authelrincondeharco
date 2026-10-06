"""
Tests para lógica de dominio
Cubren reglas de negocio y validaciones de dominio (UserDomain).

Reescritos contra la API actual (Fase 1):
- `is_active()`/`is_locked()` ya no existen → `is_authenticated()`,
  `is_pending_approval()`, `can_login()`.
- `can_assign_role` solo permite SUPERADMIN asignar SUPERADMIN/ADMIN.
- `can_delete` exige ser admin o superior (manager ya no elimina).
"""
import pytest
from app.domain.user_domain import UserDomain
from app.models.user import User, UserRole, UserStatus


class TestUserDomain:
    """Tests para UserDomain"""

    @pytest.fixture
    def admin_user(self):
        """Usuario administrador para tests"""
        return User(
            id=2,
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_active=True,
            is_locked=False
        )

    @pytest.fixture
    def manager_user(self):
        """Usuario manager para tests"""
        return User(
            id=3,
            username="manager",
            email="manager@example.com",
            role=UserRole.MANAGER,
            status=UserStatus.ACTIVE,
            is_active=True,
            is_locked=False
        )

    @pytest.fixture
    def regular_user(self):
        """Usuario regular para tests"""
        return User(
            id=4,
            username="user",
            email="user@example.com",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            is_active=True,
            is_locked=False
        )

    @pytest.fixture
    def superadmin_user(self):
        """Usuario superadmin para tests"""
        return User(
            id=1,
            username="superadmin",
            email="superadmin@example.com",
            role=UserRole.SUPERADMIN,
            status=UserStatus.ACTIVE,
            is_active=True,
            is_locked=False
        )

    # ── Jerarquía de roles ──────────────────────────────────────

    def test_is_superadmin_true(self, superadmin_user):
        """Test verificación de superadmin - true"""
        domain = UserDomain(superadmin_user)

        assert domain.is_superadmin() is True

    def test_is_superadmin_false(self, admin_user, manager_user, regular_user):
        """Test verificación de superadmin - false"""
        for user in [admin_user, manager_user, regular_user]:
            domain = UserDomain(user)
            assert domain.is_superadmin() is False

    def test_is_admin_true(self, admin_user, superadmin_user):
        """Test verificación de admin - true (admin o superior)"""
        for user in [admin_user, superadmin_user]:
            domain = UserDomain(user)
            assert domain.is_admin() is True

    def test_is_admin_false(self, manager_user, regular_user):
        """Test verificación de admin - false"""
        for user in [manager_user, regular_user]:
            domain = UserDomain(user)
            assert domain.is_admin() is False

    def test_is_manager_or_above_true(self, manager_user, admin_user, superadmin_user):
        """Test verificación de manager o superior - true"""
        for user in [manager_user, admin_user, superadmin_user]:
            domain = UserDomain(user)
            assert domain.is_manager_or_above() is True

    def test_is_manager_or_above_false(self, regular_user):
        """Test verificación de manager o superior - false"""
        domain = UserDomain(regular_user)
        assert domain.is_manager_or_above() is False

    # ── Asignación de roles ─────────────────────────────────────

    def test_can_assign_role_superadmin(self, superadmin_user):
        """Test asignación de roles - superadmin puede asignar cualquier rol"""
        domain = UserDomain(superadmin_user)

        # Superadmin puede asignar cualquier rol
        assert domain.can_assign_role(UserRole.SUPERADMIN) is True
        assert domain.can_assign_role(UserRole.ADMIN) is True
        assert domain.can_assign_role(UserRole.MANAGER) is True
        assert domain.can_assign_role(UserRole.USER) is True
        assert domain.can_assign_role(UserRole.VIEWER) is True

    def test_can_assign_role_admin(self, admin_user):
        """Test asignación de roles - solo SUPERADMIN asigna SUPERADMIN/ADMIN"""
        domain = UserDomain(admin_user)

        # Admin puede asignar roles por debajo de su nivel...
        assert domain.can_assign_role(UserRole.MANAGER) is True
        assert domain.can_assign_role(UserRole.USER) is True
        assert domain.can_assign_role(UserRole.VIEWER) is True

        # ... pero NO SUPERADMIN ni ADMIN (exclusivo de SUPERADMIN)
        assert domain.can_assign_role(UserRole.SUPERADMIN) is False
        assert domain.can_assign_role(UserRole.ADMIN) is False

    def test_can_assign_role_manager(self, manager_user):
        """Test asignación de roles - manager no puede asignar roles (no es admin)"""
        domain = UserDomain(manager_user)

        # Manager no es admin: no puede asignar ningún rol
        assert domain.can_assign_role(UserRole.USER) is False
        assert domain.can_assign_role(UserRole.VIEWER) is False
        assert domain.can_assign_role(UserRole.MANAGER) is False
        assert domain.can_assign_role(UserRole.ADMIN) is False
        assert domain.can_assign_role(UserRole.SUPERADMIN) is False

    def test_can_assign_role_regular_user(self, regular_user):
        """Test asignación de roles - usuario regular no puede asignar roles"""
        domain = UserDomain(regular_user)

        # Usuario regular no puede asignar ningún rol
        assert domain.can_assign_role(UserRole.USER) is False
        assert domain.can_assign_role(UserRole.VIEWER) is False
        assert domain.can_assign_role(UserRole.MANAGER) is False
        assert domain.can_assign_role(UserRole.ADMIN) is False
        assert domain.can_assign_role(UserRole.SUPERADMIN) is False

    # ── Eliminación de usuarios ─────────────────────────────────

    def test_can_delete_user_superadmin(self, superadmin_user, admin_user, manager_user, regular_user):
        """Test eliminación - superadmin puede eliminar a todos menos a sí mismo"""
        domain = UserDomain(superadmin_user)

        # Superadmin puede eliminar a todos los demás
        assert domain.can_delete(admin_user) is True
        assert domain.can_delete(manager_user) is True
        assert domain.can_delete(regular_user) is True

        # Superadmin NO puede eliminarse a sí mismo
        assert domain.can_delete(superadmin_user) is False

    def test_can_delete_user_admin(self, admin_user, superadmin_user, manager_user, regular_user):
        """Test eliminación - admin elimina roles inferiores, nunca a un superadmin"""
        domain = UserDomain(admin_user)

        # Admin puede eliminar a roles inferiores
        assert domain.can_delete(manager_user) is True
        assert domain.can_delete(regular_user) is True

        # Admin NO puede eliminar a un superadmin
        assert domain.can_delete(superadmin_user) is False

        # Admin NO puede eliminarse a sí mismo
        assert domain.can_delete(admin_user) is False

    def test_can_delete_user_manager(self, manager_user, regular_user):
        """Test eliminación - manager no es admin: no puede eliminar a nadie"""
        domain = UserDomain(manager_user)

        # Manager no tiene permiso de eliminación
        assert domain.can_delete(regular_user) is False

        # Tampoco a sí mismo
        assert domain.can_delete(manager_user) is False

    def test_can_delete_user_regular(self, regular_user):
        """Test eliminación - usuario regular no puede eliminar"""
        domain = UserDomain(regular_user)

        # Usuario regular no puede eliminar a nadie
        assert domain.can_delete(regular_user) is False

    # ── Estado de autenticación (is_authenticated) ──────────────

    def test_is_authenticated_active_user(self, admin_user):
        """Usuario activo y con status ACTIVE está autenticado"""
        domain = UserDomain(admin_user)

        assert domain.is_authenticated() is True

    def test_is_not_authenticated_inactive_user(self, admin_user):
        """Usuario con is_active=False no está autenticado"""
        admin_user.is_active = False
        domain = UserDomain(admin_user)

        assert domain.is_authenticated() is False

    def test_is_not_authenticated_non_active_status(self, admin_user):
        """Usuario activo pero con status distinto de ACTIVE no está autenticado"""
        admin_user.status = UserStatus.SUSPENDED
        domain = UserDomain(admin_user)

        assert domain.is_authenticated() is False

    # ── Login permitido (can_login) ─────────────────────────────

    def test_can_login_active_user(self, regular_user):
        """Usuario activo, ACTIVE, con rol y sin bloqueo puede login"""
        domain = UserDomain(regular_user)

        assert domain.can_login() is True

    def test_can_login_locked_user(self, admin_user):
        """Usuario bloqueado no puede iniciar sesión"""
        admin_user.is_locked = True
        domain = UserDomain(admin_user)

        assert domain.can_login() is False

    def test_can_login_inactive_user(self, admin_user):
        """Usuario inactivo no puede iniciar sesión"""
        admin_user.is_active = False
        domain = UserDomain(admin_user)

        assert domain.can_login() is False

    def test_can_login_pending_user(self, admin_user):
        """Usuario con status PENDING no puede iniciar sesión"""
        admin_user.status = UserStatus.PENDING
        domain = UserDomain(admin_user)

        assert domain.can_login() is False

    def test_can_login_user_without_role(self, regular_user):
        """Usuario con rol NONE no puede iniciar sesión"""
        regular_user.role = UserRole.NONE
        domain = UserDomain(regular_user)

        assert domain.can_login() is False

    # ── Aprobación pendiente (is_pending_approval) ──────────────

    def test_is_pending_approval_status_pending(self, regular_user):
        """Usuario con status PENDING está pendiente de aprobación"""
        regular_user.status = UserStatus.PENDING
        domain = UserDomain(regular_user)

        assert domain.is_pending_approval() is True

    def test_is_pending_approval_role_none(self, regular_user):
        """Usuario con rol NONE está pendiente de aprobación"""
        regular_user.role = UserRole.NONE
        domain = UserDomain(regular_user)

        assert domain.is_pending_approval() is True

    def test_is_not_pending_approval_active_user(self, regular_user):
        """Usuario ACTIVE con rol asignado no está pendiente de aprobación"""
        domain = UserDomain(regular_user)

        assert domain.is_pending_approval() is False

    # ── Jerarquía y casos edge ──────────────────────────────────

    def test_user_hierarchy(self):
        """Test jerarquía de usuarios"""
        # Definir jerarquía esperada
        hierarchy = {
            UserRole.SUPERADMIN: 5,
            UserRole.ADMIN: 4,
            UserRole.MANAGER: 3,
            UserRole.USER: 2,
            UserRole.VIEWER: 1,
            UserRole.NONE: 0
        }

        for role, level in hierarchy.items():
            user = User(
                id=level,
                username=f"user_{role.value.lower()}",
                email=f"{role.value.lower()}@example.com",
                role=role,
                status=UserStatus.ACTIVE,
                is_active=True,
                is_locked=False
            )
            domain = UserDomain(user)

            # Verificar que el dominio puede determinar el nivel correctamente
            if role == UserRole.SUPERADMIN:
                assert domain.is_superadmin() is True
                assert domain.is_admin() is True
                assert domain.is_manager_or_above() is True
            elif role == UserRole.ADMIN:
                assert domain.is_superadmin() is False
                assert domain.is_admin() is True
                assert domain.is_manager_or_above() is True
            elif role == UserRole.MANAGER:
                assert domain.is_superadmin() is False
                assert domain.is_admin() is False
                assert domain.is_manager_or_above() is True
            else:
                # USER, VIEWER y NONE no alcanzan nivel de gestión
                assert domain.is_superadmin() is False
                assert domain.is_admin() is False
                assert domain.is_manager_or_above() is False

    def test_edge_cases(self):
        """Test casos edge y validaciones"""
        # Usuario sin rol
        user_no_role = User(
            id=10,
            username="norole",
            email="norole@example.com",
            role=UserRole.NONE,
            status=UserStatus.ACTIVE,
            is_active=True,
            is_locked=False
        )
        domain = UserDomain(user_no_role)

        # Sin rol, no debe tener permisos
        assert domain.is_superadmin() is False
        assert domain.is_admin() is False
        assert domain.is_manager_or_above() is False
        # ... y está pendiente de aprobación
        assert domain.is_pending_approval() is True

        # Usuario inactivo
        user_inactive = User(
            id=11,
            username="inactive",
            email="inactive@example.com",
            role=UserRole.USER,
            status=UserStatus.INACTIVE,
            is_active=False,
            is_locked=False
        )
        domain_inactive = UserDomain(user_inactive)

        # Usuario inactivo no está autenticado ni puede loguear,
        # aunque tenga rol asignado
        assert domain_inactive.is_authenticated() is False
        assert domain_inactive.can_login() is False
        # Los métodos de permisos dependen solo del rol
        assert domain_inactive.is_admin() is False
