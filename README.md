# AuthCore - Sistema de Autenticación y Gestión de Usuarios

## 🚀 Visión General

AuthCore es un sistema completo de autenticación y gestión de usuarios construido con **FastAPI + Astro + Svelte 5**, siguiendo principios **SOLID** y arquitectura moderna. Proporciona autenticación tradicional, Google OAuth 2.0, gestión de roles, **multi-tenant** (organizaciones con selección de tenant) y un dashboard administrativo totalmente funcional.

## 🏗️ Stack Tecnológico

### Backend (FastAPI)
- **Framework**: FastAPI 0.128.0 con Python 3.10+ (pyproject `^3.10`; runtime y Docker en 3.12)
- **Base de Datos**: PostgreSQL con SQLAlchemy 2.0
- **ORM**: SQLAlchemy 2.0 con Psycopg3
- **Autenticación**: JWT + bcrypt + Google OAuth 2.0
- **Arquitectura**: SOLID con inyección de dependencias
- **Testing**: pytest con pytest-asyncio
- **Calidad**: black, isort, flake8, mypy, pre-commit

### Frontend (Astro + Svelte 5)
- **Framework**: Astro 6.1.1 con Islands Architecture
- **UI Framework**: Svelte 5.55.0 (Runes: $state, $derived, onclick)
- **Styling**: TailwindCSS 4.2.2
- **TypeScript**: 5.9.3 con tipado fuerte
- **Package Manager**: pnpm
- **Componentes**: Reutilizables y tipados

## 🎯 Características Principales

### 🔐 Sistema de Autenticación
- **Login Tradicional**: Username/password con JWT
- **Google OAuth 2.0**: Flujo popup con aprobación automática
- **Sesión Segura**: Cookies httpOnly + Authorization header
- **CORS**: Configuración dinámica por entorno
- **User Approval**: Usuarios nuevos de Google requieren aprobación admin

### 👥 Gestión de Usuarios
- **Roles**: SUPERADMIN, ADMIN, MANAGER, USER, VIEWER, NONE
- **Estados**: ACTIVE, INACTIVE, SUSPENDED, PENDING
- **CRUD Completo**: Crear, leer, actualizar, eliminar usuarios
- **Filtros**: Por rol, estado, origen, búsqueda
- **Búsqueda/Actividad**: `GET /users/search` y `GET /users/{id}/activity`
- **Aprobación**: Panel dedicado para usuarios pendientes

### 🏢 Multi-tenant
- **Tenants**: CRUD de organizaciones (`/api/v1/tenants`) con módulos asignados
- **Módulos**: Catálogo `/api/v1/modules` y asignación por tenant (`/api/v1/tenant-modules`)
- **Asignaciones**: `GET /api/v1/users/me/tenants` y `POST /api/v1/users/select-tenant`
- **Selección de tenant**: pantalla `/select-tenant` tras el login de usuario normal
- **SUPERADMIN**: ve y gestiona todos los tenants (bypass en asignaciones)
- **Perfil de empresa**: `/api/v1/company` (perfil propio y de otros usuarios)

### 📊 Dashboard Administrativo
- **Panel Principal**: Estadísticas en tiempo real
- **Gestión de Usuarios**: Tabla con filtros funcionales
- **Usuarios Pendientes**: Aprobar/rechazar con un click
- **Orígenes**: Usuarios agrupados por proyecto/origen
- **Detalle de Usuario**: Edición completa con validaciones

