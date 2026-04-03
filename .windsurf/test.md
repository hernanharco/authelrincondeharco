# Testing Suite - AuthCore

## 🧪 Overview General

AuthCore cuenta con suites de testing completas y profesionales para ambos backend (Python) y frontend (TypeScript/Svelte), siguiendo las mejores prácticas de la industria y garantizando calidad y fiabilidad del código.

---

## 🐍 Backend Testing (Python + pytest)

### Framework y Stack
- **pytest**: Framework principal con async support
- **pytest-asyncio**: Soporte para código asíncrono
- **pytest-cov**: Cobertura de código (80%+ mínimo)
- **SQLite**: Base de datos aislada para tests
- **Fixtures**: Reutilizables para usuarios, tokens, mocks

### Estructura de Tests
```
backend/tests/
├── conftest.py              # Configuración global y fixtures
├── pytest.ini              # Configuración profesional de pytest
├── test_auth_endpoints.py    # Tests endpoints de autenticación
├── test_user_endpoints.py    # Tests endpoints de usuarios
├── test_auth_services.py     # Tests servicios de autenticación
├── test_user_services.py     # Tests servicios de usuarios
├── test_user_repository.py   # Tests repositorio de usuarios
├── test_models.py            # Tests modelos SQLAlchemy
├── test_domain.py            # Tests lógica de dominio
└── test_main.py             # Tests endpoints principales
```

### Tests por Categoría

#### 🔴 Tests Críticos (High Priority)
- **Endpoints Tests**: Validación completa de API REST
  - Login tradicional (éxito/fracaso)
  - Google OAuth (flujo completo)
  - CRUD de usuarios con permisos
  - Protección de rutas y tokens

- **Services Tests**: Lógica de negocio
  - AuthService (autenticación, tokens)
  - UserService (validaciones, reglas de negocio)
  - TokenService (JWT creation/verification)
  - GoogleOAuthService (integración Google)

#### 🟡 Tests de Soporte (Medium Priority)
- **Repository Tests**: Acceso a datos
  - CRUD operations
  - Filtros y búsqueda
  - Validaciones de unicidad
  - Operaciones de base de datos

- **Models Tests**: Modelos SQLAlchemy
  - Validaciones de campos
  - Defaults y constraints
  - Relaciones y enums
  - Timestamps y tipos

- **Domain Tests**: Lógica de dominio
  - Jerarquía de roles y permisos
  - Reglas de negocio
  - Validaciones de eliminación
  - Casos edge y límites

### Configuración Profesional
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

### Comandos de Ejecución
```bash
# Todos los tests
pytest

# Con cobertura
pytest --cov=app --cov-report=html

# Por categoría
pytest -m auth          # Tests de autenticación
pytest -m users         # Tests de usuarios
pytest -m integration    # Tests de integración
pytest -m unit          # Tests unitarios

# Verboso y específico
pytest -v tests/test_auth_endpoints.py

# Reporte HTML
pytest --cov=app --cov-report=html --cov-report=term-missing
```

### Métricas de Calidad
- **Cobertura**: 80%+ configurado
- **Tests Unitarios**: Aislados con mocks
- **Tests Integración**: Con base de datos real
- **Performance**: Ejecución rápida y paralela
- **Seguridad**: Validación de permisos y tokens

---

## 🎨 Frontend Testing (TypeScript + Vitest)

### Framework y Stack
- **Vitest**: Framework moderno y rápido
- **@testing-library/svelte**: Testing de componentes Svelte 5
- **jsdom**: Entorno DOM simulado
- **TypeScript**: Tipado fuerte en tests
- **Coverage**: 80%+ mínimo configurado

### Estructura de Tests
```
frontend/tests/
├── setup.ts                 # Configuración global de Vitest
├── vitest.config.ts         # Configuración profesional
├── auth/                    # Tests componentes de autenticación
│   ├── LoginForm.test.ts     # Formulario de login
│   └── GoogleButton.test.ts  # Botón Google OAuth
├── dashboard/               # Tests componentes dashboard
│   ├── StatsCard.test.ts     # Tarjetas de estadísticas
│   └── UsersTable.test.ts   # Tabla de usuarios
├── pages/                   # Tests de páginas Astro
│   └── login.test.ts        # Página de login
├── services/                # Tests de servicios
│   └── authService.test.ts  # Servicio de autenticación
└── middleware.test.ts       # Tests middleware de rutas
```

### Tests por Categoría

#### 🔴 Tests Críticos (High Priority)
- **Componentes de Autenticación**:
  - LoginForm (validación, envío, errores)
  - GoogleButton (OAuth popup, manejo de errores)
  - PendingApproval (estado pendiente)

- **Componentes de Dashboard**:
  - UsersTable (filtrado, paginación, acciones)
  - StatsCard (renderizado, formatos, accesibilidad)
  - RoleBadge, StatusBadge (estados y permisos)

#### 🟡 Tests de Soporte (Medium Priority)
- **Páginas Completas**:
  - Login page (renderizado, parámetros URL)
  - Dashboard pages (carga de datos, errores)

- **Servicios y Utilidades**:
  - AuthService (tokens, llamadas API)
  - Date utils (formateo de fechas)
  - Auth roles (validación de permisos)

- **Middleware**:
  - Protección de rutas
  - Redirecciones automáticas
  - Validación de tokens

### Configuración Profesional
```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    globals: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      thresholds: {
        global: {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80
        }
      }
    }
  }
});
```

