# Frontend AuthCore - Documentación Real

## 🏗️ Stack Tecnológico Actual

- **Framework**: Astro 6.1.1
- **UI Framework**: Svelte 5.55.0 (con Runes: $state, $derived, onclick)
- **Styling**: TailwindCSS 4.2.2
- **TypeScript**: 5.9.3
- **Package Manager**: pnpm
- **Node Version**: >=22.12.0
- **Integración**: @astrojs/svelte

## 📁 Estructura Real del Proyecto

```
frontend/
├── public/                 # Assets estáticos
├── src/
│   ├── components/
│   │   ├── auth/          # Componentes de autenticación
│   │   │   ├── LoginForm.svelte      # Formulario login tradicional
│   │   │   ├── GoogleButton.svelte   # Botón OAuth con popup
│   │   │   └── PendingApproval.svelte # Vista de usuario pendiente de aprobación
│   │   ├── common/         # Componentes reutilizables
│   │   │   └── Icon.svelte           # Componente centralizado de iconos SVG
│   │   └── dashboard/     # Componentes del dashboard
│   │       ├── StatsCard.svelte      # Tarjetas de estadísticas
│   │       ├── UserAvatar.svelte     # Avatar de usuario (iniciales o imagen)
│   │       ├── RoleBadge.svelte      # Badge de rol con colores
│   │       ├── StatusBadge.svelte    # Badge de estado con indicadores
│   │       ├── OriginBadge.svelte    # Badge de origen con dominio
│   │       ├── ConfirmModal.svelte   # Modal de confirmación de acciones
│   │       ├── OriginChart.svelte    # Gráfico de distribución por origen
│   │       ├── PendingUserCard.svelte # Card de usuario pendiente de aprobación
│   │       └── UsersTable.svelte     # Tabla de usuarios con filtros y sorting
│   ├── config/
│   │   ├── api.config.ts   # SSOT de URLs de API (BACKEND_URL + ENDPOINTS)
│   │   └── index.ts       # Re-exports de configuración general
│   ├── layouts/
│   │   ├── Layout.astro          # Layout base (head, meta, estilos globales)
│   │   └── DashboardLayout.astro # Layout del dashboard (sidebar + header)
│   ├── pages/
│   │   ├── index.astro     # Página raíz (redirige a login o dashboard)
│   │   ├── login.astro     # Página de login completa
│   │   ├── logout/
│   │   │   └── index.astro # Limpieza de sesión y redirección a login
│   │   ├── api/           # API Routes de Astro (SSR)
│   │   │   ├── auth/
│   │   │   │   └── session.ts   # POST — guarda JWT en cookie httpOnly
│   │   │   └── users/
│   │   │       └── action.ts    # PATCH — proxy de acciones sobre usuarios
│   │   └── dashboard/     # Dashboard protegido (requiere sesión)
│   │       ├── index.astro         # Panel principal con estadísticas
│   │       ├── users/
│   │       │   ├── index.astro     # Listado de usuarios con filtros
│   │       │   └── [id].astro      # Detalle y edición de usuario (ruta dinámica)
│   │       ├── pending/
│   │       │   └── index.astro     # Aprobación de usuarios pendientes
│   │       └── origins/
│   │           └── index.astro     # Usuarios agrupados por origen
│   ├── services/
│   │   └── authService.ts  # Servicio singleton de autenticación (login, getCurrentUser)
│   ├── styles/
│   │   └── global.css      # Estilos globales y reset SVG
│   ├── utils/
│   │   ├── date.ts         # Utilidades de formateo de fechas
│   │   └── auth.roles.ts   # DASHBOARD_ROLES, canAccessDashboard(), isPendingOrRestricted()
│   └── middleware.ts       # Middleware de protección de rutas (verifica cookie session)
├── astro.config.mjs         # Configuración de Astro (Svelte + TailwindCSS)
├── svelte.config.js         # Configuración de Svelte
├── tsconfig.json            # Configuración de TypeScript
├── package.json             # Dependencias y scripts
├── pnpm-lock.yaml           # Lock file de dependencias
└── README.md                # Documentación
```

