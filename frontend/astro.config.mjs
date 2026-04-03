// @ts-check
import { defineConfig } from 'astro/config';
import svelte from '@astrojs/svelte';
import tailwindcss from '@tailwindcss/vite';
import vercel from '@astrojs/vercel';
import node from '@astrojs/node';

export default defineConfig({
  output: 'server',
  
  // Configuración del adaptador
  adapter: process.env.VERCEL 
    ? vercel() 
    : node({ 
        mode: 'standalone' 
      }),

  // 🚀 ESTO ES LO QUE FALTA:
  // Forzamos a Astro/Node a escuchar en todas las interfaces (0.0.0.0)
  // y en el puerto que Docker espera (4321)
  server: {
    host: true, // Esto equivale a 0.0.0.0
    port: 4321,
    headers: {
      'Cross-Origin-Opener-Policy': 'unsafe-none',
    },
  },

  integrations: [svelte()],
  
  vite: {
    plugins: [tailwindcss()]
  }
});