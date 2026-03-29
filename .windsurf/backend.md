# Backend AuthCore - Resumen Técnico

## 🏗️ Stack Tecnológico

- **Framework**: FastAPI 0.128.0
- **Base de Datos**: PostgreSQL con SQLAlchemy 2.0
- **ORM**: SQLAlchemy 2.0 con Psycopg3
- **Autenticación**: JWT + bcrypt + Google OAuth 2.0
- **Gestión de Dependencias**: Poetry
- **Python**: ^3.10
- **Testing**: pytest con pytest-asyncio
- **Calidad de Código**: black, isort, flake8, mypy, pre-commit

## 📁 Estructura del Proyecto

```
backend/
├── app/                    # Código fuente principal
│   ├── api/               # Endpoints API
│   │   ├── route.py       # Router principal
│   │   └── v1/            # API versión 1
│   │       ├── dependencies.py  # Inyección de dependencias
│   │       └── endpoints/      # Endpoints específicos
│   │           ├── auth.py      # Autenticación (login, Google OAuth)
│   │           ├── users.py     # Gestión de usuarios
│   │           └── auth/       # Módulos de auth
│   ├── core/              # Configuración central
│   │   └── config.py     # Settings con Pydantic
│   ├── db/                # Base de datos
│   │   └── session.py    # Conexión SQLAlchemy
│   ├── domain/            # Lógica de dominio
│   ├── interfaces/        # Contratos SOLID
│   ├── models/            # Modelos SQLAlchemy
│   │   ├── base.py        # Modelo base
│   │   └── user.py        # Modelo User completo
│   ├── repositories/      # Acceso a datos
│   ├── schemas/           # Schemas Pydantic
│   │   ├── auth.py        # Schemas de autenticación
│   │   └── user.py        # Schemas de usuario
│   ├── services/          # Lógica de negocio
│   │   ├── auth_service.py # Servicio principal de auth
│   │   ├── user_service.py # Gestión de usuarios
│   │   ├── auth/          # Servicios de auth
│   │   └── user/          # Servicios de usuarios
│   ├── types/             # Tipos personalizados
│   │   └── enums.py       # Enums UserRole, UserStatus
│   └── main.py            # Entry point FastAPI
├── tests/                 # Tests unitarios e integración
├── scripts/               # Scripts utilitarios
├── .env                   # Variables de entorno
├── .env.example           # Plantilla de configuración
├── create_test_user.py    # Script para crear usuario de prueba
├── pyproject.toml         # Configuración Poetry
├── poetry.lock            # Lock file de dependencias
├── Dockerfile             # Imagen Docker
├── docker-compose.yml     # Compose
└── README.md              # Documentación
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

### 🏗️ Arquitectura Limpia
- **Domain-Driven Design** con separación clara
- **SOLID Principles** en toda la arquitectura
- **Dependency Injection** con interfaces
- **Repository Pattern** para acceso a datos
- **Service Layer** para lógica de negocio

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
- **PENDING**: Usuario pendiente de aprobación

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
- `POST /refresh`: Refresh token JWT
- `POST /forgot-password`: Recuperación de contraseña
- `POST /reset-password`: Restablecimiento de contraseña

### Usuarios (`/api/v1/users/`)
- `GET /`: Listar usuarios (paginado, admin+)
- `POST /`: Crear usuario (admin+)
- `GET /me`: Perfil del usuario actual
- `GET /{id}`: Detalles de usuario por ID
- `PUT /{id}`: Actualizar usuario completo
- `PATCH /{id}`: Actualización parcial
- `DELETE /{id}`: Eliminar usuario (admin+)
- `PATCH /{id}/role`: Cambiar rol (admin+)
- `GET /pending`: Usuarios pendientes (superadmin)

### Sistema (`/`, `/health`)
- `GET /`: Mensaje de bienvenida
- `GET /health`: Estado de conexión a BD
- `GET /docs`: Swagger UI
- `GET /redoc`: ReDoc documentation

## 🔁 Flujo de Autenticación

### Login Tradicional
1. Usuario envía `username` y `password` a `/api/v1/auth/login`
2. Backend valida credenciales contra BD con bcrypt
3. Genera JWT token con claims del usuario
4. Retorna token y datos del usuario
5. Frontend guarda token y redirige al dashboard

### Google OAuth 2.0 con Popup
1. **Frontend**: Usuario hace clic en "Continuar con Google"
2. **Popup**: Se abre ventana con `GET /api/v1/auth/google`
3. **Backend**: Redirige a Google OAuth
4. **Google**: Usuario autoriza en popup
5. **Google**: Redirige a `http://localhost:4321/api/v1/auth/callback?code=xxx`
6. **Frontend**: Callback redirige a `http://localhost:8001/api/v1/auth/callback?code=xxx`
7. **Backend**: Intercambia código por access_token, obtiene userinfo
8. **Backend**: Crea/actualiza usuario, genera JWT interno
9. **Backend**: Responde con HTML que cierra popup y envía datos via postMessage
10. **Frontend**: Recibe AUTH_SUCCESS, guarda usuario, redirige a dashboard

## 🛠️ Comandos de Desarrollo

