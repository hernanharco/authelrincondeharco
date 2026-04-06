# 🎯 Orquestador de Desarrollo AuthCore

## 📋 Qué Hacer Según Requerimientos (Actualizado 2024)

### 🔐 Autenticación & Seguridad
**Requerimiento**: Implementar auth completo
- **Backend**: `backend.md` → Sección "Sistema de Autenticación" con OAuth + PENDING_APPROVAL
- **Frontend**: `frontend.md` → Sección "Sistema de Autenticación" con popup OAuth
- **Herramientas**: FastAPI + JWT + Google OAuth, Svelte 5 + Runes + TypeScript
- **Estado**: ✅ Completamente implementado y probado

### 👥 Gestión de Usuarios
**Requerimiento**: CRUD de usuarios con roles
- **Backend**: Servicios especializados SOLID (4 servicios User)
  - `UserQueryService` → Consultas, estadísticas, búsqueda avanzada
  - `UserUpdateService` → Actualizaciones, bulk operations, perfiles
  - `UserValidationService` → Permisos, validaciones, reglas de negocio
  - `UserService` → Facade principal que coordina servicios
- **Frontend**: Dashboard con búsqueda, filtros, acciones masivas
- **Endpoints**: `/api/v1/users/` con 15+ endpoints especializados
- **Estado**: ✅ Completamente implementado con SOLID strict

### 🏗️ Arquitectura SOLID
**Requerimiento**: Código mantenible y escalable
- **Backend**: `backend.md` → "Arquitectura SOLID (Refactorizada 2024)"
- **Servicios**: 4 servicios especializados con SRP estricto
- **Patrones**: Facade, Repository, Dependency Injection, Strategy
- **Interfaces**: Contratos claros y desacoplados
- **Estado**: ✅ Refactorización completa implementada

### 🎨 UI/UX Moderna
**Requerimiento**: Interfaz profesional y accesible
- **Frontend**: `frontend.md` → "Sistema de Diseño"
- **Stack**: Astro 6 + Svelte 5 + TailwindCSS 4 + TypeScript
- **Componentes**: Reutilizables con 15+ iconos SVG centralizados
- **Estado**: ✅ Dashboard completo con responsive design y accesibilidad

---

## 🛠️ Qué Utilizar (Stack Actualizado)

### Backend (FastAPI 0.128.0 + PostgreSQL)
```bash
# Desarrollo completo
poetry install && poetry shell
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Tests profesionales
pytest --cov=app --cov-report=html --cov-fail-under=80

# Calidad enterprise
black . && isort . && flake8 . && mypy . && pre-commit run --all-files

# Crear usuario de prueba
python create_test_user.py --create
```

### Frontend (Astro 6.1.1 + Svelte 5.55.0)
```bash
# Desarrollo con hot-reload
pnpm install && pnpm dev --port 4321

# Build optimizado
pnpm build && pnpm preview

# Tipado estricto
pnpm astro check

# Testing (cuando se implemente)
pm test && npm run test:coverage
```

### Base de Datos (PostgreSQL + SQLAlchemy 2.0)
- **PostgreSQL**: 15+ con JSONB para multi-tenant
- **Migrations**: Automáticas en startup con validación
- **Connection**: Pooling optimizado y variables en `.env`
- **Testing**: SQLite aislado para tests

### Docker (Multi-stage + Production Ready)
```bash
# Desarrollo local
./scripts/setup.sh dev

# Producción optimizada
./scripts/setup.sh prod

# Logs y monitoreo
./scripts/setup.sh logs
docker stats
```

---

## 📁 Estructura por Tarea

### Nueva Funcionalidad Backend
1. **Interface**: `app/interfaces/` → Definir contrato
2. **Service**: `app/services/` → Implementar lógica
3. **Repository**: `app/repositories/` → Acceso a datos
4. **Schema**: `app/schemas/` → Validación Pydantic
5. **Endpoint**: `app/api/v1/endpoints/` → Exponer API
6. **Tests**: `tests/` → Unit + Integration

### Nueva Funcionalidad Frontend
1. **Componente**: `src/components/` → UI reutilizable
2. **Página**: `src/pages/` → Ruta Astro
3. **Servicio**: `src/services/` → Lógica de API
4. **Config**: `src/config/` → URLs y settings
5. **Types**: Interfaces TypeScript sincronizadas

