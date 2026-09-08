import type { APIRoute } from 'astro';

export const POST: APIRoute = async ({ cookies, request }) => {
  // Detectar dominio actual desde el request
  const url = new URL(request.url);
  const host = url.hostname;
  const parts = host.split('.');
  const domain = parts.length > 2 ? '.' + parts.slice(-2).join('.') : host;

  // Borrar cookie con dominio detectado
  cookies.delete('access_token', {
    path: '/',
    domain: domain,
    secure: true,
    httpOnly: true,
    sameSite: 'none',
  });

  // Borrar sin dominio (fallback)
  cookies.delete('access_token', { path: '/' });

  return new Response(JSON.stringify({ success: true }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
};