```bash
# Instalación y configuración
poetry install                    # Instalar dependencias
poetry shell                      # Activar entorno virtual

# Crear usuario de prueba
python create_test_user.py --create  # Crear usuario test/test123
python create_test_user.py --list     # Listar usuarios existentes

# Desarrollo
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
# o
poetry run gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

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
SECRET_KEY=your-secret-key-here-change-in-production

# Database (PostgreSQL)
PGHOST=localhost
PGPORT=5432
PGDATABASE=authcore
PGUSER=postgres
PGPASSWORD=your_password
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
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Cloudinary (opcional)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

## 🔌 Integración con Frontend

### Configuración Astro + Svelte
- **Backend URL**: `http://localhost:8001` (configurable)
- **CORS**: Orígenes permitidos configurados dinámicamente
- **Authentication**: Cookies httpOnly + Authorization header
- **Type Safety**: Schemas compartidos via TypeScript

### Flujo de Comunicación
1. **Login**: Frontend → `/api/v1/auth/login` → JWT + cookie
2. **Google OAuth**: Frontend → Google → `/api/v1/auth/google` → JWT + cookie
3. **Protected Routes**: Frontend incluye Authorization header
4. **User Profile**: GET `/api/v1/users/me` para datos del usuario
5. **Logout**: POST `/api/v1/auth/logout` para cerrar sesión

## 🐛 Depuración y Troubleshooting

### Errores Comunes
- **400 Bad Request**: Variables de entorno faltantes o incorrectas
- **401 Unauthorized**: Token JWT inválido o expirado
- **403 Forbidden**: Permisos insuficientes (rol requerido)
- **CORS Issues**: Orígenes no configurados en `CORS_ORIGINS`
- **Database Connection**: Credenciales PostgreSQL incorrectas
- **Google OAuth**: Client ID/secret inválidos o token expirado

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

## 🏛️ Arquitectura SOLID Detallada

### **S** - Single Responsibility Principle
- **Interfaces**: Cada interface tiene una responsabilidad específica
- **Servicios**: Cada servicio maneja un solo dominio (auth, users, tokens)
- **Repositorios**: Cada repositorio maneja solo una entidad
- **Endpoints**: Cada endpoint maneja una sola operación HTTP

### **O** - Open/Closed Principle
- **Interfaces**: Abiertas para extensión, cerradas para modificación
- **Servicios**: Se pueden añadir nuevos proveedores OAuth sin modificar código
- **Repositorios**: Se puede cambiar de ORM sin afectar la lógica de negocio

### **L** - Liskov Substitution Principle
- **Implementaciones**: Cualquier implementación de una interface puede sustituir a otra
- **Repositorios**: UserRepository puede ser sustituido por otro repositorio

### **I** - Interface Segregation Principle
- **Interfaces Específicas**: ITokenService solo tiene métodos de tokens
- **Clientes**: Cada cliente depende solo de los métodos que necesita

### **D** - Dependency Inversion Principle
- **Inyección de Dependencias**: FastAPI `Depends()` para inyectar servicios
- **Depende de Abstracciones**: Los servicios dependen de interfaces, no de implementaciones
- **Contenedor DI**: `dependencies.py` centraliza la configuración de dependencias

## 🧪 Testing Strategy

### Unit Tests
```bash
# Tests de lógica de negocio sin dependencias externas
pytest tests/unit/test_services.py
pytest tests/unit/test_repositories.py
```
- **Servicios**: Test de lógica de negocio con mocks
- **Repositorios**: Test de acceso a datos con BD en memoria
- **Interfaces**: Test de contratos con implementaciones falsas

### Integration Tests
```bash
# Tests de endpoints HTTP con base de datos real
pytest tests/integration/test_auth.py
pytest tests/integration/test_users.py
```
- **Endpoints**: Test de endpoints API con BD de prueba
- **OAuth**: Test de flujo de autenticación con Google sandbox
- **Database**: Test de migraciones y modelos

### E2E Tests
```bash
# Tests de flujo completo
pytest tests/e2e/test_full_auth_flow.py
```
- **Flujo Completo**: Login tradicional + Google OAuth con popup
- **Permisos**: Verificación de roles en endpoints protegidos
- **Sesiones**: Gestión de tokens y localStorage

### Scripts de Testing
- **create_test_user.py**: Creación de usuarios de prueba
- **test_oauth.md**: Checklist completo de testing OAuth
- **GOOGLE_OAUTH_SETUP.md**: Guía de configuración y testing

### Configuración de Tests
- **pytest.ini**: Configuración de markers y opciones
- **conftest.py**: Fixtures para BD y clientes HTTP
- **test_db.py**: Base de datos de testing aislada
- **Coverage**: Configurado para excluir tests y migrations

## 📦 Dependencias Principales

### Core Dependencies
```python
fastapi = "^0.128.0"           # Web framework
uvicorn = "^0.40.0"            # ASGI server
sqlalchemy = "^2.0.23"         # ORM
psycopg2-binary = "^2.9.9"     # PostgreSQL driver
pydantic = "^2.12.5"           # Data validation
pydantic-settings = "^2.1.0"   # Settings management
```

### Security & Auth
```python
python-jose = "^3.5.0"         # JWT handling
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
black = "^23.0.0"               # Code formatter
isort = "^5.12.0"               # Import sorter
flake8 = "^6.0.0"               # Linter
mypy = "^1.5.0"                 # Type checker
pre-commit = "^3.4.0"           # Git hooks
```
