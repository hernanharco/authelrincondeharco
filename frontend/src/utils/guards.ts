/**
 * src/utils/guards.ts
 * Guardas de rutas puras (sin runtime de Astro) usadas por src/middleware.ts.
 * Extraídas del middleware para poder unit-testear la clasificación de rutas.
 */

/** Prefijos de ruta siempre públicos (sin sesión requerida). */
export const PUBLIC_ROUTES = ['/login', '/api/auth', '/_astro', '/favicon.ico', '/public'] as const;

/** true si la ruta empieza por alguno de los prefijos públicos. */
export function isPublicRoute(pathname: string): boolean {
  return PUBLIC_ROUTES.some(route => pathname.startsWith(route));
}

/** true si la ruta exige cookie de sesión válida (dashboard o raíz). */
export function isProtectedRoute(pathname: string): boolean {
  return pathname.startsWith('/dashboard') || pathname === '/';
}
