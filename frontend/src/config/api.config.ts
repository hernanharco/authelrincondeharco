/**
 * src/config/api.config.ts
 * Responsabilidad: Centralizar la configuración de red y rutas.
 */

export const API_CONFIG = {
  // Prioriza variable de entorno (Astro/Vite), sino usa el puerto por defecto de FastAPI
  baseUrl: import.meta.env.BACKEND_AUTH_URL || 'http://localhost:8000',

  // Añadimos la URL del módulo ConnectGoogle
  // En local será la carpeta o puerto donde corras ese micro-frontend
  // En producción será la URL de Vercel
  connectGoogleUrl: import.meta.env.PUBLIC_CONNECT_GOOGLE_URL || 'http://localhost:4321/google-auth',
  
  endpoints: {
    auth: {
      login: '/api/v1/auth/login',
      google: '/api/v1/auth/google',
      forgotPassword: '/api/v1/auth/forgot-password',
      resetPassword: '/api/v1/auth/reset-password',
    },
    users: {
      me: '/api/v1/users/me',
    },
  },
};

/**
 * Helper para construir URLs completas sin repetir lógica de concatenación
 */
export const getApiUrl = (path: string): string => `${API_CONFIG.baseUrl}${path}`;