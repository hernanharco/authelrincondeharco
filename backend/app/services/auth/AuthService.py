"""
backend/app/services/auth/AuthService.py
Servicio de Autenticación - Principio de Responsabilidad Única
Incluye protección contra fuerza bruta: lockout tras N intentos fallidos.
"""

from typing import Optional, Tuple
from datetime import datetime, timezone
from fastapi import HTTPException, status
from app.models.user import User
from app.core.security import verify_password
from app.interfaces.auth.IAuthService import IAuthService
from app.interfaces.auth.ITokenService import ITokenService
from app.interfaces.auth.IOAuthService import IOAuthService
from app.interfaces.user.IUserRepository import IUserRepository
from app.interfaces.tenant.ITenantRepository import ITenantRepository
from app.services.tenant.TenantModuleService import TenantModuleService
from app.types.enums import UserRole, UserStatus

# ── Protección contra fuerza bruta ─────────────────────────────
# Cantidad de intentos fallidos antes de bloquear la cuenta.
MAX_FAILED_LOGIN_ATTEMPTS = 5


class AuthService(IAuthService):
    """
    Servicio de autenticación.
    NOTA: NO recibe `db: Session` — toda la persistencia se maneja
    a través de `user_repository` (Principio de Inversión de Dependencias).
    """

    def __init__(
        self,
        token_service: ITokenService,
        oauth_service: IOAuthService,
        user_repository: IUserRepository,
        tenant_repository: ITenantRepository = None,
        tenant_module_service: TenantModuleService = None,
    ):
        self.token_service = token_service
        self.oauth_service = oauth_service
        self.user_repository = user_repository
        self.tenant_repository = tenant_repository
        self.tenant_module_service = tenant_module_service

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Autentica un usuario con credenciales tradicionales.

        Incluye protección contra fuerza bruta:
        - Incrementa failed_login_attempts en cada fallo
        - Bloquea la cuenta al superar MAX_FAILED_LOGIN_ATTEMPTS
        - Resetea el contador al iniciar sesión exitosamente
        """
        user = await self.user_repository.get_by_username(username)
        if not user:
            user = await self.user_repository.get_by_email(username)

        if not user:
            return None

        # ── Cuenta bloqueada por intentos fallidos ─────────────
        if user.is_locked:
            return None

        # ── Verificar contraseña ───────────────────────────────
        if not verify_password(password, user.password_hash):
            new_attempts = (user.failed_login_attempts or 0) + 1
            update_data: dict[str, object] = {
                "failed_login_attempts": new_attempts,
            }

            # Bloquear si superó el límite
            if new_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
                update_data["is_locked"] = True

            await self.user_repository.update(user.id, update_data)
            return None

        # ── Login exitoso: resetear contador y desbloquear ────
        if user.failed_login_attempts > 0 or user.is_locked:
            await self.user_repository.update(user.id, {
                "failed_login_attempts": 0,
                "is_locked": False,
            })

        if not user.is_active:
            return None

        return user

    async def authenticate_with_google(
        self, token: str, origin: str
    ) -> Tuple[User, str, int]:
        try:
            user_info = await self.oauth_service.verify_token(token)
            email = user_info.get("email")

            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se pudo obtener el email del usuario",
                )

            user = await self.user_repository.get_by_email(email)

            if not user:
                base_username = email.split("@")[0]
                username = base_username
                suffix = 1
                while await self.user_repository.exists_by_username(username):
                    username = f"{base_username}{suffix}"
                    suffix += 1

                user = await self.user_repository.create(
                    {
                        "email": email,
                        "username": username,
                        "full_name": user_info.get("name", ""),
                        "password_hash": "",
                        "role": UserRole.NONE,       # 👈 cambiado
                        "status": UserStatus.PENDING, # 👈 cambiado
                        "is_active": False,           # 👈 cambiado
                        "origin": "google",
                    }
                )
                # Nuevo usuario pendiente — no generar token todavía
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="PENDING_APPROVAL",
                )

            # Usuario existente — verificar estado
            if user.status == UserStatus.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="PENDING_APPROVAL",
                )

            if not user.is_active or user.is_locked:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cuenta desactivada o bloqueada.",
                )

            internal_token, expires_in = await self.create_access_token(user)
            return user, internal_token, expires_in

        except HTTPException:
            raise
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error en autenticación: {str(e)}",
            )

    async def create_access_token(self, user: User) -> Tuple[str, int]:
        token_data: dict[str, object] = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "type": "access",
        }

        # ── Tenant + Modules (Feature Flags) ──────────────────────────────
        # Si el usuario tiene un tenant asignado, incluimos la info del tenant
        # y sus módulos activos en el JWT. Así los servicios downstream pueden
        # saber qué puede hacer cada usuario sin llamar a authCore.
        # ──────────────────────────────────────────────────────────────────
        tenant_id = getattr(user, "tenant_id", None)
        if tenant_id and self.tenant_repository and self.tenant_module_service:
            tenant = await self.tenant_repository.get_by_id(tenant_id)
            if tenant:
                token_data["tenant"] = {
                    "id": tenant.id,
                    "slug": tenant.slug,
                    "name": tenant.name,
                }
                # Construir dict de módulos activos con settings
                modules_dict = await self.tenant_module_service.get_modules_dict_for_jwt(tenant_id)
                if modules_dict:
                    token_data["modules"] = modules_dict

        # ── Datos no sensibles de empresa (legacy, se mantiene por compat) ─
        company_profile = user.__dict__.get("company_profile")
        if company_profile is not None:
            token_data["company_name"] = company_profile.company_name

        token, expires_at = await self.token_service.create_access_token(token_data)
        expires_in = int((expires_at - datetime.now(timezone.utc)).total_seconds())
        return token, expires_in

    async def revoke_token(self, token: str) -> bool:
        return await self.token_service.revoke_token(token)

    async def process_google_login(
        self, code: str, redirect_uri: str
    ) -> Tuple[User, str, int]:
        """
        Procesa un login con Google usando el Authorization Code Flow.
        Ahora usa las dependencias inyectadas (oauth_service, user_repository, token_service)
        en lugar de hacer llamadas HTTP directas y manipular la BD a mano.
        """
        try:
            # Paso 1: intercambiar code por info del usuario (delega en OAuthService)
            userinfo = await self.oauth_service.exchange_code(code, redirect_uri)
            email = userinfo.get("email")
            name = userinfo.get("name", "")

            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se pudo obtener email de Google",
                )

            # Paso 2: buscar o crear usuario (delega en UserRepository)
            user = await self.user_repository.get_by_email(email)

            if not user:
                # Nuevo usuario — crear como pendiente de aprobación
                base_username = email.split("@")[0]
                username = base_username
                counter = 1
                while await self.user_repository.exists_by_username(username):
                    username = f"{base_username}{counter}"
                    counter += 1

                await self.user_repository.create(
                    {
                        "username": username,
                        "email": email,
                        "full_name": name,
                        "password_hash": "",
                        "role": UserRole.NONE,
                        "status": UserStatus.PENDING,
                        "is_active": False,
                        "is_locked": False,
                        "origin": "google",
                    }
                )

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="PENDING_APPROVAL",
                )

            # Usuario existente — validar estado
            if user.status == UserStatus.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="PENDING_APPROVAL",
                )

            if user.is_locked:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cuenta bloqueada. Contacte con el administrador.",
                )

            # Paso 3: actualizar last_login y generar token (delega en servicios)
            await self.user_repository.update(user.id, {"last_login": datetime.now(timezone.utc)})

            internal_token, expires_in = await self.create_access_token(user)
            return user, internal_token, expires_in

        except HTTPException:
            raise
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error en Google OAuth: {str(e)}",
            )
