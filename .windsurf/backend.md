# Backend AuthCore - Resumen Técnico

## Estructura del Proyecto

### 📁 Archivos de Configuración
- **pyproject.toml**: Configuración Poetry con FastAPI 0.128.0 y dependencias
- **poetry.lock**: Lock file de dependencias
- **requirements.txt**: Dependencias para despliegue (generado por Poetry)
- **.pre-commit-config.yaml**: Hooks de pre-commit para calidad de código

### 📁 Archivos de Entorno
- **.env**: Variables de entorno (DATABASE_URL, SECRET_KEY, Google OAuth)
- **.env.example**: Plantilla de variables de entorno
- **.gitignore**: Exclusiones de __pycache__, venv, .env

### 📁 Docker y Despliegue
- **dockerfile**: Imagen Docker optimizada con Poetry
- **.dockerignore**: Exclusiones para imagen Docker
- **poetry-setup.sh**: Script de configuración de Poetry

### 📁 Source Code (`app/`)

#### 📂 `main.py` - Entry Point
- Configuración FastAPI con lifespan management async
- Middleware CORS dinámico por entorno
- Endpoints de salud (/health, /info)
- Inclusión de routers API v1
- Gestión de tablas de BD en startup

#### 📂 `core/` - Configuración Central
- **config.py**: Gestión de configuración con Pydantic Settings
- **security.py**: Utilidades de seguridad (JWT, bcrypt, OAuth)
- **middleware.py**: Middleware personalizado (opcional)

#### 📂 `db/` - Base de Datos
- **session.py**: Conexión SQLAlchemy síncrona con Neon PostgreSQL

#### 📂 `models/` - Modelos SQLAlchemy
- **base.py**: Modelo base con ID autoincremental y timestamps
- **user.py**: Modelo User con roles (str enum), estado, seguridad
- **__init__.py**: Exportación de modelos

#### 📂 `schemas/` - Modelos Pydantic
- **user.py**: Schemas para API (UserCreate, UserResponse, RoleUpdate)
- **auth.py**: Schemas de autenticación (LoginRequest, LoginResponse, GoogleLoginRequest)
- **__init__.py**: Exportación de schemas

