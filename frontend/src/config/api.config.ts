/**
 * src/config/api.config.ts
 * Responsabilidad única: centralizar URLs y rutas de la API.
 */

export const BACKEND_URL = import.meta.env.PUBLIC_BACKEND_URL || 'http://localhost:8000';

export const ENDPOINTS = {
  auth: {
    login: '/api/v1/auth/login',
    google: '/api/v1/auth/google',
    logout: '/api/v1/auth/logout',
  },
  users: {
    me: '/api/v1/users/me',
    list: '/api/v1/users/',
    search: '/api/v1/users/search',
    stats: '/api/v1/users/stats',
    pending: '/api/v1/users/pending',
    byOrigin: '/api/v1/users/by-origin',
    byId: (id: string) => `/api/v1/users/${id}`,
    role: (id: string) => `/api/v1/users/${id}/role`,
    status: (id: string) => `/api/v1/users/${id}/status`,
    lock: (id: string) => `/api/v1/users/${id}/lock`,
    activity: (id: string) => `/api/v1/users/${id}/activity`,
    profile: (id: string) => `/api/v1/users/${id}/profile`,
    resetPassword: (id: string) => `/api/v1/users/${id}/reset-password`,
    notes: (id: string) => `/api/v1/users/${id}/notes`,
    bulkUpdate: '/api/v1/users/bulk-update',
  },
};

export const apiUrl = (path: string) => `${BACKEND_URL}${path}`;
export const publicApiUrl = (path: string) => `${BACKEND_URL}${path}`;