## 🔧 Configuración Principal

### Astro Config (`astro.config.mjs`)
- **Integración Svelte**: `@astrojs/svelte` activado
- **TailwindCSS**: Plugin Vite configurado
- **Vite**: Optimizado para desarrollo rápido

### Svelte 5 Runes
- **$state**: Estado reactivo moderno
- **$derived**: Valores computados
- **onclick**: Manejo de eventos
- **Componentes**: Reutilizables y tipados

### TailwindCSS 4
- **Configuración Vite**: Integración optimizada
- **Estilos utilitarios**: Clases modernas
- **SVG Reset**: Control de dimensiones de iconos

## 🚀 Características Principales

### Astro 6.1.1
- **Islands Architecture**: Componentes interactivos optimizados
- **File-based Routing**: Sistema de rutas por archivos
- **API Routes**: Endpoints para callbacks OAuth
- **Middleware**: Protección de rutas a nivel de servidor
- **Type Safety**: TypeScript nativo con imports absolutos (@config/)
- **SSR/SSG**: Renderizado híbrido optimizado

### Svelte 5.55.0 (Runes Modernos)
- **Runes System**: Estado reactivo moderno ($state, $derived, $effect)
- **Component Composition**: Composición de componentes reutilizables
- **TypeScript**: Tipado fuerte completo
- **Reactividad Granular**: Actualizaciones eficientes del DOM
- **Event Handling**: onclick y eventos modernos

### TailwindCSS 4.2.2
- **Utility-First**: Clases utilitarias modernas
- **Responsive Design**: Mobile-first con breakpoints optimizados
- **Dark Theme**: Paleta de colores consistente
- **Custom Components**: Componentes reutilizables con variants
- **SVG Reset**: Control de dimensiones de iconos

## 🔐 Sistema de Autenticación

### Componentes de Auth
- **LoginForm.svelte**: Formulario tradicional con validación
- **GoogleButton.svelte**: Botón OAuth con popup window y manejo de PENDING_APPROVAL
- **PendingApproval.svelte**: Componente para mostrar estado de aprobación pendiente
- **authService.ts**: Servicio singleton para gestión de auth

### Flujo de Login
1. **Formulario**: Validación en cliente con feedback visual
2. **API Call**: Envío a `/api/v1/auth/login`
3. **Response Handling**: Procesamiento de JWT y errores
4. **Session Storage**: Guardado de token y datos de usuario
5. **Redirect**: Redirección automática al dashboard

### Google OAuth con Popup (Mejorado)
1. **Popup Window**: Apertura de ventana emergente con dimensiones optimizadas
2. **OAuth Flow**: Redirección a Google → callback → postMessage seguro
3. **PENDING_APPROVAL Handling**: Detección automática y redirección con estado pendiente
4. **Token Processing**: Procesamiento de respuesta OAuth con nuevos endpoints de sesión
5. **Session Management**: Almacenamiento seguro de credenciales y datos de usuario
6. **Error Recovery**: Manejo robusto de errores de OAuth y timeouts

## 🎯 Dashboard Components

### Componentes Reutilizables
- **Icon.svelte**: Componente centralizado de iconos SVG con mapa de iconos
- **UserAvatar.svelte**: Avatar con iniciales o imagen
- **RoleBadge.svelte**: Badge de rol con colores
- **StatusBadge.svelte**: Badge de estado con indicadores
- **OriginBadge.svelte**: Badge de origen con dominio

### Layout Principal
- **DashboardLayout.astro**: Layout con sidebar y header
- **Autenticación**: Verificación de sesión y roles
- **Responsive**: Diseño adaptable mobile/desktop
- **Navigation**: Menú lateral con estados activos

