/**
 * Tests para middleware de rutas
 * Protección de rutas y redirecciones
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';

describe('Middleware', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Limpiar localStorage
    localStorage.clear();
    // Mockear URL
    vi.stubGlobal('URL', {
      searchParams: new URLSearchParams()
    });
  });

  it('debería permitir acceso a rutas públicas sin autenticación', () => {
    const mockAstro = {
      redirect: vi.fn(),
    };
    vi.stubGlobal('Astro', mockAstro);

    // Importar middleware
    const middleware = require('../../src/middleware.ts').onRequest;

    // Simular ruta pública
    const mockContext = {
      url: new URL('http://localhost:4321/login'),
      request: { headers: { get: vi.fn(() => null) } }
    };

    const result = middleware(mockContext);

    expect(result).toBeUndefined();
    expect(mockAstro.redirect).not.toHaveBeenCalled();
  });

  it('debería redirigir a login en rutas protegidas sin token', () => {
    const mockAstro = {
      redirect: vi.fn(),
    };
    vi.stubGlobal('Astro', mockAstro);

    const middleware = require('../../src/middleware.ts').onRequest;

    // Simular ruta protegida sin token
    const mockContext = {
      url: new URL('http://localhost:4321/dashboard'),
      request: { headers: { get: vi.fn(() => null) } }
    };

    middleware(mockContext);

    expect(mockAstro.redirect).toHaveBeenCalledWith('/login');
  });

  it('debería permitir acceso a rutas protegidas con token válido', () => {
    const mockAstro = {
      redirect: vi.fn(),
    };
    vi.stubGlobal('Astro', mockAstro);

    const middleware = require('../../src/middleware.ts').onRequest;

    // Simular token en localStorage
    localStorage.setItem('session', 'valid_token');

    const mockContext = {
      url: new URL('http://localhost:4321/dashboard'),
      request: { headers: { get: vi.fn(() => 'Bearer valid_token') } }
    };

    const result = middleware(mockContext);

    expect(result).toBeUndefined();
    expect(mockAstro.redirect).not.toHaveBeenCalled();
  });

  it('debería redirigir al dashboard si está autenticado en login', () => {
    const mockAstro = {
      redirect: vi.fn(),
    };
    vi.stubGlobal('Astro', mockAstro);

    const middleware = require('../../src/middleware.ts').onRequest;

    // Simular usuario autenticado
    localStorage.setItem('session', 'valid_token');

    const mockContext = {
      url: new URL('http://localhost:4321/login'),
      request: { headers: { get: vi.fn(() => 'Bearer valid_token') } }
    };

    middleware(mockContext);

    expect(mockAstro.redirect).toHaveBeenCalledWith('/dashboard');
  });

  it('debería manejar rutas de API', () => {
    const mockAstro = {
      redirect: vi.fn(),
    };
    vi.stubGlobal('Astro', mockAstro);

    const middleware = require('../../src/middleware.ts').onRequest;

    // Simular ruta de API
    const mockContext = {
      url: new URL('http://localhost:4321/api/v1/auth/login'),
      request: { headers: { get: vi.fn(() => null) } }
    };

    const result = middleware(mockContext);

    expect(result).toBeUndefined();
    expect(mockAstro.redirect).not.toHaveBeenCalled();
  });

  it('debería extraer token de headers correctamente', () => {
    const mockAstro = {
      redirect: vi.fn(),
    };
    vi.stubGlobal('Astro', mockAstro);

    const middleware = require('../../src/middleware.ts').onRequest;

    // Mock de headers con diferentes formatos
    const testCases = [
      { header: 'Bearer token123', expected: 'token123' },
      { header: 'token123', expected: 'token123' },
      { header: null, expected: null },
      { header: undefined, expected: null }
    ];

    testCases.forEach(({ header, expected }) => {
      const mockContext = {
        url: new URL('http://localhost:4321/dashboard'),
        request: { headers: { get: vi.fn(() => header) } }
      };

      localStorage.setItem('session', expected || 'fallback_token');

      middleware(mockContext);

      if (expected) {
        expect(mockAstro.redirect).not.toHaveBeenCalled();
      } else {
        expect(mockAstro.redirect).toHaveBeenCalledWith('/login');
      }
    });
  });

  it('debería manejar rutas con parámetros', () => {
    const mockAstro = {
      redirect: vi.fn(),
    };
    vi.stubGlobal('Astro', mockAstro);

    const middleware = require('../../src/middleware.ts').onRequest;

    // Simular ruta con parámetros
    localStorage.setItem('session', 'valid_token');

    const mockContext = {
      url: new URL('http://localhost:4321/dashboard/users/123'),
      request: { headers: { get: vi.fn(() => 'Bearer valid_token') } }
    };

    const result = middleware(mockContext);

    expect(result).toBeUndefined();
    expect(mockAstro.redirect).not.toHaveBeenCalled();
  });

  it('debería validar formato de token', () => {
    const mockAstro = {
      redirect: vi.fn(),
    };
    vi.stubGlobal('Astro', mockAstro);

    const middleware = require('../../src/middleware.ts').onRequest;

    // Token con formato inválido
    localStorage.setItem('session', 'invalid_format_token');

    const mockContext = {
      url: new URL('http://localhost:4321/dashboard'),
      request: { headers: { get: vi.fn(() => 'invalid_format_token') } }
    };

    middleware(mockContext);

    expect(mockAstro.redirect).toHaveBeenCalledWith('/login');
  });

  it('debería manejar excepciones', () => {
    const mockAstro = {
      redirect: vi.fn(),
    };
    vi.stubGlobal('Astro', mockAstro);

    const middleware = require('../../src/middleware.ts').onRequest;

    // Simular error en URL
    const mockContext = {
      url: null,
      request: { headers: { get: vi.fn(() => null) } }
    };

    const result = middleware(mockContext);

    // Debería manejar el error y redirigir a login
    expect(mockAstro.redirect).toHaveBeenCalledWith('/login');
  });

  it('debería ser eficiente para múltiples rutas', () => {
    const mockAstro = {
      redirect: vi.fn(),
    };
    vi.stubGlobal('Astro', mockAstro);

    const middleware = require('../../src/middleware.ts').onRequest;

    localStorage.setItem('session', 'valid_token');

    // Probar múltiples rutas rápidamente
    const routes = [
      'http://localhost:4321/dashboard',
      'http://localhost:4321/dashboard/users',
      'http://localhost:4321/dashboard/settings'
    ];

    routes.forEach(route => {
      const mockContext = {
        url: new URL(route),
        request: { headers: { get: vi.fn(() => 'Bearer valid_token') } }
      };

      const result = middleware(mockContext);
      expect(result).toBeUndefined();
    });

    // No debería haber redirigido en ningún caso
    expect(mockAstro.redirect).not.toHaveBeenCalled();
  });

  it('debería limpiar estado al cerrar sesión', () => {
    const mockAstro = {
      redirect: vi.fn(),
    };
    vi.stubGlobal('Astro', mockAstro);

    const middleware = require('../../src/middleware.ts').onRequest;

    // Configurar token
    localStorage.setItem('session', 'valid_token');

    // Simular cierre de sesión
    localStorage.removeItem('session');

    const mockContext = {
      url: new URL('http://localhost:4321/dashboard'),
      request: { headers: { get: vi.fn(() => null) } }
    };

    middleware(mockContext);

    expect(mockAstro.redirect).toHaveBeenCalledWith('/login');
  });
});
