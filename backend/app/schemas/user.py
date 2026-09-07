from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.types.enums import UserRole, UserStatus

# --- RESPUESTAS (Lo que el API devuelve) ---


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole
    status: UserStatus
    is_active: bool
    is_locked: bool
    last_login: Optional[datetime] = None
    origin: Optional[str] = None
    avatar_url: Optional[str] = None
    notes: Optional[str] = None
    last_ip: Optional[str] = None
    login_count: int = 0
    tenant_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

    model_config = ConfigDict(from_attributes=True)


# --- ENTRADAS (Lo que el API recibe) ---


class GoogleLogin(BaseModel):
    # 'credential' es el nombre que envía el botón de Google por defecto
    token: str = Field(..., description="El ID Token o Access Token de Google")
    origin: Optional[str] = Field(default="google")

    # populate_by_name permite usar 'token' o 'credential' en el código Python
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: Optional[str] = "oauth_no_password"
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE
    is_active: bool = True
    is_locked: bool = False
    origin: str = "web"
    failed_login_attempts: int = 0
    avatar_url: Optional[str] = None
    notes: Optional[str] = None
    last_ip: Optional[str] = None
    login_count: int = 0
    tenant_id: Optional[str] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    is_active: Optional[bool] = None
    is_locked: Optional[bool] = None
    avatar_url: Optional[str] = None
    notes: Optional[str] = None
    last_ip: Optional[str] = None
    login_count: Optional[int] = None
    tenant_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RoleUpdate(BaseModel):
    role: UserRole


class StatusUpdate(BaseModel):
    status: UserStatus


class LockUpdate(BaseModel):
    is_locked: bool


class NotesUpdate(BaseModel):
    notes: str


class UserStats(BaseModel):
    total: int
    by_role: dict[str, int]
    by_status: dict[str, int]
    by_origin: dict[str, int]
    new_this_week: int
    locked_accounts: int


class UserActivitySummary(BaseModel):
    user_id: int
    username: str
    total_logins: int
    last_login: Optional[datetime] = None
    failed_attempts: int
    is_locked: bool
    account_age_days: int
    recent_activity: bool


class ProfileUpdate(BaseModel):
    """Schema para actualizar datos del perfil (campos no sensibles).
    
    NOTA: Los datos de empresa (nombre, CIF, dirección, IBAN, etc.)
    se agregarán en Fase 2 con un modelo CompanyProfile dedicado.
    """

    avatar_url: Optional[str] = None


class PasswordReset(BaseModel):
    """Schema para reset de contraseña."""

    new_password: str = Field(..., min_length=8)
    confirm_password: str


class BulkUpdateRequest(BaseModel):
    """Schema para actualización masiva de usuarios."""

    user_ids: list[int] = Field(..., min_length=1)
    update_data: dict


class SearchResponse(BaseModel):
    """Schema para respuesta de búsqueda."""

    users: list[UserResponse]
    total_found: int
    search_query: str


class UsersByOrigin(BaseModel):
    origin: str
    count: int

    model_config = ConfigDict(from_attributes=True)
