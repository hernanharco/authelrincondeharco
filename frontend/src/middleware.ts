// src/middleware.ts
import { defineMiddleware } from 'astro:middleware';
import { canAccessDashboard } from '@utils/auth.roles';

// SSOT del origin — viene del entorno, nunca de headers reconstruidos
const SITE_ORIGIN = process.env.SITE_ORIGIN || 'http://localhost:4321';

export const onRequest = defineMiddleware((context, next) => {
  const { url, cookies } = context;

  const publicRoutes = ['/login', '/api/auth', '/_astro', '/favicon.ico', '/public'];
  const isPublicRoute = publicRoutes.some(route => url.pathname.startsWith(route));
  if (isPublicRoute) return next();

  const isProtectedRoute = url.pathname.startsWith('/dashboard') || url.pathname === '/';

  if (isProtectedRoute) {
    const sessionCookie = cookies.get('access_token');
    
    if (!sessionCookie || !sessionCookie.value) {
      const loginUrl = new URL('/login', SITE_ORIGIN);
      loginUrl.searchParams.set('error', 'no_session');
      loginUrl.searchParams.set('redirect', url.pathname + url.search);
      return context.redirect(loginUrl.toString(), 302);
    }

    try {
      const parts = sessionCookie.value.split('.');
      if (parts.length !== 3) throw new Error('JWT format invalid');

      const payload = JSON.parse(atob(parts[1]));
      const now = Math.floor(Date.now() / 1000);

      if (payload.exp && payload.exp < now) {
        cookies.delete('access_token', { path: '/' });
        const expiredUrl = new URL('/login', SITE_ORIGIN);
        expiredUrl.searchParams.set('error', 'expired_token');
        return context.redirect(expiredUrl.toString(), 302);
      }

      if (!canAccessDashboard(payload.role)) {
        return context.redirect(`${SITE_ORIGIN}/login?status=pending`, 302);
      }

      context.locals.user = {
        id: payload.sub || payload.id,
        username: payload.username || payload.email,
        role: payload.role,
        ...payload
      };

    } catch (error) {
      console.error('❌ Error en Middleware AuthCore:', error);
      cookies.delete('access_token', { path: '/' });
      return context.redirect(`${SITE_ORIGIN}/login?error=invalid_token`, 302);
    }
  }

  return next();
});