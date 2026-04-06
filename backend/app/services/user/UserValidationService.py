"""
Servicio de Validación de Usuarios - Principio de Responsabilidad Única
"""

from typing import Dict, Any
from fastapi import HTTPException, status
from app.models.user import User
from app.types.enums import UserRole, UserStatus
from app.domain.user_domain import UserDomain


class UserValidationService:
    """
    Servicio dedicado a validaciones de dominio y permisos de usuarios.
    SRP: Única responsabilidad = validar reglas de negocio y permisos.
    """

    @staticmethod
    def validate_user_exists(user: User) -> None:
        """Valida que el usuario exista."""
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Usuario no encontrado"
            )

    @staticmethod
    def validate_permission_to_view(current_user: User, target_user_id: int) -> None:
        """Valida permisos para ver un usuario específico."""
        domain = UserDomain(current_user)
        
        if not domain.is_manager_or_above() and current_user.id != target_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver este usuario",
            )

    @staticmethod
    def validate_permission_to_list(current_user: User) -> None:
        """Valida permisos para listar usuarios."""
        domain = UserDomain(current_user)
        
        if not domain.is_manager_or_above():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para listar usuarios",
            )

    @staticmethod
    def validate_permission_to_create(current_user: User) -> None:
        """Valida permisos para crear usuarios."""
        domain = UserDomain(current_user)
        
        if not domain.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para crear usuarios",
            )

    @staticmethod
    def validate_permission_to_update(current_user: User, target_user_id: int) -> None:
        """Valida permisos para actualizar un usuario."""
        domain = UserDomain(current_user)
        
        if not domain.is_admin() and current_user.id != target_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para actualizar este usuario",
            )

    @staticmethod
    def validate_permission_to_delete(current_user: User, target_user: User) -> None:
        """Valida permisos para eliminar un usuario."""
        domain = UserDomain(current_user)
        
        if not domain.can_delete(target_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para eliminar este usuario",
            )

    @staticmethod
    def validate_permission_to_change_role(current_user: User, new_role: UserRole) -> None:
        """Valida permisos para asignar un rol específico."""
        domain = UserDomain(current_user)
        
        if not domain.can_assign_role(new_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para asignar ese rol",
            )

    @staticmethod
    def validate_admin_permission(current_user: User, action: str) -> None:
        """Valida permisos de administrador para acciones específicas."""
        domain = UserDomain(current_user)
        
        if not domain.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes permiso para {action}",
            )

    @staticmethod
    def validate_superadmin_permission(current_user: User, action: str) -> None:
        """Valida permisos de superadministrador."""
        domain = UserDomain(current_user)
        
        if not domain.is_superadmin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Solo los superadministradores pueden {action}",
            )

    @staticmethod
    def validate_role_assignment(current_user: User, new_role: UserRole) -> None:
        """Valida que el usuario actual puede asignar el rol especificado."""
        domain = UserDomain(current_user)
        
        if not domain.can_assign_role(new_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para asignar ese rol",
            )

    @staticmethod
    def validate_self_role_change(current_user: User, target_user_id: int) -> None:
        """Valida que un usuario no puede cambiar su propio rol."""
        if current_user.id == target_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes cambiar tu propio rol",
            )

    @staticmethod
    def filter_sensitive_fields(update_data: Dict[str, Any], current_user: User) -> Dict[str, Any]:
        """Filtra campos sensibles para usuarios sin privilegios de admin."""
        domain = UserDomain(current_user)
        
        if not domain.is_admin():
            # Crear una copia para no modificar el original
            filtered_data = update_data.copy()
            for field in ["role", "status", "is_active", "is_locked"]:
                filtered_data.pop(field, None)
            return filtered_data
        
        return update_data

    @staticmethod
    def validate_user_data_for_creation(user_data: Dict[str, Any], current_user: User) -> Dict[str, Any]:
        """Valida y prepara datos para creación de usuario."""
        domain = UserDomain(current_user)
        
        # Validar rol si se está asignando
        if "role" in user_data:
            UserValidationService.validate_role_assignment(current_user, user_data["role"])
        else:
            user_data["role"] = UserRole.USER

        # Establecer valores por defecto
        user_data.setdefault("status", UserStatus.ACTIVE)
        user_data.setdefault("is_active", True)
        user_data.setdefault("is_locked", False)
        user_data.setdefault("failed_login_attempts", 0)

        return user_data
