/**
 * Tests unitarios de src/utils/guards.ts (clasificación de rutas extraída del middleware)
 */
import { describe, it, expect } from 'vitest';
import { PUBLIC_ROUTES, isPublicRoute, isProtectedRoute } from '../../src/utils/guards';

describe('isPublicRoute', () => {
  it('las rutas públicas no exigen sesión', () => {
    for (const route of PUBLIC_ROUTES) {
      expect(isPublicRoute(route)).toBe(true);
    }
  });

  it('reconoce prefijos con subrutas', () => {
    expect(isPublicRoute('/login')).toBe(true);
    expect(isPublicRoute('/api/auth/callback')).toBe(true);
    expect(isPublicRoute('/_astro/hoisted.abc.js')).toBe(true);
  });

  it('cualquier otra ruta no es pública', () => {
    expect(isPublicRoute('/dashboard')).toBe(false);
    expect(isPublicRoute('/')).toBe(false);
    expect(isPublicRoute('/api/v1/users')).toBe(false);
  });
});

describe('isProtectedRoute', () => {
  it('protege el dashboard (cualquier subruta)', () => {
    expect(isProtectedRoute('/dashboard')).toBe(true);
    expect(isProtectedRoute('/dashboard/users/1')).toBe(true);
  });

  it('protege la raíz del sitio', () => {
    expect(isProtectedRoute('/')).toBe(true);
  });

  it('no protege rutas de login ni APIs', () => {
    expect(isProtectedRoute('/login')).toBe(false);
    expect(isProtectedRoute('/api/v1/auth/login')).toBe(false);
  });
});