### Páginas del Dashboard (Actualizadas)
- **index.astro**: Panel principal con estadísticas en tiempo real
- **users/index.astro**: Gestión completa con búsqueda avanzada y filtros
- **pending/index.astro**: Aprobación de usuarios pendientes con acciones masivas
- **origins/index.astro**: Usuarios agrupados por origen con métricas

### Nuevas Funcionalidades Integradas
- **Búsqueda Avanzada**: Integración con endpoint `/users/search`
- **Actividad de Usuario**: Detalles de actividad por usuario
- **Actualización Masiva**: Operaciones bulk para admins
- **Reset de Contraseñas**: Flujo seguro de reset de passwords
- **Perfiles de Usuario**: Actualización de datos no sensibles

## 🛠️ Comandos de Desarrollo

```bash
# Instalación
pnpm install                    # Instalar dependencias

# Desarrollo
pnpm dev                        # Servidor en localhost:4321
pnpm dev --port 3000           # En puerto personalizado

# Build y Preview
pnpm build                      # Build para producción
pnpm preview                    # Preview local del build

# CLI de Astro
pnpm astro check                # Verificación de tipos
pnpm astro add <package>        # Agregar integración
```

## 📦 Dependencias Principales

### Core Dependencies
```json
{
  "dependencies": {
    "@astrojs/svelte": "^8.0.4",
    "@tailwindcss/vite": "^4.2.2", 
    "astro": "^6.1.1",
    "svelte": "^5.55.0",
    "tailwindcss": "^4.2.2",
    "typescript": "^5.9.3"
  }
}
```

### Development Tools
- **TypeScript**: Tipado fuerte y autocompletado
- **Vite**: Build tool rápido y optimizado
- **pnpm**: Gestor de paquetes eficiente

## 🎨 Sistema de Diseño

### TailwindCSS 4.2.2
- **Dark Theme**: Paleta de colores consistente
- **Responsive**: Mobile-first approach
- **Components**: Diseño de componentes reutilizables
- **SVG Icons**: Sistema centralizado de iconos

