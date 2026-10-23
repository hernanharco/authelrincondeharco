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

// ── Visualización de rol en listas de miembros de tenant ────────────
// Un tenant NO puede tener membresía SUPERADMIN (MembershipRole lo
// rechaza): ese rol solo existe a nivel global. Igualmente la vista de
// miembros debe mostrarlo, porque es la información que importa a quien
// administra la plataforma.

/**
 * Rol a pintar en el badge de un miembro de tenant.
 *
 * `roleTenant` es el rol de la membresía (user_tenants.role).
 * `roleGlobal` es el rol de plataforma (users.role). Si el global es
 * SUPERADMIN se pinta SUPERADMIN —aunque la membresía diga otra cosa—;
 * en cualquier otro caso se pinta la membresía.
 *
 * Si `roleGlobal` falta (respuesta cacheada o backend sin desplegar el
 * campo) se usa la membresía: el fallback nunca rompe la vista.
 */
export function displayMemberRole(
  roleTenant: string | null | undefined,
  roleGlobal?: string | null,
): string {
  const tenant = (roleTenant ?? '').trim().toUpperCase();
  const global = (roleGlobal ?? '').trim().toUpperCase();
  if (global === 'SUPERADMIN') return 'SUPERADMIN';
  return tenant;
}

/**
 * Tooltip opcional para el badge del miembro.
 *
 * Devuelve un texto que aclara ambos roles cuando el rol global difiere
 * de la membresía (el caso SUPERADMIN, que es el que confunde), y
 * `undefined` cuando coinciden o no hay global: no se pinta nada.
 */
export function memberRoleTooltip(
  roleTenant: string | null | undefined,
  roleGlobal?: string | null,
): string | undefined {
  const tenant = (roleTenant ?? '').trim().toUpperCase();
  const global = (roleGlobal ?? '').trim().toUpperCase();
  if (!global || global === tenant) return undefined;
  const labels: Record<string, string> = {
    SUPERADMIN: 'Superadmin',
    ADMIN: 'Admin',
    MANAGER: 'Manager',
    USER: 'Usuario',
    VIEWER: 'Lector',
    NONE: 'Sin rol',
  };
  const globalLabel = labels[global] ?? global;
  const tenantLabel = labels[tenant] ?? tenant;
  return `Rol global: ${globalLabel} · Rol en este tenant: ${tenantLabel}`;
}
