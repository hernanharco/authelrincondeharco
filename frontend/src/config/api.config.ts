/**
 * src/config/api.config.ts
 * Responsabilidad única: centralizar URLs y rutas de la API.
 */

// En SSR (server-side dentro del contenedor Docker), usamos API_TARGET que apunta al servicio interno
// En cliente (browser), usamos PUBLIC_BACKEND_URL que es accesible desde el navegador
export const BACKEND_URL = import.meta.env.SSR
  ? (process.env.API_TARGET || 'http://localhost:8000')
  : (import.meta.env.PUBLIC_BACKEND_URL || 'http://localhost:8000');

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
  company: {
    list: '/api/v1/company/',
    me: '/api/v1/company/me',
    byId: (userId: number | string) => `/api/v1/company/${userId}`,
    create: (userId: number | string) => `/api/v1/company/${userId}`,
    update: (userId: number | string) => `/api/v1/company/${userId}`,
    upsert: (userId: number | string) => `/api/v1/company/${userId}/upsert`,
    delete: (userId: number | string) => `/api/v1/company/${userId}`,
  },
  tenants: {
    list: '/api/v1/tenants/',
    byId: (id: string) => `/api/v1/tenants/${id}`,
    bySlug: (slug: string) => `/api/v1/tenants/by-slug/${slug}`,
    modules: (tenantId: string) => `/api/v1/tenant-modules/tenants/${tenantId}/modules`,
    assignModule: (tenantId: string) => `/api/v1/tenant-modules/tenants/${tenantId}/modules`,
    updateModule: (tenantId: string, moduleId: string) =>
      `/api/v1/tenant-modules/tenants/${tenantId}/modules/${moduleId}`,
    removeModule: (tenantId: string, moduleId: string) =>
      `/api/v1/tenant-modules/tenants/${tenantId}/modules/${moduleId}`,
  },
  modules: {
    list: '/api/v1/modules/',
    byId: (id: string) => `/api/v1/modules/${id}`,
  },
};

export const apiUrl = (path: string) => `${BACKEND_URL}${path}`;
export const publicApiUrl = (path: string) => `${BACKEND_URL}${path}`;