### Paleta de Colores
- **Primarios**: Indigo (#6366F1), Success (#10B981), Warning (#F59E0B), Danger (#EF4444)
- **Neutros**: Gris oscuro (#0F1117), Card background (#1E2130)
- **Textos**: Blanco (#F9FAFB), Gris medio (#9CA3AF)

## 🌌 Integración con Backend (Actualizada)

### Configuración de API Mejorada
- **api.config.ts**: URLs centralizadas con imports absolutos (@config/api.config)
- **Environment Variables**: Configuración dinámica por entorno
- **Type Safety**: Interfaces TypeScript sincronizadas con backend
- **Error Handling**: Manejo centralizado con códigos de estado específicos
- **Retry Logic**: Reintentos automáticos para fallos de red

### Comunicación HTTP Optimizada
- **Fetch API**: Llamadas a endpoints REST con headers optimizados
- **Authentication**: Headers con JWT tokens y refresh automático
- **Error Handling**: Manejo específico por código de estado (401, 403, 422)
- **Loading States**: Estados de carga con skeletons y spinners
- **Caching**: Cache inteligente para datos frecuentes
- **Pagination**: Paginación optimizada para grandes volúmenes de datos

## 🔒 Seguridad Implementada

### Frontend Security
- **Session Management**: Tokens en localStorage
- **Route Protection**: Middleware de verificación
- **Input Validation**: Validación en formularios
- **XSS Prevention**: Sanitización de datos
- **CSRF Protection**: Tokens y headers seguros

### OAuth Security
- **Popup Communication**: postMessage API seguro
- **Origin Validation**: Verificación de origen del popup
- **Token Storage**: Almacenamiento seguro de credenciales
- **State Management**: Manejo seguro de sesión

## 📋 Estado Actual del Proyecto

### ✅ Completamente Implementado
- ✅ **Estructura base**: Astro + Svelte 5 con Runes modernos y TypeScript
- ✅ **Sistema de autenticación**: Login tradicional + Google OAuth con PENDING_APPROVAL
- ✅ **Dashboard completo**: Layout responsive con componentes reutilizables y navegación
- ✅ **TypeScript**: Tipado fuerte completo con interfaces sincronizadas
- ✅ **TailwindCSS 4**: Diseño dark theme consistente y componentes optimizados
- ✅ **Componentes centralizados**: Icon, UserAvatar, Badges con mapa de iconos completo
- ✅ **Middleware de rutas**: Protección automática con detección de sesión
- ✅ **Configuración API**: URLs centralizadas con imports absolutos (@config/api.config)
- ✅ **Error handling**: Manejo robusto de errores y estados de carga
- ✅ **Svelte 5 Runes**: $state, $derived, onclick modernos implementados
- ✅ **Astro Islands**: Componentes interactivos optimizados con SSR/SSG híbrido
- ✅ **SVG System**: Componente Icon centralizado con 15+ iconos disponibles
- ✅ **Responsive Design**: Mobile-first con breakpoints optimizados
- ✅ **Dark Theme**: Diseño consistente para modo oscuro con paleta profesional
- ✅ **API Integration**: Comunicación HTTP optimizada con headers y retry logic
- ✅ **Loading States**: Skeletons y spinners para mejor UX
- ✅ **Performance**: Paginación optimizada y cache inteligente

### 🔧 Características Técnicas
- **Svelte 5 Runes**: $state, $derived, onclick modernos
- **Astro Islands**: Componentes interactivos optimizados
- **Type Safety**: Interfaces TypeScript en todo el proyecto
- **SVG System**: Componente Icon centralizado con mapa de iconos
- **Responsive Design**: Mobile-first con breakpoints
- **Dark Theme**: Diseño consistente para modo oscuro

### 📋 Funcionalidades Disponibles (Actualizadas)
- **Login tradicional**: Formulario con validación en tiempo real (username: testuser, password: testpass)
- **Google OAuth**: Cuenta Google con sistema de aprobación PENDING_APPROVAL mejorado
- **Dashboard protegido**: Sidebar con navegación activa, breadcrumbs y notificaciones
- **Gestión de usuarios**: CRUD completo con búsqueda avanzada, filtros múltiples y sorting
- **Aprobación pendientes**: Panel dedicado con acciones masivas y bulk operations
- **Usuarios por origen**: Métricas detalladas con gráficos interactivos y estadísticas
- **Sistema de badges**: Badges de rol, estado, origen con colores consistentes y tooltips
- **Estadísticas avanzadas**: Gráficos en tiempo real con datos de endpoints especializados
- **Manejo PENDING**: Flujo completo para nuevos usuarios de Google con estado visual
- **Búsqueda global**: Búsqueda de usuarios por nombre, email, username con debounce
- **Actividad por usuario**: Resumen detallado de actividad y métricas individuales
- **Actualización masiva**: Operaciones bulk para administración eficiente
- **Reset de contraseñas**: Flujo seguro con validación de confirmación
- **Perfiles de usuario**: Actualización de datos no sensibles con validación
- **Notificaciones real-time**: Sistema de toast notifications para feedback
- **Accesibilidad**: ARIA labels, keyboard navigation y screen reader support

### 🔄 Flujo de Usuario Completo (Mejorado)
1. **Index → Login**: Redirección automática con detección de sesión existente
2. **Login tradicional**: Formulario con validación en tiempo real y API call optimizada
3. **Google OAuth**: Popup → Google → callback → PENDING_APPROVAL (si nuevo) → Dashboard
4. **Dashboard**: Panel principal con estadísticas en tiempo real y notificaciones
5. **Gestión avanzada**: CRUD completo con búsqueda, filtros, y operaciones masivas
6. **Aprobación eficiente**: Panel dedicado con bulk actions y estados actualizados
7. **Monitoreo**: Vista de actividad por usuario y métricas detalladas
8. **Logout**: Cierre de sesión completo con limpieza de localStorage y cookies

## 🌐 Despliegue y Entorno

### Desarrollo Local
- **Frontend**: `http://localhost:4321`
- **Backend**: `http://localhost:8001`
- **Base de Datos**: PostgreSQL

### Producción (Vercel)
- **Hosting**: Vercel (stack tecnológico definido)
- **Build**: `pnpm build` genera archivos en `./dist/`
- **Preview**: `pnpm preview` para testing local
- **Variables**: Configuradas en Vercel Dashboard

### Configuración de Entorno
```bash
# .env (development)
BACKEND_URL=http://localhost:8001
PUBLIC_GOOGLE_CLIENT_ID=YOUR_GOOGLE_OAUTH_CLIENT_ID

# .env (production)
BACKEND_URL=https://your-backend-domain.com
PUBLIC_GOOGLE_CLIENT_ID=YOUR_GOOGLE_OAUTH_CLIENT_ID_PROD
```

## 🎨 Sistema de Iconos SVG

### Componente Icon.svelte
- **Mapa de Iconos**: Todos los iconos centralizados
- **Sizing Control**: Dimensiones consistentes con Tailwind
- **Types**: Tipado TypeScript para nombres de iconos
- **Fallback**: Icono por defecto si no existe

### Iconos Disponibles
- **user**: Icono de usuario
- **active**: Check de activo
- **pending**: Reloj de pendiente
- **locked**: Candado de bloqueado
- **check**: Check de verificación
- **projects**: Proyectos/orígenes
- **calendar**: Calendario
- **eye**: Ojo de ver
- **edit**: Lápiz de editar
- **search**: Lupa de buscar
- **arrow**: Flecha de dirección
- **logout**: Cierre de sesión

### Uso en Componentes
```svelte
<Icon name="user" size="5" />
<Icon name="active" size="4" />
<Icon name="pending" size="6" />
```

## 🧪 Testing Strategy

### Testing de Componentes
- **Unit Tests**: Pruebas de lógica de componentes
- **Integration Tests**: Pruebas de flujo completo
- **E2E Tests**: Pruebas end-to-end con Playwright

### Testing de Autenticación
- **Login Flow**: Formulario → API → Dashboard
- **OAuth Flow**: Popup → Google → Callback → Dashboard
- **Error Handling**: Estados de error y validación
- **Session Management**: Persistencia y cleanup

### 🚀 Optimizaciones y Mejoras Recientes
- ✅ **Imports Absolutos**: Configuración @config/ para imports limpios y mantenibles
- ✅ **Nuevos Endpoints**: Integración completa con búsqueda, actividad, bulk operations
- ✅ **Error Handling Mejorado**: Manejo específico por código de estado (401, 403, 422)
- ✅ **Loading States**: Skeletons y spinners para mejor UX durante carga
- ✅ **Type Safety**: Interfaces sincronizadas con backend SOLID
- ✅ **Performance**: Paginación optimizada y cache inteligente para datos frecuentes
- ✅ **Responsive Design**: Mejoras significativas en mobile y tablet
- ✅ **Accessibility**: Mejoras en ARIA labels, keyboard navigation y screen reader
- ✅ **Security**: Mejoras en sanitización de inputs y CSRF protection
- ✅ **Component Architecture**: Componentes más reutilizables y mantenibles
- ✅ **State Management**: Manejo eficiente de estado con Svelte 5 Runes
- ✅ **API Communication**: Retry logic automático y manejo de errores robusto
- ✅ **User Experience**: Micro-interacciones, transiciones suaves y feedback visual
- ✅ **Code Quality**: Linting, formateo y tipado estricto implementados
- ✅ **Build Optimization**: Bundle size optimizado y tiempo de carga reducido
