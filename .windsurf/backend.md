# Backend AuthCore - Documentación Actualizada

## 🏗️ Stack Tecnológico Actual

- **Framework**: FastAPI 0.128.0
- **Base de Datos**: PostgreSQL con SQLAlchemy 2.0
- **ORM**: SQLAlchemy 2.0 con Psycopg3 (`psycopg[binary]`) — también incluye psycopg2-binary como fallback
- **Autenticación**: JWT + bcrypt + Google OAuth 2.0
- **Gestión de Dependencias**: Poetry
- **Python**: ^3.10
- **Testing**: pytest con pytest-asyncio
- **Calidad de Código**: black, isort, flake8, mypy, pre-commit

## 📁 Estructura Real del Proyecto

```
backend/
├── app/                    # Código fuente principal
│   ├── api/               # Endpoints API
│   │   ├── route.py       # Router principal (agrupa todos los routers v1)
│   │   └── v1/            # API versión 1
│   │       ├── dependencies.py  # Inyección de dependencias
│   │       └── endpoints/      # Endpoints específicos
│   │           ├── auth/        # Subpaquete de autenticación (SRP)
│   │           │   ├── __init__.py  # Ensambla login_router + google_router
│   │           │   ├── login.py     # POST /login — autenticación tradicional
│   │           │   └── google.py    # GET /google + GET /callback — OAuth
│   │           └── users.py     # Gestión de usuarios (rutas estáticas primero)
│   ├── core/              # Configuración central
│   │   ├── config.py     # Settings con Pydantic
│   │   └── security.py    # JWT y utilidades de seguridad
│   ├── db/                # Base de datos
│   │   └── session.py    # Conexión SQLAlchemy
│   ├── domain/            # Lógica de dominio
│   │   └── user_domain.py # Reglas de negocio de usuarios
│   ├── interfaces/         # Contratos SOLID
│   │   ├── auth/         # Interfaces de autenticación
│   │   └── user/         # Interfaces de usuarios
│   ├── models/            # Modelos SQLAlchemy
│   │   ├── base.py        # Modelo base
│   │   └── user.py        # Modelo User completo
│   ├── repositories/      # Acceso a datos
│   │   └── UserRepository.py  # Repositorio de usuarios (PascalCase)
│   ├── schemas/           # Schemas Pydantic
│   │   ├── auth.py        # Schemas de autenticación
│   │   └── user.py        # Schemas de usuarios
│   ├── services/          # Lógica de negocio (Arquitectura SOLID)
│   │   ├── auth/          # Servicios de autenticación
│   │   │   ├── AuthService.py     # Servicio principal
│   │   │   ├── GoogleOAuthService.py # OAuth Google
│   │   │   └── TokenService.py    # Gestión JWT
│   │   └── user/         # Servicios de usuarios (Refactorizado SRP)
│   │       ├── UserService.py        # Facade principal
│   │       ├── UserValidationService.py # Validaciones y permisos
│   │       ├── UserQueryService.py  # Consultas y estadísticas
│   │       ├── UserUpdateService.py # Actualizaciones de datos
│   │       └── README.md           # Documentación de arquitectura
│   ├── types/             # Tipos personalizados
│   │   └── enums.py       # Enums UserRole, UserStatus
│   └── main.py            # Entry point FastAPI
├── tests/                 # Tests completos
│   ├── conftest.py        # Configuración pytest
│   ├── pytest.ini         # Configuración profesional
│   ├── test_auth_endpoints.py      # Tests endpoints auth
│   ├── test_user_endpoints.py       # Tests endpoints users
│   ├── test_auth_services.py         # Tests servicios auth
│   ├── test_user_services.py         # Tests servicios users
│   ├── test_user_repository.py        # Tests repositorio
│   ├── test_models.py               # Tests modelos
│   ├── test_domain.py               # Tests dominio
│   └── test_main.py               # Tests principales
├── scripts/               # Scripts utilitarios
│   ├── entrypoint.sh      # Entrypoint Docker
│   └── setup.sh           # Setup dev/prod/logs
├── nginx/                 # Configuración Nginx (certs + conf.d)
├── .env                   # Variables de entorno
├── .env.example           # Plantilla de configuración
├── pyproject.toml         # Configuración Poetry + herramientas
├── poetry.lock            # Lock file de dependencias
├── Dockerfile             # Imagen Docker multi-stage
├── docker-compose.yml      # Compose
└── README.md              # Documentación
```

## 🧪 Testing Suite Completa

