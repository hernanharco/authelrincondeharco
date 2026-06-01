// @ts-check
import { defineConfig } from 'astro/config';
import svelte from '@astrojs/svelte';
import tailwindcss from '@tailwindcss/vite';
import vercel from '@astrojs/vercel';
import node from '@astrojs/node';

// ── Proxy target configurable ──────────────────────────────────
// En local sin Docker: usa localhost:8000
// En Docker: se setea API_TARGET=http://backend:8000
const API_TARGET = process.env.API_TARGET || 'http://localhost:8000';

export default defineConfig({
  output: 'server',
  
  // Seguridad: Aquí es donde evitamos el error 403
  security: {
    checkOrigin: false,
    exclude: ['/api/auth/logout'] // Permitimos el logout sin validación estricta de origen
  },
  
  // Configuración del adaptador
  adapter: process.env.VERCEL 
    ? vercel() 
    : node({ 
        mode: 'standalone',
        trustForwardedHeaders: true,
      }),

  server: {
    host: true, // Escucha en todas las interfaces
    port: 4321,
    headers: {
      'Cross-Origin-Opener-Policy': 'unsafe-none',
    },
  },

  integrations: [svelte()],
  
  vite: {
    plugins: [tailwindcss()],
    server: {
      proxy: {
        '/api': {
          target: API_TARGET,
          changeOrigin: true,
        },
      },
    },
  }
});