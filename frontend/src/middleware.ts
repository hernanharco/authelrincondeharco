// src/middleware.ts
import { defineMiddleware } from 'astro:middleware';
import { canAccessDashboard } from '@utils/auth.roles';
import { isPublicRoute, isProtectedRoute } from '@utils/guards';
import { parseJwtPayload, isTokenExpired } from '@utils/jwt';

// SSOT del origin — viene del entorno, nunca de headers reconstruidos
const SITE_ORIGIN = process.env.SITE_ORIGIN || 'http://localhost:4321';

export const onRequest = defineMiddleware((context, next) => {
  const { url, cookies } = context;

  if (isPublicRoute(url.pathname)) return next();

  if (isProtectedRoute(url.pathname)) {
    const sessionCookie = cookies.get('access_token');
    
    if (!sessionCookie || !sessionCookie.value) {
      const loginUrl = new URL('/login', SITE_ORIGIN);
      loginUrl.searchParams.set('error', 'no_session');
      loginUrl.searchParams.set('redirect', url.pathname + url.search);
      return context.redirect(loginUrl.toString(), 302);
    }

    try {
      if (isTokenExpired(sessionCookie.value)) {
        cookies.delete('access_token', { path: '/' });
        const expiredUrl = new URL('/login', SITE_ORIGIN);
        expiredUrl.searchParams.set('error', 'expired_token');
        return context.redirect(expiredUrl.toString(), 302);
      }

      const payload = parseJwtPayload(sessionCookie.value);

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