### Comandos de Ejecución
```bash
# Todos los tests
npm test

# Con cobertura
npm run test:coverage

# Modo watch (desarrollo)
npm run test:watch

# Interfaz gráfica
npm run test:ui

# Tests específicos
npm test -- auth/
npm test -- --grep "integration"
```

### Dependencias de Testing
```json
{
  "devDependencies": {
    "vitest": "^2.0.5",
    "@vitest/ui": "^2.0.5",
    "@vitest/coverage-v8": "^2.0.5",
    "jsdom": "^25.0.1",
    "@testing-library/svelte": "^5.0.0",
    "@testing-library/jest-dom": "^6.6.0"
  }
}
```

---

## 🎯 Estrategia General de Testing

### Pyramid de Testing

#### 🔴 Tests Unitarios (70%)
- **Veloces**: Aislados y rápidos
- **Mocks**: Simulación de dependencias externas
- **Cobertura**: Lógica de negocio pura
- **Ejecución**: En cada PR y commit

#### 🟡 Tests de Integración (20%)
- **Reales**: Con base de datos y APIs
- **End-to-End**: Flujo completo usuario
- **Validación**: Interacción entre componentes
- **Ejecución**: En CI/CD

#### 🟢 Tests E2E (10%)
- **Browser**: Simulación real del usuario
- **Flujos Críticos**: Login, CRUD, OAuth
- **Performance**: Tiempos de respuesta
- **Ejecución**: En staging antes de producción

### Principios de Testing

#### **FIRST Principles**
- **Fast**: Rápidos de ejecutar
- **Independent**: No dependen entre sí
- **Repeatable**: Mismos resultados siempre
- **Self-Validating**: Pass/Fail claro
- **Timely**: Escritos oportunamente

#### **Best Practices**
- **AAA Pattern**: Arrange, Act, Assert
- **Descriptive Names**: Nombres claros y específicos
- **Single Assertion**: Un assert por test cuando sea posible
- **Test Data**: Datos predecibles y aislados
- **Error Cases**: Probar caminos de error

### Coverage Goals

#### **Backend Targets**
- **Statements**: 85%+
- **Branches**: 80%+
- **Functions**: 85%+
- **Lines**: 85%+

#### **Frontend Targets**
- **Statements**: 80%+
- **Branches**: 75%+
- **Functions**: 80%+
- **Lines**: 80%+

---

## 🚀 Integración CI/CD

### GitHub Actions Workflow
```yaml
name: Tests
on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: |
        pip install poetry
        poetry install
        pytest --cov=app --cov-report=xml
      - uses: codecov/codecov-action@v3

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
      - run: |
        npm ci
        npm run test:coverage
      - uses: codecov/codecov-action@v3
```

### Quality Gates
- **Backend**: 80%+ cobertura, todos los tests pasan
- **Frontend**: 75%+ cobertura, todos los tests pasan
- **Performance**: Tests completan en < 5 minutos
- **Security**: No vulnerabilidades críticas

---

## 📊 Reportes y Métricas

### Reportes de Cobertura
- **Backend**: `backend/htmlcov/index.html`
- **Frontend**: `frontend/coverage/index.html`
- **CI**: Integración con Codecov
- **Local**: `npm run test:coverage` o `pytest --cov=app`

### Métricas de Calidad
- **Test Count**: Número total de tests
- **Pass Rate**: Porcentaje de tests exitosos
- **Coverage**: Porcentaje de código cubierto
- **Execution Time**: Tiempo total de ejecución
- **Flaky Tests**: Tests inconsistentes

### Monitoreo
- **Test Trends**: Evolución de cobertura
- **Performance**: Tiempos de ejecución históricos
- **Failure Analysis**: Patrones de errores comunes
- **Quality Metrics**: Densidad de bugs por feature

---

## 🛠️ Troubleshooting Común

### Backend Issues
```bash
# Tests lentos
pytest --durations=10

# Tests fallidos con detalles
pytest -v --tb=long

# Tests específicos fallidos
pytest tests/test_auth_endpoints.py::test_login_success -v

# Debug con breakpoints
pytest --pdb
```

### Frontend Issues
```bash
# Tests con UI interactiva
npm run test:ui

# Debug en browser
npm run test -- --inspect-brk

# Tests específicos
npm test -- --grep "LoginForm"
```

### Problemas Comunes
- **Database Locks**: Tests corren en paralelo
- **Async Issues**: Mocks de funciones asíncronas
- **Component Hydration**: Tests de Svelte 5
- **Environment Variables**: Configuración de testing

---

## 🎯 Estado Actual y Roadmap

### ✅ Completamente Implementado
- ✅ **Backend Suite**: pytest con 80%+ cobertura
- ✅ **Frontend Suite**: Vitest + Testing Library
- ✅ **CI Integration**: GitHub Actions automáticos
- ✅ **Coverage Reports**: HTML + Codecov
- ✅ **Quality Gates**: Umbrales de calidad

### 🔄 En Mejora
- 🔄 **E2E Tests**: Playwright o Cypress
- 🔄 **Performance Tests**: Carga y estrés
- 🔄 **Visual Regression**: Cambios en UI
- 🔄 **Accessibility Tests**: WCAG compliance

### 🚀 Próximos Features
- 🚀 **Contract Testing**: API-frontend contracts
- 🚀 **Mutation Testing**: Pitest equivalent
- 🚀 **Property-Based Testing**: Hypothesis
- 🚀 **Chaos Engineering**: Resiliencia

---

**AuthCore Testing Suite** - Calidad garantizada con testing profesional en todos los niveles. 🧪✨