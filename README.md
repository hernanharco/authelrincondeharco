# AuthCore - Sistema de Autenticación y Gestión de Usuarios

## 🚀 Visión General

AuthCore es un sistema completo de autenticación y gestión de usuarios construido con **FastAPI + Astro + Svelte 5**, siguiendo principios **SOLID** y arquitectura moderna. Proporciona autenticación tradicional, Google OAuth 2.0, gestión de roles y un dashboard administrativo totalmente funcional.

## 🏗️ Stack Tecnológico

### Backend (FastAPI)
- **Framework**: FastAPI 0.128.0 con Python 3.10+
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
- **Aprobación**: Panel dedicado para usuarios pendientes

### 📊 Dashboard Administrativo
- **Panel Principal**: Estadísticas en tiempo real
- **Gestión de Usuarios**: Tabla con filtros funcionales
- **Usuarios Pendientes**: Aprobar/rechazar con un click
- **Orígenes**: Usuarios agrupados por proyecto/origen
- **Detalle de Usuario**: Edición completa con validaciones

### 🛡️ Seguridad
- **JWT**: Expiración configurable (30 min default)
- **bcrypt**: Password hashing seguro
- **RBAC**: Role-based Access Control
- **Validaciones**: Inyección SQL, XSS, CSRF
- **Rate Limiting**: Intentos de login fallidos

## 📁 Estructura del Proyecto

```
authCore/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── api/v1/            # Endpoints API
│   │   ├── core/               # Configuración
│   │   ├── domain/             # Lógica de dominio
│   │   ├── interfaces/          # Contratos SOLID
│   │   ├── models/             # Modelos SQLAlchemy
│   │   ├── repositories/        # Acceso a datos
│   │   ├── services/           # Lógica de negocio
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
│   │   └── utils/             # Utilidades
│   ├── astro.config.mjs        # Configuración Astro
│   └── package.json          # Dependencias pnpm
└── README.md                  # Este archivo
```

## 🚀 Quick Start

### Prerrequisitos
- **Python**: 3.10+ con Poetry instalado
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

# Crear usuario de prueba
python create_test_user.py --create

# Iniciar servidor
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Frontend Setup
```bash
cd frontend
pnpm install                    # Instalar dependencias

# Configurar variables de entorno
echo "PUBLIC_GOOGLE_CLIENT_ID=tu_google_client_id" > .env.local

# Iniciar servidor
pnpm dev                        # http://localhost:4321
```

### Acceso Rápido
- **Frontend**: http://localhost:4321
- **Backend API**: http://localhost:8001
- **Documentación**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health

## 🔐 Credenciales de Prueba

### Usuario Administrador
- **Username**: `testuser`
- **Password**: `testpass`
- **Rol**: ADMIN

### Google OAuth
- Configura `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET` en `.env`
- Los usuarios nuevos de Google se crean con rol `NONE` y estado `PENDING`
- Requieren aprobación de un administrador

## 🎯 Flujo de Usuario

### 1. Login Tradicional
1. Ingresar username/password
2. Validación en backend
3. Generación de JWT
4. Almacenamiento en cookie httpOnly
5. Redirección al dashboard

### 2. Google OAuth
1. Click en "Iniciar con Google"
2. Popup de Google OAuth
3. Autorización y callback
4. Si es usuario nuevo → estado PENDING
5. Si existe → login directo
6. Almacenamiento de credenciales

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
pytest                           # Todos los tests
pytest -v                        # Verboso
pytest --cov=app                 # Con cobertura
pytest -m unit                    # Unit tests
pytest -m integration            # Integration tests
```

### Frontend Tests
```bash
cd frontend
# Tests de componentes (pendiente de implementación)
npm test                          # Unit tests
npm run test:e2e                  # E2E tests con Playwright
```

## 📦 Endpoints API Principales

### Autenticación
- `POST /api/v1/auth/login` - Login tradicional
- `GET /api/v1/auth/google` - Iniciar OAuth
- `GET /api/v1/auth/callback` - Callback OAuth
- `POST /api/v1/auth/logout` - Cerrar sesión

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

## 🌐 Despliegue

### Desarrollo
- **Frontend**: `http://localhost:4321` (Astro dev)
- **Backend**: `http://localhost:8001` (FastAPI dev)
- **Base de Datos**: PostgreSQL local o Neon

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

# Frontend  
BACKEND_URL=https://tu-backend.com
PUBLIC_BACKEND_URL=https://tu-backend.com
PUBLIC_GOOGLE_CLIENT_ID=tu-client-id-produccion
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
- ✅ **Gestión de Usuarios**: CRUD completo con roles
- ✅ **Dashboard**: Panel administrativo funcional
- ✅ **Seguridad**: JWT, bcrypt, CORS, validaciones
- ✅ **Arquitectura**: SOLID con inyección de dependencias
- ✅ **Testing**: Suite de tests backend
- ✅ **Documentación**: Swagger UI + README completo

### 🔄 En Desarrollo
- 🔄 **Tests Frontend**: Unit tests y E2E con Playwright
- 🔄 **Analytics**: Métricas de uso del sistema
- 🔄 **Auditoría**: Logs de acciones administrativas
- 🔄 **Notificaciones**: Email para usuarios pendientes

### 🚀 Próximas Features
- 🚀 **Multi-tenant**: Aislamiento por organización
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
pytest --cov=app                 # Tests con cobertura

# Frontend
pnpm check                       # Verificación Astro
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
