# Frontend Project Summary

## 🏗️ **Stack Tecnológico**

- **Framework**: Astro 6.1.1
- **UI Framework**: Svelte 5.55.0 (con Runes: $state, $derived, onclick)
- **Styling**: TailwindCSS 4.2.2
- **TypeScript**: 5.9.3
- **Package Manager**: pnpm
- **Node Version**: >=22.12.0
- **Integrations**: @astrojs/svelte

## 📁 **Estructura del Proyecto**

```
frontend/
├── public/                 # Assets estáticos
├── src/
│   ├── components/
│   │   └── auth/          # Componentes de autenticación
│   │       ├── LoginForm.svelte    # Formulario login tradicional
│   │       └── GoogleButton.svelte # Botón OAuth con popup
│   ├── config/
│   │   └── api.config.ts  # Configuración centralizada de API
│   ├── layouts/
│   │   └── Layout.astro   # Layout principal
│   ├── pages/
│   │   ├── index.astro    # Página principal (redirige a login)
│   │   ├── login.astro    # Página de login completa
│   │   ├── api/           # Endpoints API para callbacks
│   │   │   └── v1/
│   │   │       └── auth/
│   │   │           └── callback.astro # Callback OAuth
│   │   └── dashboard/     # Dashboard protegido
│   │       └── index.astro
│   ├── services/
│   │   └── authService.ts # Servicio de autenticación
│   ├── styles/            # Estilos globales
│   └── middleware.ts      # Middleware de rutas
├── astro.config.mjs       # Configuración de Astro
├── svelte.config.js       # Configuración de Svelte
├── tsconfig.json          # Configuración de TypeScript
├── package.json           # Dependencias y scripts
├── pnpm-lock.yaml         # Lock file de dependencias
└── README.md              # Documentación
```

## 🔐 **Funcionalidades Principales**

### Autenticación Completa
- **Login tradicional**: Formulario con username/password y validación
- **Google OAuth con Popup**: Integración completa con popup no intrusivo
- **Gestión de sesiones**: Tokens JWT en localStorage
- **Redirecciones automáticas**: Login → Dashboard, Index → Login
- **Manejo de errores**: Mensajes amigables y estados de carga

### Componentes Reactivos (Svelte 5 Runes)
- **LoginForm.svelte**: 
  - Estado reactivo con `$state`
  - Validación en tiempo real
  - Manejo de errores y loading states
  - Redirección automática al dashboard

- **GoogleButton.svelte**:
  - Flujo OAuth con popup window
  - Comunicación via postMessage
  - Estados de carga y error handling
  - Cierre automático de popup

### Servicios y Configuración
- **authService.ts**: 
  - Clase singleton con métodos de autenticación
  - Tipado fuerte con TypeScript
  - Manejo de respuestas HTTP
  - Gestión de errores centralizada

- **api.config.ts**:
  - Centralización de URLs de API
  - Configuración de endpoints
  - Helper functions para construcción de URLs

### Middleware de Rutas
- **middleware.ts**: Protección de rutas basada en sesión
- Verificación de cookies de sesión
- Redirecciones automáticas

## 🚀 **Scripts Disponibles**

| Comando | Acción |
|---------|--------|
| `pnpm dev` | Servidor de desarrollo en localhost:4321 |
| `pnpm build` | Build para producción |
| `pnpm preview` | Preview local del build |
| `pnpm astro ...` | Comandos CLI de Astro |
| `pnpm astro check` | Verificación de tipos |
| `pnpm astro add` | Agregar integraciones |

## �️ **Comandos de Desarrollo**

```bash
# Instalación
pnpm install

# Desarrollo
pnpm dev                    # Servidor en localhost:4321
pnpm dev --port 3000        # En puerto personalizado

# Build y Preview
pnpm build                  # Build para producción
pnpm preview                # Preview del build

# Utilidades
pnpm astro check            # Verificación de tipos
pnpm astro add <package>    # Agregar integración
```

## � **Configuración Clave**

### Astro Config
- Integración con Svelte activada
- TailwindCSS via Vite plugin
- Configuración minimalista

### Svelte 5 Runes
- Uso de `$state` para estado reactivo
- `$derived` para valores computados
- `onclick` para manejo de eventos

### TailwindCSS 4
- Configuración vía Vite plugin
- Estilos utilitarios modernos

## 📦 **Dependencias Principales**

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

## 🎯 **Estado Actual del Proyecto**

