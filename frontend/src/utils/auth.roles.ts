// src/utils/auth.roles.ts

/**
 * Roles que tienen permiso explícito para entrar al Dashboard principal.
 * Usamos 'as const' para que TypeScript cree un tipo literal exacto.
 */
export const DASHBOARD_ROLES = ['ADMIN', 'SUPERADMIN'] as const;

// Creamos el tipo basado en el array para autocompletado en todo el proyecto
export type DashboardRole = typeof DASHBOARD_ROLES[number];

/**
 * Verifica si un rol tiene permisos de acceso.
 * Convertimos a uppercase para evitar errores por mayúsculas/minúsculas del backend.
 */
export function canAccessDashboard(role: string | null | undefined): boolean {
  if (!role) return false;
  
  const upperRole = role.toUpperCase();
  // Verificamos si el rol está incluido en nuestra lista blanca
  return DASHBOARD_ROLES.includes(upperRole as DashboardRole);
}

/**
 * Determina si el usuario debe ser enviado a la vista de "Pendiente de Aprobación".
 */
export function isPendingOrRestricted(role: string | null | undefined): boolean {
  // Si no puede entrar al dashboard, por defecto es un usuario restringido o pendiente
  return !canAccessDashboard(role);
}