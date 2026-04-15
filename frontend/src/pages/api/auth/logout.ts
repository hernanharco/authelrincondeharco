import type { APIRoute } from 'astro';

export const POST: APIRoute = async ({ cookies }) => {
  const domain = '.elrincondeharco.com'; 

  // Borramos la cookie con la configuración exacta que tiene en el navegador
  cookies.delete('access_token', {
    path: '/',
    domain: domain,
    secure: true,
    httpOnly: true,
    sameSite: 'none' // Según tu captura, aparece como 'None'
  });

  // Un borrado extra sin dominio por si las moscas
  cookies.delete('access_token', { path: '/' });

  return new Response(JSON.stringify({ success: true }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' }
  });
};