---

## 🚀 Flujo de Trabajo Actualizado

### 1. Setup Inicial (Automatizado)
```bash
# Backend - Configuración completa
cd backend
poetry install
cp .env.example .env  # Configurar variables críticas
python create_test_user.py --create  # Usuario de prueba

# Frontend - Configuración completa
cd frontend
pnpm install
cp .env.example .env  # Configurar BACKEND_URL y GOOGLE_CLIENT_ID

# Docker - Entorno completo
docker-compose up --build  # Desarrollo local
```

### 2. Desarrollo Iterativo (SOLID First)
- **Backend**: Tests → Interface → Service → Repository → Endpoint → Documentation
- **Frontend**: Componente → Página → API Integration → Tests → Accessibility
- **Quality**: Pre-commit hooks en cada commit
- **Testing**: Cobertura 80%+ requerida para merge

### 3. Despliegue (Multi-entorno)
- **Development**: `localhost:8001` (backend) + `localhost:4321` (frontend)
- **Staging**: Docker Compose con PostgreSQL aislado
- **Production**: Vercel (frontend) + Hetzner VPS (backend) + Dokploy
- **CI/CD**: GitHub Actions automáticos con testing y security scanning

---

## 🎯 Decisiones Arquitectónicas

### ¿Cuándo usar cada servicio?

#### UserQueryService
- ✅ Consultas, estadísticas, búsquedas
- ✅ Datos de lectura únicamente
- ❌ Modificaciones de datos

#### UserUpdateService  
- ✅ Actualizaciones, cambios de estado
- ✅ Operaciones de escritura
- ❌ Consultas complejas

#### UserValidationService
- ✅ Permisos, reglas de negocio
- ✅ Validaciones centralizadas
- ❌ Lógica de CRUD

#### UserService (Facade)
- ✅ Coordinación de servicios
- ✅ Compatibilidad con endpoints
- ❌ Lógica de negocio específica

---

## 📋 Checklist de Desarrollo (Actualizado)

### Backend ✅ (Enterprise Ready)
- [ ] Interface definida con tipado estricto
- [ ] Servicio implementa SOLID con SRP estricto
- [ ] Tests unitarios (80%+ cobertura) con fixtures
- [ ] Endpoint documentado con Swagger UI
- [ ] Error handling implementado con códigos HTTP
- [ ] Security validada (JWT, RBAC, sanitización)
- [ ] Performance optimizada (queries N+1 eliminados)
- [ ] Logging estructurado implementado

### Frontend ✅ (Production Ready)
- [ ] Componente reutilizable con TypeScript
- [ ] Responsive design (mobile-first)
- [ ] Loading states y skeletons implementados
- [ ] Error handling con toast notifications
- [ ] Accessibility (ARIA labels, keyboard navigation)
- [ ] Performance (bundle size optimizado)
- [ ] SEO meta tags implementados
- [ ] Cross-browser compatibility probado

### Integración ✅ (Full Stack)
- [ ] API sincronizada (frontend ↔ backend)
- [ ] Variables de entorno configuradas por entorno
- [ ] CORS configurado con orígenes específicos
- [ ] Tests E2E funcionando (cuando se implementen)
- [ ] Security headers configurados
- [ ] Monitoring y logging centralizados

---

## 🔍 Referencias Rápidas

### Docs Principales
- **Backend**: `.windsurf/backend.md`
- **Frontend**: `.windsurf/frontend.md`
- **Servicios**: `backend/app/services/user/README.md`
- **Endpoints**: `backend/app/api/v1/endpoints/README.md`

### Comandos Esenciales
```bash
# Backend - Todo en uno
poetry run pytest && poetry run black . && poetry run isort .

# Frontend - Todo en uno  
pnpm build && pnpm astro check
```

### Variables Críticas
```bash
# Backend
BACKEND_URL, DATABASE_URL, SECRET_KEY, GOOGLE_CLIENT_ID

# Frontend
BACKEND_URL, PUBLIC_GOOGLE_CLIENT_ID
```

---

**AuthCore Orchestrator** - Tu guía central para desarrollo eficiente. 🚀
