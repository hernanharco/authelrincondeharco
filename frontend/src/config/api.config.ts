/**
 * src/config/api.config.ts
 * Responsabilidad única: centralizar URLs y rutas de la API.
 */

export const BACKEND_URL = import.meta.env.BACKEND_URL || 'http://localhost:8001';
export const PUBLIC_BACKEND_URL = import.meta.env.PUBLIC_BACKEND_URL || 'http://localhost:8001';

export const ENDPOINTS = {
  auth: {
    login:          '/api/v1/auth/login',
    google:         '/api/v1/auth/google',
    forgotPassword: '/api/v1/auth/forgot-password',
    resetPassword:  '/api/v1/auth/reset-password',
  },
  users: {
    me:      '/api/v1/users/me',
    list:    '/api/v1/users/',
    stats:   '/api/v1/users/stats',
    pending: '/api/v1/users/pending',
    byId:    (id: string) => `/api/v1/users/${id}`,
    role:    (id: string) => `/api/v1/users/${id}/role`,
    status:  (id: string) => `/api/v1/users/${id}/status`,
    lock:    (id: string) => `/api/v1/users/${id}/lock`,
  },
  origins: '/api/v1/users/by-origin',
};

export const apiUrl = (path: string) => `${BACKEND_URL}${path}`;
export const publicApiUrl = (path: string) => `${PUBLIC_BACKEND_URL}${path}`;
