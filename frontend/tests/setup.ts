/**
 * Configuración de tests para AuthCore Frontend
 * Setup de Vitest con jsdom — matchers de jest-dom y globals de storage.
 *
 * NOTA: la configuración de vitest vive en vitest.config.ts
 * (este archivo solo se usa como setupFiles de vitest).
 */
import '@testing-library/jest-dom/vitest';

// Node ≥22 declara `localStorage`/`sessionStorage` experimentales en globalThis
// (sin la flag --localstorage-file devuelven undefined). Como la clave ya existe
// en global, Vitest NO copia la implementación de jsdom (populateGlobal la salta)
// y `window` es globalThis, así que el DOM real hay que leerlo de `globalThis.jsdom`.
const jsdomWindow = (globalThis as { jsdom?: { window: Window } }).jsdom?.window ?? window;

for (const key of ['localStorage', 'sessionStorage'] as const) {
  const jsdomStorage = jsdomWindow?.[key];
  if (jsdomStorage) {
    let storage: Storage = jsdomStorage;
    Object.defineProperty(globalThis, key, {
      configurable: true,
      enumerable: true,
      get: () => storage,
      set: (value: Storage) => {
        storage = value;
      },
    });
  }
}