### Framework de Testing
- **pytest**: Framework principal con async support
- **pytest-asyncio**: Soporte para código asíncrono
- **Cobertura**: 80% mínimo configurado
- **SQLite**: Base de datos aislada para tests
- **Fixtures**: Reutilizables para usuarios, tokens, mocks

### Tests Creados
- **Endpoints Tests**: `test_auth_endpoints.py`, `test_user_endpoints.py`
- **Services Tests**: `test_auth_services.py`, `test_user_services.py`
- **Repository Tests**: `test_user_repository.py`
- **Models Tests**: `test_models.py`
- **Domain Tests**: `test_domain.py`
- **Main Tests**: `test_main.py` para endpoints principales

### Configuración Profesional (`pytest.ini`)
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers --disable-warnings --color=yes --cov=app --cov-report=html --cov-report=term-missing --cov-fail-under=80
markers = unit, integration, slow, auth, users, oauth, security, database
minversion = 6.0
filterwarnings = ignore::DeprecationWarning ignore::PendingDeprecationWarning ignore::UserWarning:sqlalchemy.*
```

## 🔧 Configuración Principal

### FastAPI Application (`main.py`)
- **Lifespan Management**: Startup/shutdown asíncrono
- **Auto-creación de tablas**: Verificación y creación en startup
- **CORS Middleware**: Configuración dinámica por entorno
- **Health Checks**: `/` y `/health` endpoints
- **Documentation**: Swagger UI en `/docs`, ReDoc en `/redoc`

### Settings Inteligentes (`core/config.py`)
- **Pydantic Settings**: Configuración robusta con validación
- **Database URL**: Construcción automática de conexión PostgreSQL
- **CORS Dinámico**: Parseo flexible de orígenes (JSON, CSV, string)
- **Environment Detection**: Desarrollo vs producción
- **Google OAuth**: Configuración de cliente ID/secret

### Modelo de Usuario (`models/user.py`)
```python
class User(Base):
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)  # bcrypt
    full_name = Column(String(100))
    role = Column(Enum(UserRole), default=UserRole.USER)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

## 🚀 Características Principales

### FastAPI 0.128.0
- **API RESTful** con documentación automática (Swagger/ReDoc)
- **Validación de datos** con Pydantic v2
- **Dependency Injection** nativa
- **Async Support** con lifespan management
- **Type Hints** obligatorios
- **Google OAuth 2.0** con flujo popup y aprobación de usuarios

### PostgreSQL
- **SQLAlchemy 2.0** con Psycopg3
- **Connection Pooling** optimizado
- **Schema Isolation** con search_path
- **Auto-migrations** en startup
- **Timezone-aware** timestamps

### 🔐 Seguridad Robusta
- **JWT** con expiración configurable (30 min default)
- **bcrypt** para password hashing
- **Google OAuth 2.0** con validación de access_token
- **Role-based Access Control** (RBAC)
- **httpOnly cookies** + Authorization header
- **CORS** configurable por entorno
- **User Approval System**: Usuarios nuevos de Google requieren aprobación admin

## 🎯 Sistema de Roles y Permisos

### Roles Definidos (UserRole enum)
- **SUPERADMIN**: Control total del sistema
- **ADMIN**: Gestión de usuarios y configuración
- **MANAGER**: Gestión limitada de usuarios
- **USER**: Acceso básico
- **VIEWER**: Solo lectura
- **NONE**: Sin rol asignado

### Estados de Usuario (UserStatus enum)
- **ACTIVE**: Usuario activo con acceso
- **INACTIVE**: Usuario inactivo sin acceso
- **SUSPENDED**: Usuario suspendido temporalmente
- **PENDING**: Usuario pendiente de aprobación (creado por Google OAuth)
- **NONE**: Sin rol asignado (usuarios nuevos de Google OAuth)

### 🔒 Decoradores de Seguridad
- `get_current_user`: Autenticación básica JWT
- `get_current_active_user`: Verifica usuario activo
- `get_current_admin_user`: Admin o superior
- `get_current_manager_or_admin`: Manager o superior
- `get_current_superadmin_user`: Solo superadmin

## 🛣️ Endpoints API

### Autenticación (`/api/v1/auth/`)
- `POST /login`: Login tradicional (username/password)
- `GET /google`: Inicia flujo Google OAuth (redirección)
- `GET /callback`: Procesa callback de Google (HTML con postMessage)
- `POST /logout`: Cierre de sesión

### Usuarios (`/api/v1/users/`)
#### Endpoints Principales
- `GET /`: Listar usuarios (paginado, admin+)
- `POST /`: Crear usuario (admin+)
- `GET /me`: Perfil del usuario actual
- `GET /{id}`: Detalles de usuario por ID
- `PUT /{id}`: Actualizar usuario completo
- `DELETE /{id}`: Eliminar usuario (admin+)