### ✅ Completamente Implementado
- ✅ Estructura base con Astro + Svelte 5
- ✅ Sistema de autenticación completo (tradicional + Google OAuth)
- ✅ Login tradicional con validación y errores
- ✅ Google OAuth con popup y postMessage
- ✅ Gestión de sesiones con localStorage
- ✅ Redirecciones automáticas y middleware
- ✅ TypeScript configurado con tipado fuerte
- ✅ TailwindCSS para estilos modernos
- ✅ Componentes reactivos con Svelte 5 Runes
- ✅ Configuración centralizada de API
- ✅ Manejo robusto de errores
- ✅ Estados de carga y feedback visual

### 🔧 Características Técnicas
- **Popup OAuth**: Ventana emergente no intrusiva
- **postMessage API**: Comunicación segura entre popup y parent
- **Svelte 5 Runes**: `$state`, `$derived`, `onclick` modernos
- **TypeScript**: Tipado fuerte en todo el proyecto
- **TailwindCSS 4**: Estilos utilitarios modernos
- **Middleware**: Protección de rutas a nivel de servidor

### 📋 Funcionalidades Disponibles
- Login tradicional (username: testuser, password: test123)
- Google OAuth con cuenta Google
- Dashboard protegido
- Redirección automática desde ruta principal
- Manejo de errores y estados de carga
- Persistencia de sesión

## 🔄 **Flujo de Usuario Completo**

### Flujo de Login Tradicional
1. Usuario visita `/` → redirige a `/login`
2. Ingresa username/password en formulario
3. Frontend valida y envía a `/api/v1/auth/login`
4. Backend valida credenciales con bcrypt
5. Frontend recibe JWT y datos del usuario
6. Guarda en localStorage y redirige a `/dashboard`

### Flujo de Google OAuth con Popup
1. Usuario hace clic en "Continuar con Google"
2. **Popup**: Se abre ventana emergente con `/api/v1/auth/google`
3. **Backend**: Redirige a Google OAuth
4. **Google**: Usuario autoriza en popup
5. **Google**: Redirige a `/api/v1/auth/callback?code=xxx`
6. **Frontend**: Callback redirige a backend `/api/v1/auth/callback`
7. **Backend**: Procesa código, obtiene tokens, crea/actualiza usuario
8. **Backend**: Responde con HTML que cierra popup y envía datos via postMessage
9. **Frontend**: Recibe AUTH_SUCCESS, guarda datos, redirige a dashboard

### Gestión de Sesión
- Tokens guardados en localStorage
- Verificación de sesión en middleware
- Redirección automática si no está autenticado
- Persistencia de datos de usuario

### 📋 Próximos Pasos Típicos
- Implementar dashboard
- Registro de usuarios
- Recuperación de contraseña
- Perfil de usuario
- Logout y cierre de sesión

## 🌐 **Despliegue y Entorno**

### Desarrollo Local
- **Frontend**: `http://localhost:4321`
- **Backend**: `http://localhost:8001`
- **Base de Datos**: Neon PostgreSQL

### Producción (Vercel)
- **Hosting**: Vercel (según stack tecnológico definido)
- **Build**: `pnpm build` genera archivos en `./dist/`
- **Preview**: `pnpm preview` para testing local
- **Variables de Entorno**: Configuradas en Vercel Dashboard

### Configuración de Entorno
```bash
# .env (development)
PUBLIC_API_URL=http://localhost:8001
PUBLIC_GOOGLE_CLIENT_ID=tu_google_client_id

# .env (production)
PUBLIC_API_URL=https://tu-backend.com
PUBLIC_GOOGLE_CLIENT_ID=tu_google_client_id_prod
```

## 🔒 **Seguridad Implementada**

### Frontend
- ✅ Middleware para protección de rutas
- ✅ Validación de formularios en cliente
- ✅ Manejo seguro de tokens en localStorage
- ✅ Verificación de origen en postMessage
- ✅ Sanitización de datos de usuario

### Comunicación con Backend
- ✅ HTTPS obligatorio en producción
- ✅ CORS configurado para orígenes específicos
- ✅ Tokens JWT con expiración
- ✅ Manejo de errores sin exponer información sensible

### Google OAuth
- ✅ Flujo OAuth 2.0 estándar
- ✅ Popup con origen verificado
- ✅ Callback seguro y validado
- ✅ No exposición de client secret en frontend
