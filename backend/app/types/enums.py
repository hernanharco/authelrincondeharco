"""
Enumeraciones del dominio de usuarios corregidas para coincidir con DB.
"""
import enum

class UserRole(str, enum.Enum): # Agregamos 'str' para facilitar comparaciones
    SUPERADMIN = "SUPERADMIN"  # Antes era "superadmin"
    ADMIN = "ADMIN"            # Antes era "admin"
    MANAGER = "MANAGER"
    USER = "USER"
    VIEWER = "VIEWER"
    NONE = "NONE"

class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"          # Antes era "active"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    PENDING = "PENDING"