#### 📂 `interfaces/` - Contratos SOLID (DIP, ISP)
- **auth/**: Interfaces de servicios de autenticación
  - **IAuthService.py**: Contrato principal de autenticación
  - **ITokenService.py**: Gestión de tokens JWT
  - **IOAuthService.py**: Integración con proveedores OAuth
- **user/**: Interfaces de gestión de usuarios
  - **IUserService.py**: Lógica de negocio de usuarios
  - **IUserRepository.py**: Acceso a datos de usuarios

#### 📂 `services/` - Lógica de Negocio SOLID (S, OCP)
- **auth/**: Servicios de autenticación
  - **AuthService.py**: Orquestador principal de autenticación
  - **TokenService.py**: Gestión de tokens JWT
  - **GoogleOAuthService.py**: Integración con Google OAuth
- **user/**: Servicios de usuarios
  - **UserService.py**: Lógica de negocio de usuarios con validaciones

#### 📂 `repositories/` - Acceso a Datos SOLID (S, DIP)
- **UserRepository.py**: Implementación de acceso a datos de usuarios
- **BaseRepository.py**: Repositorio base genérico

#### 📂 `domain/` - Dominio Puro
- **user_domain.py**: Lógica de negocio pura de usuarios (roles, permisos)

#### 📂 `api/` - Endpoints API
- **route.py**: Router principal con prefijo /api/v1
- **v1/**: Endpoints versión 1
  - **dependencies.py**: Inyección de dependencias (DIP)
  - **endpoints/**: Endpoints específicos
    - **auth/**: Autenticación modular
      - **login.py**: Login tradicional
      - **google.py**: Google OAuth
    - **users.py**: CRUD de usuarios con permisos

#### 📂 `types/` - Tipos Personalizados
- **enums.py**: Enums para UserRole (str enum), UserStatus (str enum)

### 📁 Tests (`tests/`)
- **unit/**: Tests unitarios de servicios y repositorios
- **integration/**: Tests de integración de endpoints
- **e2e/**: Tests end-to-end

### 📁 Archivos Adicionales
- **README.md**: Documentación completa del backend
- **agent.md**: Guía de desarrollo y arquitectura
- **.windsurfrules**: Reglas específicas del IDE
- **fix_user.py**: Script de mantenimiento (opcional)

#### 📂 `services/` - Lógica de Negocio
- **auth_service.py**: Servicios de autenticación con Google OAuth
- **user_service.py**: Servicios de gestión de usuarios

#### 📂 `domain/` - Dominio
- **user_domain.py**: Lógica de negocio pura de usuarios (roles, permisos)

#### 📂 `types/` - Tipos Personalizados
- **enums.py**: Enums para UserRole (str enum), UserStatus (str enum)

### 📁 Tests (`tests/`)
- **test_auth.py**: Tests de autenticación
- **test_users.py**: Tests de gestión de usuarios

### 📁 Archivos Adicionales
- **README.md**: Documentación completa del backend
- **agent.md**: Guía de desarrollo y arquitectura
- **.windsurfrules**: Reglas específicas del IDE
- **fix_user.py**: Script de mantenimiento (opcional)

## Características Principales

### 🚀 FastAPI 0.128.0
- API RESTful con documentación automática (Swagger)
- Validación de datos con Pydantic
- Soporte síncrono con SQLAlchemy
- Dependency injection

### 🗄️ PostgreSQL con Neon
- SQLAlchemy 2.0 síncrono
- Connection pooling optimizado
- Migraciones automáticas en startup
- Modelo de usuarios completo con ID autoincremental

### 🔐 Seguridad Robusta
- JWT con expiración configurable
- bcrypt para password hashing
- Google OAuth 2.0 integrado (@react-oauth/google)
- Sistema de roles jerárquico (SUPERADMIN > ADMIN > MANAGER > USER > VIEWER > NONE)
- httpOnly cookies + Authorization header

### 🏗️ Arquitectura SOLID
- **S**: Single Responsibility - Cada clase con una sola responsabilidad
- **O**: Open/Closed - Interfaces extensibles sin modificar código
- **L**: Liskov Substitution - Implementaciones intercambiables
- **I**: Interface Segregation - Interfaces específicas y pequeñas
- **D**: Dependency Inversion - Inyección de dependencias con FastAPI

### 🛠️ Desarrollo Optimizado
- Poetry para gestión de dependencias
- Pre-commit hooks (black, isort, flake8, mypy)
- Type hints obligatorios
- Tests con pytest

## Sistema de Roles y Permisos

### Roles Definidos (str enum)
- **SUPERADMIN**: Control total del SaaS
- **ADMIN**: Gestión de usuarios y configuración
- **MANAGER**: Gestión limitada de usuarios
- **USER**: Acceso básico
- **VIEWER**: Solo lectura
- **NONE**: Sin rol asignado (pendiente de aprobación)

### Estados de Usuario (str enum)
- **ACTIVE**: Usuario activo, puede acceder
- **INACTIVE**: Usuario inactivo, no puede acceder
- **SUSPENDED**: Usuario suspendido temporalmente
- **PENDING**: Usuario pendiente de aprobación

### Decoradores de Seguridad
- `get_current_user`: Autenticación básica
- `get_current_active_user`: Usuario activo
- `get_current_admin_user`: Admin o superior
- `get_current_manager_or_admin`: Manager o superior
- `get_current_superadmin_user`: Solo superadmin

## Endpoints Principales

### Autenticación (`/api/v1/auth/`)
- `POST /login`: Login tradicional
- `POST /google`: Google OAuth (recibe access_token)
- `POST /logout`: Cierre de sesión
- `POST /forgot-password`: Recuperación de contraseña
- `POST /reset-password`: Restablecimiento de contraseña

### Usuarios (`/api/v1/users/`)
- `GET /`: Listar usuarios (admin)
- `POST /`: Crear usuario (admin)
- `GET /me`: Perfil actual
- `GET /{id}`: Detalles de usuario (ID int)
- `PUT /{id}`: Actualizar usuario
- `DELETE /{id}`: Eliminar usuario (admin)
- `PATCH /{id}/role`: Cambiar rol (admin)
- `GET /pending`: Lista usuarios pendientes (solo superadmin)

### Sistema (`/health`, `/info`)
- `GET /health`: Estado de conexión a BD
- `GET /info`: Información del sistema

## Flujo de Google OAuth Actualizado

### Implementación con Access Token
1. Frontend obtiene `access_token` de Google OAuth 2.0
2. Frontend envía `access_token` a `/api/v1/auth/google`
3. Backend valida token llamando a `https://www.googleapis.com/oauth2/v3/userinfo`
4. Si el usuario no existe, se crea automáticamente con:
   - Email como identificador principal
   - Username único generado desde email (ej: "usuario", "usuario1", etc.)
   - Rol por defecto: USER
   - Estado: ACTIVE
5. Backend genera JWT interno y establece cookie httpOnly
6. Frontend recibe respuesta y actualiza estado

## Comandos Principales

```bash
# Instalación
poetry install               # Instalar dependencias
poetry shell                 # Activar entorno virtual

# Desarrollo
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Tests
pytest                      # Ejecutar todos los tests
pytest -v                   # Tests verbosos
pytest --cov=app            # Tests con cobertura

# Calidad de código
black .                      # Formatear código
isort .                      # Ordenar imports
flake8 .                     # Linting
mypy .                       # Type checking
```

## Variables de Entorno

### Archivo `.env` requerido:
```bash
# Environment Configuration
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-here-change-in-production

# Database Configuration (Neon PostgreSQL)
PGHOST=ep-xxx.us-east-2.aws.neon.tech
PGPORT=5432
PGDATABASE=your_db_name
PGUSER=your_db_user
PGPASSWORD=your_db_password
PGSCHEMA=public
PGSSLMODE=require

# JWT Settings
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# CORS Settings
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

## Integración con Frontend

### Configuración Next.js
- **Backend URL**: `http://localhost:8001` (configurable en `next.config.ts`)
- **Rewrites**: `/backend/*` → `${BACKEND_URL}/*`
- **CORS**: Orígenes permitidos configurados dinámicamente
- **COOP**: `same-origin-allow-popups` para Google OAuth

### Flujo Google OAuth
1. Frontend obtiene `credential` de Google
2. Envía `credential` a `/api/v1/auth/google`
3. Backend valida token con Google
4. Busca/crea usuario en BD
5. Genera JWT interno y establece cookie httpOnly
6. Frontend recibe respuesta y actualiza estado

## Depuración y Problemas Comunes

### Errores Conocidos
- **400 Bad Request**: Variables de entorno no configuradas
- **CORS**: Orígenes no permitidos en settings
- **COOP**: Política bloqueando popup de Google OAuth
- **TransportError**: Problemas de conexión con servidores Google
- **UUID vs int**: Asegurar consistencia en tipos de ID

### Logs Útiles
- **Startup**: Verificación de conexión a BD y creación de tablas
- **Auth**: Errores de validación de tokens Google
- **CORS**: Orígenes bloqueados en consola del navegador

## Arquitectura SOLID Detallada

### Single Responsibility Principle (SRP)
- **Interfaces**: Cada interface tiene una responsabilidad específica
- **Servicios**: Cada servicio maneja un solo dominio (auth, users, tokens)
- **Repositorios**: Cada repositorio maneja solo una entidad
- **Endpoints**: Cada endpoint maneja una sola operación HTTP

### Open/Closed Principle (OCP)
- **Interfaces**: Abiertas para extensión, cerradas para modificación
- **Servicios**: Se pueden añadir nuevos proveedores OAuth sin modificar código
- **Repositorios**: Se puede cambiar de ORM sin afectar la lógica de negocio

### Liskov Substitution Principle (LSP)
- **Implementaciones**: Cualquier implementación de una interface puede sustituir a otra
- **Repositorios**: UserRepository puede ser sustituido por otro repositorio

### Interface Segregation Principle (ISP)
- **Interfaces Específicas**: ITokenService solo tiene métodos de tokens
- **Clientes**: Cada cliente depende solo de los métodos que necesita

### Dependency Inversion Principle (DIP)
- **Inyección de Dependencias**: FastAPI `Depends()` para inyectar servicios
- **Depende de Abstracciones**: Los servicios dependen de interfaces, no de implementaciones
- **Contenedor DI**: `dependencies.py` centraliza la configuración de dependencias

## Testing Strategy

### Unit Tests
- **Servicios**: Test de lógica de negocio sin dependencias externas
- **Repositorios**: Test de acceso a datos con BD en memoria
- **Interfaces**: Test de contratos con mocks

### Integration Tests
- **Endpoints**: Test de endpoints HTTP con base de datos de prueba
- **OAuth**: Test de flujo de autenticación con Google sandbox

### E2E Tests
- **Flujo Completo**: Test de login tradicional y Google OAuth
- **Permisos**: Test de roles y permisos en endpoints protegidos
