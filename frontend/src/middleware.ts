import { defineMiddleware } from 'astro:middleware';

export const onRequest = defineMiddleware((context, next) => {
  const { url, cookies } = context;

  // Rutas públicas que no requieren autenticación
  const publicRoutes = ['/login', '/api/auth', '/_astro', '/favicon.ico'];

  // Verificar si la ruta actual es pública
  const isPublicRoute = publicRoutes.some(route =>
    url.pathname.startsWith(route)
  );

  // Si es una ruta pública, permitir acceso
  if (isPublicRoute) {
    return next();
  }

  // Verificar rutas protegidas del dashboard
  if (url.pathname.startsWith('/dashboard')) {
    // Leer la cookie de sesión
    const sessionCookie = cookies.get('session');

    if (!sessionCookie) {
      // Redireccionar a login si no hay sesión
      return Response.redirect(new URL('/login?error=no_session', url), 302);
    }

    // Validación básica del token (formato JWT)
    try {
      const token = sessionCookie.value;
      const parts = token.split('.');

      if (parts.length !== 3) {
        return Response.redirect(new URL('/login?error=invalid_token', url), 302);
      }

      // Decodificar el payload para verificar expiración básica
      const payload = JSON.parse(atob(parts[1]));
      const now = Math.floor(Date.now() / 1000);

      if (payload.exp && payload.exp < now) {
        return Response.redirect(new URL('/login?error=expired_token', url), 302);
      }

    } catch (error) {
      console.error('Error validating token format:', error);
      return Response.redirect(new URL('/login?error=invalid_token', url), 302);
    }
  }

  return next();
});
