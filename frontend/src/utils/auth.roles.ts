// src/utils/auth.roles.ts

export const DASHBOARD_ROLES = ['ADMIN', 'SUPERADMIN'] as const;
export type DashboardRole = typeof DASHBOARD_ROLES[number];

export function canAccessDashboard(role: string): boolean {
  return DASHBOARD_ROLES.includes(role.toUpperCase() as DashboardRole);
}

export function isPendingOrRestricted(role: string): boolean {
  return !canAccessDashboard(role);
}