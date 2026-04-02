export const prerender = false;

import type { APIRoute } from 'astro';

export const POST: APIRoute = async ({ request, cookies }) => {
  try {
    const { token } = await request.json();

    if (!token) {
      return new Response(JSON.stringify({ error: 'Token requerido' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    cookies.set('session', token, {
      httpOnly: true,
      secure: import.meta.env.PROD,
      sameSite: import.meta.env.PROD ? 'strict' : 'lax',
      path: '/',
      maxAge: 60 * 60 * 24, // 24 horas
    });

    return new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch {
    return new Response(JSON.stringify({ error: 'Error interno' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
};