#### Operaciones Específicas
- `PATCH /{id}/role`: Cambiar rol (admin+)
- `PATCH /{id}/status`: Cambiar estado (admin+)
- `PATCH /{id}/lock`: Bloquear/desbloquear usuario (admin+)
- `POST /{id}/notes`: Agregar notas al usuario (admin+)

#### Estadísticas y Reportes
- `GET /pending`: Usuarios pendientes (admin+)
- `GET /by-origin`: Usuarios agrupados por origen (admin+)
- `GET /stats`: Estadísticas de usuarios (admin+)

#### Nuevos Endpoints (Arquitectura Especializada)
- `GET /search`: Búsqueda avanzada de usuarios (admin+)
- `GET /{id}/activity`: Resumen de actividad de usuario (admin+)
- `PATCH /{id}/profile`: Actualización de perfil (campos no sensibles)
- `POST /{id}/reset-password`: Reset de contraseña con validación (admin+)
- `PATCH /bulk-update`: Actualización masiva de usuarios (admin+)

### Sistema (`/`, `/health`)
- `GET /`: Mensaje de bienvenida
- `GET /health`: Estado de conexión a BD
- `GET /docs`: Swagger UI
- `GET /redoc`: ReDoc documentation

## ️ Comandos de Desarrollo

```bash
# Instalación y configuración
poetry install                    # Instalar dependencias
poetry shell                      # Activar entorno virtual

# Crear usuario de prueba
python create_test_user.py --create  # Crear usuario test/test123
python create_test_user.py --list     # Listar usuarios existentes

# Desarrollo
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Tests
pytest                           # Todos los tests
pytest -v                        # Verboso
pytest --cov=app                 # Con cobertura
pytest -m unit                    # Solo unit tests
pytest -m integration            # Solo integration tests

# Calidad de código
black .                          # Formatear
isort .                          # Ordenar imports
flake8 .                         # Linting
mypy .                           # Type checking
pre-commit run --all-files       # Todos los hooks
```

## ⚙️ Variables de Entorno

### Archivo `.env` requerido:
```bash
# Environment
ENVIRONMENT=development
DEBUG=true

SECRET_KEY=your-super-secret-key-change-this-in-production

# Database (PostgreSQL)
PGHOST=localhost
PGPORT=5432
PGDATABASE=authcore
PGUSER=postgres
PGPASSWORD=your_secure_password
PGSCHEMA=public
PGSSLMODE=require
PGCHANNELBINDING=disable

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# CORS (formatos soportados)
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
# o: CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
# o: CORS_ORIGINS="*"

# Google OAuth
GOOGLE_CLIENT_ID=your_google_oauth_client_id
GOOGLE_CLIENT_SECRET=your_google_oauth_client_secret

# Cloudinary (opcional)
CLOUDINARY_CLOUD_NAME=your_cloudinary_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret
```

## 🌌 Integración con Frontend

### Configuración Astro + Svelte
- **Backend URL**: `http://localhost:8001` (configurable via .env)
- **Frontend URL**: `http://localhost:4321` (desarrollo)
- **CORS**: Orígenes permitidos configurados dinámicamente
- **Authentication**: Cookies httpOnly + Authorization header
- **Type Safety**: Schemas compartidos via TypeScript
- **API Config**: `src/config/api.config.ts` como Single Source of Truth

### Flujo de Comunicación
1. **Login**: Frontend → `/api/v1/auth/login` → JWT + cookie
2. **Google OAuth**: Frontend → Google → `/api/v1/auth/google` → `/api/v1/auth/callback` → popup postMessage → JWT + cookie
3. **Protected Routes**: Frontend incluye Authorization header o cookie de sesión
4. **User Profile**: GET `/api/v1/users/me` para datos del usuario
5. **Logout**: POST `/api/v1/auth/logout` para cerrar sesión
6. **New Google Users**: Se crean con rol NONE y estado PENDING, requieren aprobación admin

## 🐛 Depuración y Troubleshooting

### Errores Comunes
- **400 Bad Request**: Variables de entorno faltantes o incorrectas
- **401 Unauthorized**: Token JWT inválido o expirado
- **403 Forbidden**: Permisos insuficientes (rol requerido) o usuario PENDING
- **422 Unprocessable Entity**: Error de validación en endpoints
- **CORS Issues**: Orígenes no configurados en `CORS_ORIGINS`
- **Database Connection**: Credenciales PostgreSQL incorrectas
- **Google OAuth**: Client ID/secret inválidos o token expirado
- **PENDING_APPROVAL**: Nuevo usuario Google espera aprobación de admin

