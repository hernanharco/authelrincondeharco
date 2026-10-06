/**
 * Tests unitarios de src/utils/jwt.ts (lógica pura extraída del middleware)
 * Nota: parseJwtPayload NO verifica firmas; aquí se comprueba solo decodificación.
 */
import { describe, it, expect } from 'vitest';
import { parseJwtPayload, isTokenExpired, type JwtPayload } from '../../src/utils/jwt';

function makeJwt(payload: Record<string, unknown>, signature = 'signature'): string {
  const encode = (obj: Record<string, unknown>) => btoa(JSON.stringify(obj));
  return `${encode({ alg: 'RS256', typ: 'JWT' })}.${encode(payload)}.${signature}`;
}

describe('parseJwtPayload', () => {
  it('decodifica el payload base64 central', () => {
    const token = makeJwt({ sub: 'u1', role: 'ADMIN', exp: 1700000000 });

    expect(parseJwtPayload(token)).toEqual({ sub: 'u1', role: 'ADMIN', exp: 1700000000 });
  });

  it('ignora la firma (no hay verificación criptográfica)', () => {
    // Firma basura: el parseo igual funciona — documentado en el docstring.
    const token = makeJwt({ sub: 'u1' }, 'firma-totalmente-falsa');

    expect(parseJwtPayload(token)).toEqual({ sub: 'u1' });
  });

  it('lanza Error si no hay exactamente 3 partes', () => {
    expect(() => parseJwtPayload('solo.una')).toThrow('JWT format invalid');
    expect(() => parseJwtPayload('a.b.c.d')).toThrow('JWT format invalid');
    expect(() => parseJwtPayload('')).toThrow('JWT format invalid');
  });

  it('lanza Error si el payload no es JSON válido', () => {
    expect(() => parseJwtPayload('aaa.!!!!.ccc')).toThrow();
  });
});

describe('isTokenExpired', () => {
  const NOW = 1_700_000_000;

  it('false si exp está en el futuro', () => {
    const token = makeJwt({ exp: NOW + 60 });
    expect(isTokenExpired(token, NOW)).toBe(false);
  });

  it('true si exp está en el pasado', () => {
    const token = makeJwt({ exp: NOW - 60 });
    expect(isTokenExpired(token, NOW)).toBe(true);
  });

  it('false en el límite exacto (exp === now no expira)', () => {
    const token = makeJwt({ exp: NOW });
    expect(isTokenExpired(token, NOW)).toBe(false);
  });

  it('false si el token no tiene exp', () => {
    const token = makeJwt({ sub: 'u1' });
    expect(isTokenExpired(token, NOW)).toBe(false);
  });

  it('usa el reloj actual por defecto', () => {
    const past = makeJwt({ exp: Math.floor(Date.now() / 1000) - 10 });
    const future = makeJwt({ exp: Math.floor(Date.now() / 1000) + 10 });

    expect(isTokenExpired(past)).toBe(true);
    expect(isTokenExpired(future)).toBe(false);
  });

  it('propaga la excepción de parseo para tokens inválidos', () => {
    expect(() => isTokenExpired('token-roto', NOW)).toThrow('JWT format invalid');
  });

  it('acepta cualquier reclamo desconocido en el payload', () => {
    const payload: JwtPayload = parseJwtPayload(makeJwt({ custom: { nested: true }, exp: NOW + 1 }));
    expect(payload.custom).toEqual({ nested: true });
  });
});
