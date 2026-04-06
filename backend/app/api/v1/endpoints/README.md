# Endpoints de Usuarios - API REST v1

## Overview

Esta documentación describe todos los endpoints disponibles para la gestión de usuarios en la API v1. Los endpoints han sido actualizados para aprovechar la nueva arquitectura de servicios especializados que sigue los principios SOLID.

## 🏗️ Arquitectura Subyacente

- **UserService**: Facade que coordina los servicios especializados
- **UserQueryService**: Maneja todas las operaciones de consulta
- **UserUpdateService**: Maneja todas las operaciones de actualización
- **UserValidationService**: Centraliza validaciones y permisos

## 📋 Endpoints Disponibles

### 🔐 Autenticación y Perfil

#### `GET /users/me`
- **Descripción**: Obtiene el perfil del usuario autenticado
- **Autenticación**: Requiere token válido
- **Response**: `UserResponse`

```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "USER",
  "status": "ACTIVE",
  "is_active": true,
  "is_locked": false,
  "last_login": "2024-01-15T10:30:00Z",
  "origin": "web",
  "avatar_url": null,
  "notes": null,
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

### 👥 Gestión de Usuarios (Admin/Manager)

#### `GET /users/`
- **Descripción**: Lista usuarios con paginación y filtros
- **Permisos**: Manager o Admin
- **Query Params**:
  - `skip`: Offset para paginación (default: 0)
  - `limit`: Límite de resultados (default: 100, max: 100)
  - `search`: Término de búsqueda opcional
  - `role`: Filtro por rol (USER, ADMIN, etc.)
- **Response**: `List[UserResponse]`

#### `GET /users/{user_id}`
- **Descripción**: Obtiene un usuario específico por ID
- **Permisos**: Usuario autenticado (solo propio perfil) o Manager/Admin
- **Response**: `UserResponse`

#### `POST /users/`
- **Descripción**: Crea un nuevo usuario
- **Permisos**: Admin únicamente
- **Request**: `UserCreate`
- **Response**: `UserResponse`

```json
{
  "username": "new_user",
  "email": "new@example.com",
  "full_name": "New User",
  "password": "secure_password",
  "role": "USER",
  "origin": "web"
}
```

#### `PUT /users/{user_id}`
- **Descripción**: Actualiza completamente un usuario
- **Permisos**: Usuario autenticado (solo propio perfil) o Admin
- **Request**: `UserUpdate`
- **Response**: `UserResponse`

#### `DELETE /users/{user_id}`
- **Descripción**: Desactiva un usuario (borrado lógico)
- **Permisos**: Admin únicamente
- **Response**: `UserResponse` (usuario desactivado)

---

### 🔧 Operaciones Específicas

#### `PATCH /users/{user_id}/role`
- **Descripción**: Actualiza el rol de un usuario
- **Permisos**: Admin únicamente
- **Request**: `RoleUpdate`
- **Response**: `UserResponse`

```json
{
  "role": "ADMIN"
}
```

#### `PATCH /users/{user_id}/status`
- **Descripción**: Actualiza el estado de un usuario
- **Permisos**: Admin únicamente
- **Request**: `StatusUpdate`
- **Response**: `UserResponse`

```json
{
  "status": "ACTIVE"
}
```

#### `PATCH /users/{user_id}/lock`
- **Descripción**: Bloquea o desbloquea un usuario
- **Permisos**: Admin únicamente
- **Request**: `LockUpdate`
- **Response**: `UserResponse`

```json
{
  "is_locked": true
}
```

#### `POST /users/{user_id}/notes`
- **Descripción**: Agrega o actualiza notas de un usuario
- **Permisos**: Admin únicamente
- **Request**: `NotesUpdate`
- **Response**: `UserResponse`

```json
{
  "notes": "Usuario verificado manualmente"
}
```

---

### 📊 Estadísticas y Reportes

#### `GET /users/stats`
- **Descripción**: Obtiene estadísticas generales de usuarios
- **Permisos**: Manager o Admin
- **Response**: `UserStats`

```json
{
  "total": 150,
  "by_role": {
    "USER": 120,
    "ADMIN": 25,
    "SUPERADMIN": 5
  },
  "by_status": {
    "ACTIVE": 140,
    "INACTIVE": 8,
    "PENDING": 2
  },
  "by_origin": {
    "web": 100,
    "google": 45,
    "api": 5
  },
  "new_this_week": 12,
  "locked_accounts": 3
}
```

#### `GET /users/by-origin`
- **Descripción**: Obtiene usuarios agrupados por origen
- **Permisos**: Manager o Admin
- **Response**: `List[UsersByOrigin]`

#### `GET /users/pending`
- **Descripción**: Obtiene usuarios pendientes de aprobación
- **Permisos**: Superadmin únicamente
- **Response**: `List[UserResponse]`

---

### 🔍 Nuevos Endpoints (Arquitectura Especializada)

#### `GET /users/search`
- **Descripción**: Busca usuarios por nombre, username o email
- **Permisos**: Manager o Admin
- **Query Params**:
  - `q`: Término de búsqueda (mínimo 2 caracteres)
  - `limit`: Límite de resultados (default: 50, max: 100)
- **Response**: `SearchResponse`

```json
{
  "users": [...],
  "total_found": 5,
  "search_query": "john"
}
```

#### `GET /users/{user_id}/activity`
- **Descripción**: Obtiene resumen de actividad de un usuario
- **Permisos**: Manager o Admin
- **Response**: `UserActivitySummary`

```json
{
  "user_id": 1,
  "username": "john_doe",
  "total_logins": 45,
  "last_login": "2024-01-15T10:30:00Z",
  "failed_attempts": 2,
  "is_locked": false,
  "account_age_days": 30,
  "recent_activity": true
}
```

#### `PATCH /users/{user_id}/profile`
- **Descripción**: Actualiza datos del perfil (campos no sensibles)
- **Permisos**: Usuario autenticado (solo propio perfil)
- **Request**: `ProfileUpdate`
- **Response**: `UserResponse`

```json
{
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "bio": "Software Developer",
  "avatar_url": "https://example.com/avatar.jpg"
}
```

#### `POST /users/{user_id}/reset-password`
- **Descripción**: Resetea la contraseña de un usuario
- **Permisos**: Admin únicamente
- **Request**: `PasswordReset`
- **Response**: `dict`

```json
{
  "new_password": "new_secure_password",
  "confirm_password": "new_secure_password"
}
```

#### `PATCH /users/bulk-update`
- **Descripción**: Actualiza múltiples usuarios en lote
- **Permisos**: Admin únicamente
- **Request**: `BulkUpdateRequest`
- **Response**: `List[UserResponse]`

```json
{
  "user_ids": [1, 2, 3],
  "update_data": {
    "status": "ACTIVE",
    "is_locked": false
  }
}
```

---

## 🔒 Códigos de Estado

| Código | Descripción |
|--------|-------------|
| 200 | Operación exitosa |
| 201 | Recurso creado exitosamente |
| 400 | Solicitud inválida (datos incorrectos) |
| 401 | No autenticado |
| 403 | No autorizado (sin permisos) |
| 404 | Recurso no encontrado |
| 422 | Error de validación (Pydantic) |

## 🛡️ Seguridad

- Todos los endpoints (excepto `/me`) requieren autenticación vía token Bearer
- Los permisos se validan según el rol del usuario
- Las validaciones se centralizan en `UserValidationService`
- Los campos sensibles se filtran automáticamente según permisos

## 📈 Mejoras Recientes

### ✅ Optimizaciones Aplicadas

1. **Uso de métodos principales**: Los endpoints ahora usan los métodos principales de UserService en lugar de los métodos de compatibilidad
2. **Validaciones mejoradas**: Uso de schemas Pydantic para mejor validación de entrada
3. **Nuevos endpoints**: Se agregaron endpoints especializados que aprovechan la arquitectura modular
4. **Respuestas estructuradas**: Mejores formatos de respuesta con información adicional
5. **Manejo de errores**: Mejor gestión de errores y mensajes descriptivos

### 🔄 Compatibilidad Mantenida

- Todos los endpoints existentes siguen funcionando igual
- No se requieren cambios en los clientes existentes
- Los métodos de compatibilidad permanecen disponibles

## 🚀 Próximas Mejoras

- Paginación mejorada con cursores
- Filtros avanzados por fecha
- Exportación de datos a CSV/Excel
- Webhooks para eventos de usuario
- Sistema de auditoría completo