### Logs Útiles para Debug
```bash
# Startup logs - conexión a BD y creación de tablas
🚀 Starting FastAPI app in development mode
✅ Nuevas tablas creadas/detectadas: users

# Auth logs - validación de tokens
❌ Error en DB: connection failed
❌ Token validation failed: invalid_signature

# CORS logs - orígenes bloqueados
WARNING: CORS request blocked: Origin not allowed
```

### Herramientas de Debug
- **Swagger UI**: `http://localhost:8001/docs` para probar endpoints
- **Health Check**: `http://localhost:8001/health` para verificar BD
- **Environment**: Verificar variables en `print(settings.model_dump())`
- **Database**: Conectar a PostgreSQL para verificar datos

## 📦 Dependencias Principales

### Core Dependencies
```python
fastapi = "^0.128.0"           # Web framework
uvicorn = { extras = ["standard"], version = "^0.40.0" }  # ASGI server
sqlalchemy = "^2.0.23"         # ORM
psycopg2-binary = "^2.9.9"     # PostgreSQL driver
pydantic = "^2.12.5"           # Data validation
pydantic-settings = "^2.1.0"   # Settings management
python-dotenv = "^1.0.0"       # Environment variables
```

### Security & Auth
```python
python-jose = { extras = ["cryptography"], version = "^3.5.0" }  # JWT handling
bcrypt = "^5.0.0"              # Password hashing
python-multipart = "^0.0.22"   # Form data
google-auth = "^2.48.0"        # Google OAuth
google-auth-oauthlib = "^1.2.4" # Google OAuth
requests = "^2.32.5"           # HTTP client
requests-oauthlib = "^2.0.0"   # OAuth client
```

### Development & Quality
```python
pytest = "^7.4.0"              # Testing framework
pytest-asyncio = "^0.21.0"    # Async testing
pytest-cov = "^4.1.0"          # Coverage
black = "^23.0.0"               # Code formatter
isort = "^5.12.0"               # Import sorter
flake8 = "^6.0.0"               # Linter
mypy = "^1.5.0"                 # Type checker
pre-commit = "^3.4.0"           # Git hooks
```

## 🏛️ Arquitectura SOLID (Refactorizada 2024)

### **S** - Single Responsibility Principle (Aplicado Estrictamente)
- **UserValidationService**: Única responsabilidad = validaciones y permisos
- **UserQueryService**: Única responsabilidad = consultas y estadísticas
- **UserUpdateService**: Única responsabilidad = actualizaciones de datos
- **UserService**: Patrón Facade = coordinar servicios especializados
- **Interfaces**: Cada interface tiene una responsabilidad específica
- **Repositorios**: Cada repositorio maneja solo una entidad

### **O** - Open/Closed Principle
- **Interfaces**: Abiertas para extensión, cerradas para modificación
- **Servicios Especializados**: Se pueden añadir nuevos métodos sin afectar otros servicios
- **Repositorios**: Se puede cambiar de ORM sin afectar la lógica de negocio
- **Endpoints**: Nuevos endpoints sin modificar existentes

### **L** - Liskov Substitution Principle
- **Implementaciones**: Cualquier implementación de una interface puede sustituir a otra
- **Servicios**: UserQueryService puede ser sustituido por otra implementación de consulta
- **Repositorios**: UserRepository puede ser sustituido por otro repositorio

### **I** - Interface Segregation Principle
- **Interfaces Específicas**: ITokenService solo tiene métodos de tokens
- **Clientes**: Cada cliente depende solo de los métodos que necesita
- **Servicios Especializados**: Interfaces específicas para cada tipo de operación

### **D** - Dependency Inversion Principle
- **Inyección de Dependencias**: FastAPI `Depends()` para inyectar servicios
- **Depende de Abstracciones**: Los servicios dependen de interfaces, no de implementaciones
- **Contenedor DI**: `dependencies.py` centraliza la configuración de dependencias
- **Servicios Especializados**: Inyectados en UserService principal

### 🎯 Patrones de Diseño Aplicados
- **Facade Pattern**: UserService como fachada unificada
- **Strategy Pattern**: Diferentes estrategias de validación
- **Repository Pattern**: Abstracción de acceso a datos
- **Dependency Injection**: Inversión de control con FastAPI

## 🎯 Estado Actual del Proyecto

