/**
 * Configuración de tests para AuthCore Frontend
 * Setup de Vitest con Astro y Svelte 5
 */
import { defineConfig } from 'vitest/config';
import { sveltekit } from '@sveltejs/kit/vite';

export default defineConfig({
  plugins: [
    // Plugin para Svelte 5 con Vitest
    sveltekit(),
  ],
  test: {
    // Configuración específica para tests
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    globals: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/**',
        'tests/**',
        '**/*.d.ts',
        '**/*.config.*'
      ],
    },
  },
});
