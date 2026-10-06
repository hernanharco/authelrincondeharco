/**
 * Tests para middleware de rutas (src/middleware.ts)
 * Protección de rutas y redirecciones — cookies httpOnly `access_token`.
 *
 * Nota: la lógica pura (clasificación de rutas, parseo/expiración de JWT)
 * vive en src/utils/guards.ts y src/utils/jwt.ts; aquí se verifica el
 * cableado del middleware con el contexto de Astro (cookies/redirect/locals).
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';

const SITE_ORIGIN = 'http://localhost:4321';

// SITE_ORIGIN se lee al cargar el módulo → fijarlo antes del import dinámico.
process.env.SITE_ORIGIN = SITE_ORIGIN;

const { onRequest } = await import('../src/middleware');

/** Construye un JWT firmado-en-broma (header.payload.signature) con payload ASCII. */
function makeJwt(payload: Record<string, unknown>): string {
  const encode = (obj: Record<string, unknown>) => btoa(JSON.stringify(obj));
  return `${encode({ alg: 'RS256', typ: 'JWT' })}.${encode(payload)}.signature`;
}

interface MockContext {
  url: URL;
  cookies: {
    get: ReturnType<typeof vi.fn>;
    delete: ReturnType<typeof vi.fn>;
  };
  redirect: ReturnType<typeof vi.fn>;
  locals: Record<string, unknown>;
}

function makeContext(location: string, accessToken?: string): MockContext {
  return {
    url: new URL(location, SITE_ORIGIN),
    cookies: {
      // Simula Astro.cookies: solo `access_token` existe en este test.
      get: vi.fn((name: string) =>
        name === 'access_token' && accessToken !== undefined
          ? { name, value: accessToken }
          : undefined
      ),
      delete: vi.fn(),
    },
    redirect: vi.fn(),
    locals: {},
  };
}

const next = vi.fn(() => 'NEXT');

