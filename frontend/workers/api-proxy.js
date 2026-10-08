/**
 * Cloudflare Worker — API Proxy
 *
 * Rutea /api/* desde app.tudominio.com hacia el backend en Hetzner/Dokploy.
 *
 * ── Cómo funciona ─────────────────────────────────────────────
 * El Worker se ejecuta SOLO cuando alguien visita /api/* en tu dominio.
 * El resto del tráfico va directo a Vercel sin pasar por el Worker.
 *
 * ── Setup en Cloudflare Dashboard ────────────────────────────
 *
 * 1. DNS: app.tudominio.com → CNAME → cname.vercel-dns.com
 *    (esto ya lo tenés si Vercel maneja el dominio)
 *
 * 2. Workers & Pages → Create Worker → pegar este código
 *    Nombre sugerido: "api-proxy"
 *
 * 3. Workers & Pages → Routes → Add Route:
 *    Route: app.tudominio.com/api/*
 *    Worker: api-proxy
 *
 * 4. Workers & Pages → api-proxy → Settings → Variables:
 *    API_BACKEND_URL = https://api.tudominio.com
 *    (la URL directa de Dokploy o el dominio del backend)
 *
 * ── Variables de entorno ─────────────────────────────────────
 * API_BACKEND_URL: URL base del backend en Hetzner/Dokploy
 *   (ej: https://api.tudominio.com o https://dokploy-ip:8000)
 * ─────────────────────────────────────────────────────────────
 */

const DEFAULT_BACKEND = 'http://localhost:8000';

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const backend = env.API_BACKEND_URL || DEFAULT_BACKEND;

    // ── 1. CORS Preflight ──
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        status: 204,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
          'Access-Control-Allow-Headers': '*',
          'Access-Control-Max-Age': '86400',
        },
      });
    }

    // ── 2. Construir URL destino ──
    const targetUrl = `${backend}${url.pathname}${url.search}`;

    // ── 3. Reenviar request manteniendo headers originales ──
    const response = await fetch(targetUrl, {
      method: request.method,
      headers: request.headers,
      body: request.body,
    });

    // ── 4. Armar respuesta con CORS headers ──
    const responseHeaders = new Headers(response.headers);
    responseHeaders.set('Access-Control-Allow-Origin', '*');
    responseHeaders.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, PATCH, OPTIONS');
    responseHeaders.set('Access-Control-Allow-Headers', '*');

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  },
};
