// src/middleware/index.ts
import { defineMiddleware } from 'astro:middleware';
import { canAccessDashboard } from '@utils/auth.roles';

export const onRequest = defineMiddleware((context, next) => {
  const { url, cookies } = context;

  const publicRoutes = ['/login', '/api/auth', '/_astro', '/favicon.ico'];
  const isPublicRoute = publicRoutes.some(route => url.pathname.startsWith(route));

  if (isPublicRoute) return next();

  if (url.pathname.startsWith('/dashboard')) {
    const sessionCookie = cookies.get('session');
    if (!sessionCookie) {
      return Response.redirect(new URL('/login?error=no_session', url), 302);
    }

    try {
      const parts = sessionCookie.value.split('.');
      if (parts.length !== 3) {
        return Response.redirect(new URL('/login?error=invalid_token', url), 302);
      }

      const payload = JSON.parse(atob(parts[1]));
      const now = Math.floor(Date.now() / 1000);

      if (payload.exp && payload.exp < now) {
        return Response.redirect(new URL('/login?error=expired_token', url), 302);
      }

      if (!canAccessDashboard(payload.role || '')) {
        return Response.redirect(new URL('/login?status=pending', url), 302);
      }

    } catch (error) {
      return Response.redirect(new URL('/login?error=invalid_token', url), 302);
    }
  }

  return next();
});