describe('Middleware', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('debería permitir acceso a rutas públicas sin autenticación', () => {
    const context = makeContext('/login');

    const result = onRequest(context, next);

    expect(result).toBe('NEXT');
    expect(context.redirect).not.toHaveBeenCalled();
  });

  it('debería tratar prefijos públicos (/api/auth, /_astro…) como públicos', () => {
    for (const path of ['/api/auth/session', '/_astro/entry.js', '/favicon.ico']) {
      const context = makeContext(path);
      onRequest(context, next);
      expect(context.redirect).not.toHaveBeenCalled();
    }
    expect(next).toHaveBeenCalledTimes(3);
  });

  it('debería dejar pasar rutas de API no protegidas sin token', () => {
    const context = makeContext('/api/v1/auth/login');

    const result = onRequest(context, next);

    expect(result).toBe('NEXT');
    expect(context.redirect).not.toHaveBeenCalled();
  });

  it('debería redirigir a login en rutas protegidas sin token (302, error=no_session)', () => {
    const context = makeContext('/dashboard');

    onRequest(context, next);

    expect(context.redirect).toHaveBeenCalledWith(
      `${SITE_ORIGIN}/login?error=no_session&redirect=%2Fdashboard`,
      302
    );
    expect(next).not.toHaveBeenCalled();
  });

  it('debería proteger también la raíz del sitio', () => {
    const context = makeContext('/');

    onRequest(context, next);

    expect(context.redirect).toHaveBeenCalledWith(
      `${SITE_ORIGIN}/login?error=no_session&redirect=%2F`,
      302
    );
    expect(next).not.toHaveBeenCalled();
  });

  it('debería leer la cookie access_token (no localStorage ni el header Authorization)', () => {
    // El viejo test guardaba el token en localStorage: eso no protege nada hoy.
    localStorage.setItem('session', makeJwt({ sub: 'u1', role: 'ADMIN' }));
    const context = makeContext('/dashboard');

    onRequest(context, next);

    // Sin cookie ⇒ redirect a pesar de que "hay token" en localStorage.
    expect(context.redirect).toHaveBeenCalledWith(
      expect.stringContaining('error=no_session'),
      302
    );
    expect(context.cookies.get).toHaveBeenCalledWith('access_token');
  });

  it('debería permitir acceso a rutas protegidas con token válido', () => {
    const token = makeJwt({
      sub: 'user-1',
      username: 'alice',
      role: 'ADMIN',
      exp: Math.floor(Date.now() / 1000) + 3600,
    });
    const context = makeContext('/dashboard', token);

    const result = onRequest(context, next);

    expect(result).toBe('NEXT');
    expect(context.redirect).not.toHaveBeenCalled();
    expect(context.locals.user).toMatchObject({
      id: 'user-1',
      username: 'alice',
      role: 'ADMIN',
    });
  });

  it('debería tratar tokens sin `exp` como no expirados', () => {
    const token = makeJwt({ sub: 'user-1', role: 'ADMIN' });
    const context = makeContext('/dashboard', token);

    onRequest(context, next);

    expect(context.redirect).not.toHaveBeenCalled();
    expect(context.cookies.delete).not.toHaveBeenCalled();
  });

  it('debería eliminar la cookie y redirigir con error=expired_token si el token expiró', () => {
    const token = makeJwt({
      sub: 'user-1',
      role: 'ADMIN',
      exp: Math.floor(Date.now() / 1000) - 60,
    });
    const context = makeContext('/dashboard', token);

    onRequest(context, next);

    expect(context.cookies.delete).toHaveBeenCalledWith('access_token', { path: '/' });
    expect(context.redirect).toHaveBeenCalledWith(
      `${SITE_ORIGIN}/login?error=expired_token`,
      302
    );
    expect(next).not.toHaveBeenCalled();
  });

  it('debería redirigir a ?status=pending si el rol no puede acceder al dashboard', () => {
    const token = makeJwt({ sub: 'user-1', username: 'bob', role: 'USER' });
    const context = makeContext('/dashboard', token);

    onRequest(context, next);

    expect(context.redirect).toHaveBeenCalledWith(`${SITE_ORIGIN}/login?status=pending`, 302);
    expect(context.cookies.delete).not.toHaveBeenCalled();
    expect(next).not.toHaveBeenCalled();
  });

  it('debería validar el formato del token (≠3 partes ⇒ error=invalid_token)', () => {
    const context = makeContext('/dashboard', 'invalid_format_token');

    onRequest(context, next);

    expect(context.cookies.delete).toHaveBeenCalledWith('access_token', { path: '/' });
    expect(context.redirect).toHaveBeenCalledWith(
      `${SITE_ORIGIN}/login?error=invalid_token`,
      302
    );
    expect(next).not.toHaveBeenCalled();
  });

  it('debería manejar excepciones de decodificación (payload corrupto ⇒ invalid_token)', () => {
    // 3 partes pero el payload no es base64/JSON válido.
    const context = makeContext('/dashboard', 'aaa.!!!corrupto!!!.bbb');

    onRequest(context, next);

    expect(context.cookies.delete).toHaveBeenCalledWith('access_token', { path: '/' });
    expect(context.redirect).toHaveBeenCalledWith(
      `${SITE_ORIGIN}/login?error=invalid_token`,
      302
    );
  });

  it('debería ser eficiente para múltiples rutas protegidas con token válido', () => {
    const token = makeJwt({ sub: 'user-1', role: 'ADMIN' });
    const routes = [
      'http://localhost:4321/dashboard',
      'http://localhost:4321/dashboard/users',
      'http://localhost:4321/dashboard/settings',
    ];

    for (const route of routes) {
      const context = makeContext(route, token);
      expect(onRequest(context, next)).toBe('NEXT');
      expect(context.redirect).not.toHaveBeenCalled();
    }
  });
});
