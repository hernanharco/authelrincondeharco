import type { APIRoute } from 'astro';

export const POST: APIRoute = async ({ cookies, request }) => {
  // Detectar dominio actual desde el request
  const url = new URL(request.url);
  const host = url.hostname;
  const parts = host.split('.');
  const domain = parts.length > 2 ? '.' + parts.slice(-2).join('.') : host;

  // Borrar cookie con las MISMAS attributes con las que se creó
  // La cookie se crea en google.py con: httponly, samesite=none, secure, domain=.rincom.es
  const cookieParts = [
    'access_token=deleted',
    'Path=/',
    `Domain=${domain}`,
    'Expires=Thu, 01 Jan 1970 00:00:00 GMT',
    'HttpOnly',
    'Secure',
    'SameSite=None',
  ];

  return new Response(JSON.stringify({ success: true }), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Set-Cookie': cookieParts.join('; '),
    },
  });
};