### ✅ Completamente Implementado
- ✅ **Backend**: FastAPI con PostgreSQL completo y optimizado
- ✅ **Autenticación**: Login tradicional + Google OAuth 2.0 con PENDING_APPROVAL
- ✅ **Gestión de Usuarios**: CRUD completo con roles, permisos y validaciones SOLID
- ✅ **Seguridad**: JWT, bcrypt, RBAC, CORS dinámico y validaciones robustas
- ✅ **Arquitectura SOLID**: Servicios especializados con SRP estricto (4 servicios User)
- ✅ **Testing**: Suite completa profesional con 80%+ cobertura y fixtures
- ✅ **Calidad**: black, isort, flake8, mypy, pre-commit configurados
- ✅ **Docker**: Multi-stage builds optimizado para producción y desarrollo
- ✅ **Documentación**: Swagger UI + READMEs completos para servicios y endpoints
- ✅ **Endpoints Avanzados**: Búsqueda, actividad, perfiles, actualizaciones masivas
- ✅ **Configuración Centralizada**: URLs dinámicas sin rutas quemadas
- ✅ **Frontend Integrado**: Dashboard real con datos dinámicos y TypeScript sin errores
- ✅ **Environment Variables**: Configuración robusta con FRONTEND_ORIGIN y BACKEND_URL
- ✅ **OAuth Optimizado**: Flujo Google OAuth con manejo completo de PENDING_APPROVAL
- ✅ **CORS Dinámico**: Parseo flexible de orígenes (JSON, CSV, string)
- ✅ **Error Handling**: 401 redirects consistentes y manejo robusto de errores
- ✅ **Multi-tenant Ready**: Estructura preparada para multi-tenant con JSONB
- ✅ **Performance**: Queries optimizadas y conexión pooling eficiente

### 🔧 Mejoras Recientes (Críticas)
- ✅ **Refactorización SOLID Completa**: UserService dividido en 4 servicios especializados (SRP estricto)
- ✅ **Nuevos Endpoints Especializados**: Búsqueda, actividad, perfil, reset password, bulk update
- ✅ **Schemas Mejorados**: Nuevos schemas Pydantic para validación robusta y type safety
- ✅ **Optimización de Endpoints**: Uso directo de servicios especializados (mejor rendimiento)
- ✅ **Documentación Completa**: README detallado para servicios y endpoints
- ✅ **Configuración Centralizada**: URLs dinámicas sin rutas quemadas en todo el proyecto
- ✅ **Tests Completos**: Suite enterprise-ready con pytest, fixtures y mocks
- ✅ **Frontend Conectado**: Dashboard real con datos dinámicos y sin errores TypeScript
- ✅ **Environment Variables**: Configuración robusta con FRONTEND_ORIGIN y BACKEND_URL
- ✅ **OAuth Optimizado**: Flujo Google OAuth con manejo de PENDING_APPROVAL
- ✅ **CORS Dinámico**: Parseo flexible de orígenes (JSON, CSV, string)
- ✅ **Error Handling**: 401 redirects consistentes en todo el frontend
- ✅ **Multi-tenant Schema**: Estructura de base de datos preparada para multi-tenant
- ✅ **Performance Optimization**: Queries N+1 eliminados y connection pooling mejorado
- ✅ **Security Hardening**: Validaciones adicionales y sanitización de inputs

### 🔄 En Desarrollo
- 🔄 **Analytics Engine**: Métricas de uso del sistema con dashboards especializados
- 🔄 **Audit Logging**: Logs detallados de acciones administrativas con trazabilidad
- 🔄 **Performance Monitoring**: Health checks avanzados y métricas en tiempo real
- 🔄 **Email Notifications**: Sistema de notificaciones para usuarios pendientes y eventos
- 🔄 **WebSocket Integration**: Comunicación real-time para dashboard y notificaciones
- 🔄 **Cache Layer**: Redis integration para endpoints frecuentes

### 🚀 Próximas Features
- 🚀 **Multi-tenant Production**: Aislamiento completo por organización con subdominios
- � **2FA Integration**: Autenticación de dos factores con TOTP y SMS
- � **SSO Expansion**: Microsoft, GitHub, LinkedIn OAuth providers
- � **API Rate Limiting**: Límites por usuario con Redis y algoritmos de token bucket
- � **Webhooks Engine**: Integraciones externas con eventos y retry logic
- � **Frontend Testing Suite**: Vitest + Testing Library + Playwright E2E
- 🚀 **Microservices Migration**: Desacoplamiento progresivo a microservicios
- 🚀 **GraphQL API**: Endpoint GraphQL alternativo con subscriptions
- 🚀 **Mobile App**: React Native para iOS y Android
- 🚀 **AI Features**: ML para detección de anomalías y recomendaciones

---

**AuthCore Backend** - API RESTful moderna, segura y escalable. 🚀
