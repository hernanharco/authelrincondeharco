# Frontend AuthCore - Resumen Técnico

## Estructura del Proyecto

### 📁 Archivos de Configuración
- **package.json**: Dependencias principales (Next.js 16.1.6, React 19.2.3, Tailwind CSS 4, @react-oauth/google 0.13.4, clsx, tailwind-merge)
- **next.config.ts**: Configuración con rewrites al backend, COOP para Google OAuth, headers CORS
- **tsconfig.json**: Configuración TypeScript estricta con paths (@/*)
- **tailwind.config**: Configuración de Tailwind CSS 4 con CSS variables
- **eslint.config.mjs**: Reglas ESLint para código limpio
- **postcss.config.mjs**: Configuración PostCSS para Tailwind
- **pnpm-workspace.yaml**: Workspace configuration para monorepo

### 📁 Archivos de Entorno
- **.env.local**: Variables de entorno (NEXT_PUBLIC_API_URL, NEXT_PUBLIC_GOOGLE_CLIENT_ID, BACKEND_URL)
- **.env.example**: Plantilla de variables de entorno
- **.gitignore**: Exclusiones de node_modules, .next, builds, .env.local

### 📁 Docker y Despliegue
- **Dockerfile**: Imagen optimizada para producción
- **.dockerignore**: Exclusiones para imagen Docker
- **setup.sh**: Script de configuración para desarrollo/producción

### 📁 Source Code (`src/`)

#### 📂 `app/` - Next.js App Router
- **layout.tsx**: Layout principal con GoogleOAuthProvider y fuentes optimizadas
- **page.tsx**: Página principal de aterrizaje (redirect a /login)
- **login/**: Páginas de autenticación (login, forgot-password, reset-password)
- **dashboard/**: Dashboard principal y sub-rutas
- **health/**: Página de monitoreo de salud

#### 📂 `components/` - Componentes React SOLID
- **AuthView.tsx**: Vista principal de autenticación con composición de componentes
- **ui/**: Componentes atómicos reutilizables (S - Single Responsibility)
  - **Button/index.tsx**: Botón configurable con variantes y estados
  - **Input/index.tsx**: Input con label, iconos, validación y accesibilidad
  - **Alert/index.tsx**: Alertas con diferentes variantes y dismissible
  - **GoogleButton/index.tsx**: Botón específico para Google OAuth
- **forms/**: Formularios específicos (O - Open/Closed)
  - **LoginForm/index.tsx**: Formulario de login tradicional
  - **ForgotPasswordForm/index.tsx**: Formulario de recuperación de contraseña
  - **ResetPasswordForm/index.tsx**: Formulario de restablecimiento de contraseña
- **dashboard/Overview.tsx**: Dashboard con estadísticas y actividad reciente
- **layout/**: Layouts del dashboard (DashboardLayout, UsersDashboard)

#### 📂 `hooks/` - Hooks Personalizados SOLID
- **useAuth/index.ts**: Hook principal con inyección de dependencias (DIP)
  - **useAuthLogin.ts**: Lógica específica de login tradicional
  - **useAuthGoogle.ts**: Lógica específica de Google OAuth
  - **useAuthLogout.ts**: Lógica específica de logout
- **useUsers.ts**: CRUD de usuarios con manejo de estado optimizado
- **useHealthCheck.ts**: Monitoreo de salud del backend

#### 📂 `services/` - Lógica de Negocio SOLID (S, DIP)
- **authService.ts**: Servicio de autenticación con interface IAuthService
- **userService.ts**: Servicio de usuarios con interface IUserService
- **apiService.ts**: Servicio de llamadas HTTP genérico

#### 📂 `types/` - Definiciones TypeScript
- **auth/**: Tipos para autenticación
  - **LoginRequest.ts**: Request de login tradicional
  - **AuthState.ts**: Estado de autenticación
  - **GoogleResponse.ts**: Respuesta de Google OAuth
- **user/**: Tipos para usuarios
  - **User.ts**: Modelo de usuario
  - **UserRole.ts**: Enum de roles
  - **UserStatus.ts**: Enum de estados

#### 📂 `config/` - Configuración
- **api.ts**: Configuración centralizada de endpoints y URLs del API
- **environment.ts**: Validación de variables de entorno

#### 📂 `utils/` - Utilidades SOLID (S)
- **cn.ts**: Utilidad de clases CSS (clsx + tailwind-merge)
- **constants.ts**: Constantes centralizadas de la aplicación
- **validation.ts**: Utilidades de validación
- **storage.ts**: Utilidades de localStorage/sessionStorage

### 📁 Archivos Adicionales
- **README.md**: Documentación completa del proyecto
- **agent.md**: Guía de desarrollo y mejores prácticas
- **Google*.md**: Documentación de configuración OAuth
- **.windsurfrules**: Reglas específicas del IDE

## Características Principales

### 🚀 Next.js 16 con App Router
- Server Components y Client Components optimizados
- Routing basado en archivos
- Metadata API para SEO
- React Compiler activado para optimización automática

### 🎨 Tailwind CSS 4
- Sistema de diseño moderno con CSS variables
- Dark mode automático
- Componentes responsive
- Diseño moderno y accesible

### 🔐 Autenticación Completa
- Login tradicional con JWT
- Google OAuth 2.0 integrado (@react-oauth/google)
- Manejo de sesión persistente con localStorage
- Redirección dinámica post-login
- Recuperación de contraseña
- httpOnly cookies + Authorization headers

### 📊 Dashboard Interactivo
- Estadísticas en tiempo real
- Gestión de usuarios completa (CRUD)
- Monitoreo de salud del sistema
- Roles y permisos por usuario

### 🛠️ Desarrollo Optimizado
- TypeScript estricto
- ESLint configurado
- React Compiler activado
- Hot reload en desarrollo
- pnpm como gestor de paquetes

## Integración con Backend

### Configuración de API
- **Backend URL**: `http://localhost:8001` (configurable en `.env.local`)
- **Rewrites**: `/backend/*` → `${BACKEND_URL}/*`
- **CORS**: Orígenes permitidos en backend
- **COOP**: `same-origin-allow-popups` para Google OAuth

### Flujo de Autenticación
1. Usuario hace click en "Login with Google"
2. @react-oauth/google obtiene `access_token` directamente
3. Frontend envía `access_token` a `/api/v1/auth/google`
4. Backend valida token llamando a Google userinfo API
5. Si el usuario no existe, se crea automáticamente con username único
6. Backend genera JWT interno y establece cookie httpOnly
7. Frontend recibe respuesta y actualiza estado

### Manejo de Sesión
- **Persistencia**: localStorage para auth state
- **Cookies**: httpOnly para JWT tokens

## Variables de Entorno

### Archivo `.env.local` requerido:
```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8001

# Google OAuth
NEXT_PUBLIC_GOOGLE_CLIENT_ID=tu_google_client_id_aqui

# Backend URL (para rewrites)
BACKEND_URL=http://localhost:8001
```

## Comandos Principales

```bash
# Instalación
pnpm install          # Instalar dependencias

# Desarrollo
pnpm dev              # Servidor de desarrollo (http://localhost:3000)

# Producción
pnpm build            # Build de producción
pnpm start            # Servidor de producción

# Calidad de código
pnpm lint             # Análisis de código
pnpm lint:fix         # Corrección automática
pnpm type-check       # Verificación de tipos TypeScript

# Depuración
pnpm dev:debug        # Desarrollo con debugging
```

## Estructura de Componentes

### Componentes de Autenticación
- **AuthView**: Formulario principal con tabs (Login/Forgot/Reset)
- **GoogleButton**: Integración con @react-oauth/google
- **PasswordForm**: Formularios de recuperación/restablecimiento

### Componentes de Dashboard
- **DashboardLayout**: Layout principal del dashboard
- **Overview**: Estadísticas y métricas
- **UserManagement**: Tabla de usuarios con CRUD
- **HealthMonitor**: Estado del sistema

### Hooks Personalizados
- **useAuth**: Estado global de autenticación
- **useUsers**: Gestión de usuarios con cache
- **useHealthCheck**: Monitoreo periódico del backend

## Problemas Comunes y Soluciones

### Errores Conocidos
- **400 Bad Request**: Backend URL incorrecta o variables de entorno faltantes
- **CORS**: Orígenes no permitidos en backend
- **COOP**: Política bloqueando popup de Google OAuth (solucionado con `same-origin-allow-popups`)
- **Autofill Extension**: Error de extensión de navegador (no afecta funcionalidad)

### Depuración
- **Console Logs**: Verificar `process.env.NEXT_PUBLIC_API_URL`
- **Network Tab**: Revisar llamadas a `/backend/api/v1/*`
- **Cookies**: Verificar `access_token` httpOnly cookie
- **LocalStorage**: Comprobar `authState` persistencia

## Optimizaciones de Rendimiento

### React Compiler
- Compilación automática de componentes
- Memoización inteligente
- Reducción de re-renders

### Bundle Optimization
- Code splitting por rutas
- Dynamic imports para componentes pesados
- Optimización de imágenes Next.js

### Cache Strategy
- localStorage para auth state
- React Query para datos de usuarios
- Cache de API responses

## Accesibilidad y UX

### A11y Compliance
- Todos los inputs tienen `id` y `label` con `for`
- Navegación por teclado
- Screen reader friendly
- Focus management

### UX Features
- Loading states en todas las operaciones
- Error handling con mensajes claros
- Redirecciones inteligentes
- Dark mode automático
- Responsive design

## Deploy y Producción

### Environment Variables
- **NEXT_PUBLIC_API_URL**: URL del backend en producción
- **NEXT_PUBLIC_GOOGLE_CLIENT_ID**: OAuth Client ID de producción
- **BACKEND_URL**: URL para rewrites internos

### Build Optimization
- Minificación automática
- Tree shaking
- Image optimization
- Font optimization

### Security Headers
- COOP configurado para OAuth
- CSP headers por defecto
- X-Frame-Boundary
- Referrer-Policy

## Arquitectura SOLID Detallada

### Single Responsibility Principle (SRP)
- **Componentes UI**: Cada componente tiene una sola responsabilidad visual
- **Hooks**: Cada hook maneja un solo dominio de estado
- **Servicios**: Cada servicio maneja un solo tipo de operación
- **Utils**: Cada utilidad tiene una sola función específica

### Open/Closed Principle (OCP)
- **Componentes Configurables**: Props permiten extensión sin modificación
- **Servicios**: Interfaces permiten nuevas implementaciones
- **Formularios**: Composición permite nuevos tipos de formularios

### Liskov Substitution Principle (LSP)
- **Implementaciones de Servicios**:AuthService puede ser sustituido por MockAuthService
- **Componentes**: Button puede ser sustituido por LoadingButton

### Interface Segregation Principle (ISP)
- **Props Interfaces**: Interfaces específicas para cada componente
- **Service Interfaces**: Métodos específicos para cada caso de uso
- **Type Definitions**: Tipos pequeños y específicos

### Dependency Inversion Principle (DIP)
- **Hook Dependencies**: useAuth recibe IAuthService por parámetro
- **Service Dependencies**: Services dependen de interfaces, no de implementaciones
- **Component Dependencies**: Componentes dependen de props, no de implementaciones

## Testing Strategy

### Unit Tests
- **Component Tests**: Test de componentes con React Testing Library
- **Hook Tests**: Test de hooks con renderHook
- **Service Tests**: Test de servicios con mocks

### Integration Tests
- **API Tests**: Test de integración con backend real
- **OAuth Tests**: Test de flujo de Google OAuth
- **Form Tests**: Test de envío de formularios

### E2E Tests
- **Playwright**: Tests end-to-end completos
- **User Flows**: Test de flujos de usuario completos
- **Cross-browser**: Tests en diferentes navegadores
