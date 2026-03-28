import { defineMiddleware } from 'astro:middleware';

export const onRequest = defineMiddleware((context, next) => {
  const { url, request, cookies } = context;
  
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
    // Leer la cookie de sesión httpOnly
    const sessionCookie = cookies.get('session');
    
    if (!sessionCookie) {
      // Redireccionar a login si no hay sesión
      return Response.redirect(new URL('/login', url), 302);
    }
    
    // Opcional: Validar el token con el backend
    // Esto se puede hacer aquí o en el cliente
    try {
      // Por ahora, solo verificamos que exista la cookie
      // En el futuro, podríamos validar el token aquí
    } catch (error) {
      // Si hay error en la validación, redireccionar a login
      return Response.redirect(new URL('/login', url), 302);
    }
  }
  
  return next();
});
