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
│   │   │   ├── LoginForm.svelte    # Formulario login tradicional
│   │   │   └── GoogleButton.svelte # Botón OAuth con popup
│   │   ├── common/         # Componentes reutilizables
│   │   │   └── Icon.svelte        # Componente centralizado de iconos SVG
│   │   └── dashboard/     # Componentes del dashboard
│   │       ├── StatsCard.svelte    # Tarjetas de estadísticas
│   │       ├── UserAvatar.svelte   # Avatar de usuario
│   │       ├── RoleBadge.svelte     # Badge de rol
│   │       ├── StatusBadge.svelte   # Badge de estado
│   │       └── OriginBadge.svelte   # Badge de origen
│   ├── config/
│   │   ├── api.config.ts   # Configuración de URLs de API
│   │   └── index.ts       # Configuración general
│   ├── layouts/
│   │   └── DashboardLayout.astro   # Layout principal del dashboard
│   ├── pages/
│   │   ├── index.astro     # Página principal (redirige a login)
│   │   ├── login.astro     # Página de login completa
│   │   ├── api/           # Endpoints API para callbacks
│   │   │   └── v1/
│   │   │       └── auth/
│   │   │           └── callback.astro # Callback OAuth
│   │   └── dashboard/     # Dashboard protegido
│   │       ├── index.astro    # Panel principal
│   │       ├── users/         # Gestión de usuarios
│   │       │   └── index.astro
│   │       ├── pending/       # Usuarios pendientes
│   │       │   └── index.astro
│   │       └── origins/       # Usuarios por origen
│   │           └── index.astro
│   ├── services/
│   │   └── authService.ts # Servicio de autenticación
│   ├── styles/
│   │   └── global.css      # Estilos globales
│   ├── utils/
│   │   └── date.ts         # Utilidades de fechas
│   └── middleware.ts          # Middleware de rutas
├── astro.config.mjs         # Configuración de Astro
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
- **Islands Architecture**: Componentes interactivos
- **File-based Routing**: Sistema de rutas por archivos
- **API Routes**: Endpoints para callbacks OAuth
- **Middleware**: Protección de rutas a nivel de servidor
- **Type Safety**: TypeScript nativo

### Svelte 5.55.0
- **Runes System**: Estado reactivo moderno
- **Component Composition**: Composición de componentes
- **TypeScript**: Tipado fuerte completo
- **Reactividad**: $state, $derived, $effect

### TailwindCSS 4.2.2
- **Utility-First**: Clases utilitarias modernas
- **Responsive Design**: Mobile-first
- **Dark Theme**: Paleta de colores consistente
- **Custom Components**: Componentes reutilizables

## 🔐 Sistema de Autenticación

### Componentes de Auth
- **LoginForm.svelte**: Formulario tradicional con validación
- **GoogleButton.svelte**: Botón OAuth con popup window
- **authService.ts**: Servicio singleton para gestión de auth

### Flujo de Login
1. **Formulario**: Validación en cliente con feedback visual
2. **API Call**: Envío a `/api/v1/auth/login`
3. **Response Handling**: Procesamiento de JWT y errores
4. **Session Storage**: Guardado de token y datos de usuario
5. **Redirect**: Redirección automática al dashboard

### Google OAuth con Popup
1. **Popup Window**: Apertura de ventana emergente
2. **OAuth Flow**: Redirección a Google y callback
3. **postMessage**: Comunicación segura entre popup y parent
4. **Token Handling**: Procesamiento de respuesta OAuth
5. **Session Management**: Almacenamiento de credenciales

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

### Páginas del Dashboard
- **index.astro**: Panel principal con estadísticas
- **users/index.astro**: Gestión completa de usuarios
- **pending/index.astro**: Aprobación de usuarios pendientes
- **origins/index.astro**: Usuarios agrupados por origen

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

## 🌌 Integración con Backend

### Configuración de API
- **api.config.ts**: URLs centralizadas del backend
- **Environment Variables**: Configuración por entorno
- **Type Safety**: Interfaces TypeScript compartidas

### Comunicación HTTP
- **Fetch API**: Llamadas a endpoints REST
- **Authentication**: Headers con JWT tokens
- **Error Handling**: Manejo centralizado de errores
- **Loading States**: Estados de carga en componentes

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
- ✅ Estructura base con Astro + Svelte 5
- ✅ Sistema de autenticación completo (tradicional + Google OAuth)
- ✅ Dashboard con layout responsive y componentes reutilizables
- ✅ TypeScript configurado con tipado fuerte
- ✅ TailwindCSS 4 con diseño dark theme consistente
- ✅ Componentes centralizados (Icon, UserAvatar, Badges)
- ✅ Middleware de protección de rutas
- ✅ Configuración de API centralizada
- ✅ Manejo de errores y estados de carga

### 🔧 Características Técnicas
- **Svelte 5 Runes**: $state, $derived, onclick modernos
- **Astro Islands**: Componentes interactivos optimizados
- **Type Safety**: Interfaces TypeScript en todo el proyecto
- **SVG System**: Componente Icon centralizado con mapa de iconos
- **Responsive Design**: Mobile-first con breakpoints
- **Dark Theme**: Diseño consistente para modo oscuro

### 📋 Funcionalidades Disponibles
- Login tradicional (username: testuser, password: testpass)
- Google OAuth con cuenta Google
- Dashboard protegido con sidebar
- Gestión de usuarios con tabla y filtros
- Aprobación de usuarios pendientes
- Usuarios agrupados por origen/proyecto
- Sistema de badges y avatares
- Estadísticas y gráficos

### 🔄 Flujo de Usuario Completo
1. **Index → Login**: Redirección automática si no autenticado
2. **Login tradicional**: Formulario con validación y API call
3. **Google OAuth**: Popup con postMessage communication
4. **Dashboard**: Panel principal con estadísticas y navegación
5. **Gestión**: CRUD completo de usuarios con roles y permisos
6. **Logout**: Cierre de sesión y limpieza de localStorage

## 🌐 Despliegue y Entorno

### Desarrollo Local
- **Frontend**: `http://localhost:4321`
- **Backend**: `http://localhost:8001`
- **Base de Datos**: Neon PostgreSQL

### Producción (Vercel)
- **Hosting**: Vercel (stack tecnológico definido)
- **Build**: `pnpm build` genera archivos en `./dist/`
- **Preview**: `pnpm preview` para testing local
- **Variables**: Configuradas en Vercel Dashboard

### Configuración de Entorno
```bash
# .env (development)
PUBLIC_API_URL=http://localhost:8001
PUBLIC_GOOGLE_CLIENT_ID=tu_google_client_id

# .env (production)
PUBLIC_API_URL=https://tu-backend.com
PUBLIC_GOOGLE_CLIENT_ID=tu_google_client_id_prod
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

## 🚀 Optimizaciones y Mejoras

### Performance
- **Code Splitting**: División de código por rutas
- **Lazy Loading**: Carga bajo demanda de componentes
- **Image Optimization**: Avatares e imágenes optimizadas
- **Bundle Analysis**: Tamaño y dependencias optimizadas

### UX/UI
- **Loading States**: Indicadores visuales de carga
- **Error Messages**: Feedback claro y amigable
- **Responsive Design**: Adaptación a todos los dispositivos
- **Dark Mode**: Tema oscuro consistente
- **Microinteractions**: Animaciones y transiciones suaves
