/**
 * Configuración de Vitest para AuthCore Frontend
 * Compatible con Astro + Svelte 5
 */
import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  // Compilar componentes .svelte dentro de los tests
  plugins: [
    // `src/middleware.ts` importa el módulo virtual `astro:middleware`, que solo
    // existe con el runtime de Astro. En vitest lo resolvemos con un stub mínimo
    // (defineMiddleware es identidad: devuelve el middleware tal cual), para que
    // `onRequest` sea directamente invocable en los tests.
    {
      name: 'stub-astro-middleware',
      enforce: 'pre',
      resolveId(id: string) {
        if (id === 'astro:middleware') return '\0astro:middleware-stub';
        return null;
      },
      load(id: string) {
        if (id === '\0astro:middleware-stub') {
          return 'export const defineMiddleware = (middleware) => middleware;';
        }
        return null;
      },
    },
    svelte({
      // Vitest transforma los módulos en modo SSR, lo que hace que
      // vite-plugin-svelte compile los componentes para el lado servidor
      // (`mount` no existe ahí). Forzar compilación client-side para tests.
      dynamicCompileOptions: ({ compileOptions }) =>
        compileOptions.generate === 'server' ? { generate: 'client' } : undefined,
    }),
  ],

  test: {
    // Entorno de testing
    environment: 'jsdom',
    
    // Archivos de setup
    setupFiles: ['./tests/setup.ts'],
    
    // Globals para testing
    globals: true,
    
    // Cobertura de código
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/**',
        'tests/**',
        '**/*.d.ts',
        '**/*.config.*',
        'dist/**'
      ],
      thresholds: {
        global: {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80
        }
      }
    },
    
    // Tiempo de espera para async
    testTimeout: 10000,
    
    // Hooks personalizados
    hookTimeout: 10000,
    
    // Reporteros personalizados
    reporters: ['verbose'],
    
    // Watch mode
    watchExclude: [
      'node_modules/**',
      'dist/**'
    ]
  },
  
  // Resolver para módulos
  resolve: {
    alias: {
      // Espejo de `paths` en tsconfig.json (Vite no lee tsconfig paths solo).
      '@utils': '/src/utils',
      '@config': '/src/config',
      '@components': '/src/components',
      '@layouts': '/src/layouts',
      '@pages': '/src/pages',
      '@': '/src',
      '$lib': '/src/lib'
    },
    // Los paquetes duales (svelte: exports "browser" vs "default") se resuelven
    // en modo SSR con condición "node", lo que carga el runtime de servidor.
    // En tests (jsdom) necesitamos el runtime de cliente.
    conditions: ['browser']
  }
});
