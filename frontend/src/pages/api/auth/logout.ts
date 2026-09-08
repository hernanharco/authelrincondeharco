import type { APIRoute } from 'astro';

export const POST: APIRoute = async ({ cookies, request }) => {
  // Detectar el dominio actual desde el request
  const url = new URL(request.url);
  const host = url.hostname;
  // Extraer dominio base: "auth.rincom.es" -> ".rincom.es"
  const parts = host.split('.');
  const domain = parts.length > 2 ? '.' + parts.slice(-2).join('.') : host;

  // Borramos la cookie con el dominio correcto
  cookies.delete('access_token', {
    path: '/',
    domain: domain,
    secure: true,
    httpOnly: true,
    sameSite: 'none',
  });

  // Borrado extra sin dominio por si acaso
  cookies.delete('access_token', { path: '/' });

  return new Response(JSON.stringify({ success: true }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
};