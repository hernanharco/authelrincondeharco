// src/middleware/index.ts
import { defineMiddleware } from 'astro:middleware';
import { canAccessDashboard } from '@utils/auth.roles';

export const onRequest = defineMiddleware((context, next) => {
  const { url, cookies } = context;

  // 1. RUTAS PÚBLICAS Y RECURSOS ESTÁTICOS
  // Añadimos /public y prefijos comunes de Astro para no interceptar estilos/imágenes
  const publicRoutes = ['/login', '/api/auth', '/_astro', '/favicon.ico', '/public'];
  const isPublicRoute = publicRoutes.some(route => url.pathname.startsWith(route));

  if (isPublicRoute) return next();

  // 2. DEFINIR SI LA RUTA REQUIERE AUTENTICACIÓN
  // Protegemos el dashboard y la raíz
  const isProtectedRoute = url.pathname.startsWith('/dashboard') || url.pathname === '/';

  if (isProtectedRoute) {
    /**
     * CAMBIO CLAVE: 
     * Usamos 'access_token' porque es el nombre que tu Backend 
     * ya está usando con éxito en el proyecto de Appointment.
     */
    const sessionCookie = cookies.get('access_token');
    
    // Si no existe la cookie, redirigimos al login preservando el destino
    if (!sessionCookie || !sessionCookie.value) {
      const loginUrl = new URL('/login', url.origin);
      loginUrl.searchParams.set('error', 'no_session');
      // Guardamos la ruta original para que el login sepa a dónde volver
      loginUrl.searchParams.set('redirect', url.pathname + url.search);
      
      return context.redirect(loginUrl.toString(), 302);
    }

    try {
      // 3. VALIDACIÓN LIGERA DEL JWT
      const parts = sessionCookie.value.split('.');
      if (parts.length !== 3) throw new Error('JWT format invalid');

      // Decodificamos el payload (segunda parte del token)
      const payload = JSON.parse(atob(parts[1]));
      const now = Math.floor(Date.now() / 1000);

      // Verificación de expiración (exp)
      if (payload.exp && payload.exp < now) {
        cookies.delete('access_token', { path: '/' });
        const expiredUrl = new URL('/login', url.origin);
        expiredUrl.searchParams.set('error', 'expired_token');
        return context.redirect(expiredUrl.toString(), 302);
      }

      // 4. CONTROL DE ACCESO POR ROLES (RBAC)
      // Usamos la utilidad que definimos antes
      if (!canAccessDashboard(payload.role)) {
        return context.redirect('/login?status=pending', 302);
      }

      // 5. INYECCIÓN EN LOCALS
      // Esto permite usar Astro.locals.user en cualquier página .astro
      context.locals.user = {
        id: payload.sub || payload.id,
        username: payload.username || payload.email,
        role: payload.role,
        ...payload
      };

    } catch (error) {
      console.error('❌ Error en Middleware AuthCore:', error);
      // Si el token es corrupto, limpiamos y fuera
      cookies.delete('access_token', { path: '/' });
      return context.redirect('/login?error=invalid_token', 302);
    }
  }

  return next();
});