### 🛡️ Seguridad
- **JWT**: RS256, expiración configurable (120 min default, `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **JWKS**: Clave pública en `GET /.well-known/jwks.json`
- **bcrypt**: Password hashing seguro
- **RBAC**: Role-based Access Control
- **Validaciones**: Inyección SQL, XSS, CSRF
- **Rate Limiting**: Intentos de login fallidos

## 📁 Estructura del Proyecto

```
authCore/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── api/v1/            # Endpoints (auth, users, tenants, modules, company)
│   │   ├── core/               # Configuración
│   │   ├── domain/             # Lógica de dominio
│   │   ├── interfaces/          # Contratos SOLID
│   │   ├── models/             # Modelos SQLAlchemy
│   │   ├── repositories/        # Acceso a datos
│   │   ├── schemas/            # Schemas Pydantic
│   │   ├── services/           # Lógica de negocio (query/update/validation por dominio)
│   │   └── types/             # Enums y tipos
│   ├── tests/                 # Tests unitarios e integración
│   └── pyproject.toml         # Dependencias Poetry
├── frontend/                  # Astro + Svelte Frontend
│   ├── src/
│   │   ├── components/         # Componentes reutilizables
│   │   ├── config/            # Configuración API
│   │   ├── layouts/           # Layouts Astro
│   │   ├── pages/             # Rutas Astro
│   │   ├── services/          # Servicios cliente
│   │   ├── styles/            # Estilos TailwindCSS
│   │   ├── utils/             # Utilidades (jwt, guards, auth.roles)
│   │   └── middleware.ts      # Auth de rutas (cookie access_token)
│   ├── tests/                 # 9 suites vitest (107 tests)
│   ├── astro.config.mjs        # Configuración Astro
│   └── package.json          # Dependencias pnpm
├── openspec/                  # Cambios OpenSpec (changes/, specs/)
├── odd/                       # Documentos de features (ODD)
├── scripts/                   # Operación (deploy.sh)
└── README.md                  # Este archivo
```

## 🚀 Quick Start

### Prerrequisitos
- **Python**: 3.10+ con Poetry instalado (pyproject `^3.10`; el proyecto corre en 3.12)
- **Node.js**: 22.12.0+ con pnpm
- **PostgreSQL**: Base de datos configurada

### Backend Setup
```bash
cd backend
poetry install                    # Instalar dependencias
poetry shell                      # Activar entorno

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# Iniciar servidor
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Frontend Setup
```bash
cd frontend
pnpm install                    # Instalar dependencias

# Configurar variables de entorno (URL del backend para el navegador)
echo "PUBLIC_BACKEND_URL=http://localhost:8001" > .env.local

# Iniciar servidor
pnpm dev                        # http://localhost:4321
```

### Acceso Rápido
- **Frontend**: http://localhost:4321
- **Backend API**: http://localhost:8001
- **Documentación**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health

## 🔐 Usuarios de Prueba

- El repo no incluye un seed de usuarios: créalos con `POST /api/v1/users/` o regístralos vía Google OAuth
- Los usuarios nuevos de Google se crean con rol `NONE` y estado `PENDING`
- Requieren aprobación de un administrador

### Google OAuth
- Configura `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET` en `backend/.env`

## 🎯 Flujo de Usuario

### 1. Login Tradicional
1. Ingresar username/password
2. `POST /api/v1/auth/login` valida en backend
3. Generación de JWT (RS256, 120 min)
4. El token se devuelve en JSON — **no** se setea cookie en este endpoint

### 2. Google OAuth
1. Click en "Iniciar con Google"
2. Redirect a `GET /api/v1/auth/google` (popup/redirect OAuth)
3. Autorización y `GET /api/v1/auth/callback`
4. Si es usuario nuevo → estado PENDING (redirect a `/login?status=pending`)
5. Si existe → setea cookie httpOnly `access_token` (120 min)
6. Redirección: SUPERADMIN → `/dashboard`, resto → `/select-tenant` (destinos externos reciben `?token=`)

### 3. Dashboard Administrativo
1. **Panel Principal**: Estadísticas generales
2. **Usuarios**: Lista completa con filtros
3. **Pendientes**: Aprobar/rechazar usuarios
4. **Orígenes**: Usuarios por proyecto
5. **Detalle**: Edición individual de usuarios

## 🛡️ Sistema de Roles y Permisos

### Jerarquía de Roles
```
SUPERADMIN  ⬆️  Control total
ADMIN       ⬆️  Gestión de usuarios y configuración
MANAGER     ⬆️  Gestión limitada de usuarios
USER        ⬆️  Acceso básico
VIEWER      ⬆️  Solo lectura
NONE        ⬆️  Sin rol (usuarios nuevos de Google)
```

### Permisos por Rol
- **SUPERADMIN**: Todo el sistema
- **ADMIN**: CRUD usuarios, cambiar roles/estados
- **MANAGER**: Ver usuarios, cambiar roles básicos
- **USER**: Solo perfil propio
- **VIEWER**: Solo lectura
- **NONE**: Sin acceso (requiere aprobación)

## 🎨 Diseño y UX

### Dark Theme
- Paleta de colores consistente modo oscuro
- Alto contraste para accesibilidad
- Indicadores visuales claros

### Responsive Design
- Mobile-first approach
- Adaptación a todos los dispositivos
- Touch-friendly interactions

### Componentes Reutilizables
- **Icon**: Sistema centralizado de SVG
- **UserAvatar**: Iniciales o imagen
- **Badges**: Rol, estado, origen
- **StatsCard**: Métricas visuales

## 🧪 Testing

### Backend Tests
```bash
cd backend
python -m pytest                   # Suite completa (227 tests) — usar `python -m pytest`, no `pytest` suelto
python -m pytest -v                # Verboso
python -m pytest tests/test_domain.py  # Un módulo
python -m pytest -m unit           # Unit tests
python -m pytest -m integration    # Integration tests
```
- Gate de cobertura **activo**: `--cov-fail-under=80` en `backend/pyproject.toml` (addopts); cualquier run ya mide cobertura.
- Cobertura actual: **86.22%** (227 tests, 0 skipped).

### Frontend Tests
```bash
cd frontend
pnpm test:run                      # Vitest en una pasada (107 tests / 9 suites)
pnpm test                          # Vitest en watch
```
- Suites en `frontend/tests/` (middleware, login, authService, componentes, utils).
- E2E (Playwright): pendiente de implementar.

## 📦 Endpoints API Principales

### Autenticación
- `POST /api/v1/auth/login` - Login tradicional (devuelve token en JSON, sin cookie)
- `GET /api/v1/auth/google` - Iniciar OAuth
- `GET /api/v1/auth/callback` - Callback OAuth (setea cookie httpOnly `access_token`)
- `POST /api/v1/auth/dev-login` - Login rápido de desarrollo (403 en producción)

### Usuarios
- `GET /api/v1/users/` - Listar usuarios
- `POST /api/v1/users/` - Crear usuario
- `GET /api/v1/users/me` - Perfil actual
- `GET /api/v1/users/{id}` - Detalle usuario
- `PUT /api/v1/users/{id}` - Actualizar usuario
- `DELETE /api/v1/users/{id}` - Eliminar usuario
- `PATCH /api/v1/users/{id}/role` - Cambiar rol
- `PATCH /api/v1/users/{id}/status` - Cambiar estado

### Estadísticas
- `GET /api/v1/users/stats` - Estadísticas generales
- `GET /api/v1/users/pending` - Usuarios pendientes
- `GET /api/v1/users/by-origin` - Usuarios por origen
- `GET /api/v1/users/search` - Búsqueda de usuarios
- `GET /api/v1/users/{id}/activity` - Resumen de actividad de un usuario

### Multi-tenant
- `GET/POST/PUT/DELETE /api/v1/tenants/` - CRUD de tenants (más `GET /tenants/by-slug/{slug}`)
- `GET/POST/PUT/DELETE /api/v1/modules/` - Catálogo de módulos
- `GET/POST/PUT/DELETE /api/v1/tenant-modules/tenants/{id}/modules` - Módulos por tenant
- `GET /api/v1/users/me/tenants` - Tenants del usuario actual
- `POST /api/v1/users/select-tenant` - Seleccionar tenant (devuelve token con tenant)

### Empresa y claves
- `GET/PUT /api/v1/company/me` - Perfil de empresa propio (además de `/company/`, `/company/{user_id}`)
- `GET /.well-known/jwks.json` - JWKS (clave pública RS256)

> El cierre de sesión lo maneja el frontend (`/logout` borra la cookie `access_token`).

## 🌐 Despliegue

### Desarrollo
- **Frontend**: `http://localhost:4321` (Astro dev)
- **Backend**: `http://localhost:8001` (FastAPI dev)
- **Base de Datos**: PostgreSQL local

### Producción
- **Frontend**: Vercel (Astro build)
- **Backend**: Docker + Dokploy en Hetzner VPS
- **Base de Datos**: PostgreSQL Nativo en VPS
- **Dominio**: Hostalia + Cloudflare DNS

### Variables de Entorno
```bash
# Backend
ENVIRONMENT=production
SECRET_KEY=tu-secreto-produccion
PGHOST=tu-host-postgres
PGDATABASE=authcore
PGUSER=tu-usuario
PGPASSWORD=tu-password
BACKEND_URL=https://tu-backend.com
FRONTEND_ORIGIN=https://tu-frontend.com
# Rate limiting (slowapi): por defecto "memory://" (dev/test sin Redis).
# En producción, apuntar al servicio Redis de compose:
RATELIMIT_STORAGE_URI=redis://redis:6379

# Frontend  
PUBLIC_BACKEND_URL=https://tu-backend.com  # URL del backend para el navegador
# En Docker/SSR: API_TARGET=http://backend:8000
# Middleware: SITE_ORIGIN=https://tu-frontend.com
```

## 🔧 Configuración Avanzada

### CORS Dinámico
```bash
# Múltiples formatos soportados
CORS_ORIGINS=["https://tudominio.com", "https://app.tudominio.com"]
CORS_ORIGINS=https://tudominio.com,https://app.tudominio.com
CORS_ORIGINS="*"
```

### Google OAuth 2.0
1. Crear proyecto en Google Cloud Console
2. Configurar OAuth 2.0 Client ID
3. Añadir URLs de callback:
   - Desarrollo: `http://localhost:4321/api/v1/auth/callback`
   - Producción: `https://tudominio.com/api/v1/auth/callback`

## 🏛️ Arquitectura SOLID

### **S** - Single Responsibility Principle
- **Interfaces**: Cada interface tiene una responsabilidad específica
- **Servicios**: Cada servicio maneja un solo dominio
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

## 📈 Estado Actual del Proyecto

### ✅ Completamente Implementado
- ✅ **Backend**: FastAPI con PostgreSQL completo
- ✅ **Frontend**: Astro + Svelte 5 con dashboard
- ✅ **Autenticación**: Login tradicional + Google OAuth
- ✅ **Multi-tenant**: Tenants, módulos, asignaciones y switching
- ✅ **Gestión de Usuarios**: CRUD completo con roles
- ✅ **Dashboard**: Panel administrativo funcional
- ✅ **Seguridad**: JWT, bcrypt, CORS, validaciones
- ✅ **Arquitectura**: SOLID con inyección de dependencias
- ✅ **Testing**: 227 tests backend / 107 frontend, cobertura 86.22% (gate 80% activo)
- ✅ **Documentación**: Swagger UI + README completo

### 🔄 En Desarrollo
- 🔄 **E2E**: Tests end-to-end con Playwright
- 🔄 **Analytics**: Métricas de uso del sistema
- 🔄 **Auditoría**: Logs de acciones administrativas
- 🔄 **Notificaciones**: Email para usuarios pendientes

### 🚀 Próximas Features
- 🔄 **2FA**: Autenticación de dos factores
- 🔄 **SSO Additional**: Microsoft, GitHub OAuth
- 🔄 **API Rate Limiting**: Límites por usuario
- 🔄 **Webhooks**: Integraciones externas

## 🤝 Contribución

### Desarrollo Local
```bash
# Clonar repositorio
git clone <repository-url>
cd authCore

# Setup backend
cd backend
poetry install
poetry shell

# Setup frontend (nueva terminal)
cd frontend
pnpm install

# Iniciar servicios
# Backend: poetry run uvicorn app.main:app --reload --port 8001
# Frontend: pnpm dev --port 4321
```

### Code Quality
```bash
# Backend
black .                          # Formatear código
isort .                          # Ordenar imports
flake8 .                         # Linting
mypy .                           # Type checking
python -m pytest                 # Tests con cobertura (gate 80%)

# Frontend
pnpm test:run                    # Tests vitest
pnpm build                       # Build producción
```

## 📄 Licencia

Este proyecto está licenciado bajo MIT License - ver archivo [LICENSE](LICENSE) para detalles.

## 📞 Soporte

Para soporte técnico:
- **Documentación**: Ver archivos en `.windsurf/`
- **Issues**: Crear issue en el repositorio
- **Wiki**: Documentación detallada de arquitectura

---

**AuthCore** - Sistema de autenticación moderno, seguro y escalable. 🚀
