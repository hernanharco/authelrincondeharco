/**
 * src/utils/jwt.ts
 * Utilidades puras (sin runtime de Astro) para leer tokens JWT desde cookies.
 *
 * IMPORTANTE: este módulo NO verifica la firma del token (sin crypto).
 * Solo decodifica el payload en base64 para lecturas de conveniencia
 * (exp, role, sub...). La seguridad real la aporta la cookie httpOnly
 * firmada por el backend; aquí no se confía en el payload como autoridad.
 */

/** Reclamos del payload que consume la app (el resto se pasa por alto). */
export interface JwtPayload {
  exp?: number;
  role?: string;
  sub?: string;
  id?: string;
  username?: string;
  email?: string;
  [claim: string]: unknown;
}

/**
 * Decodifica el payload (parte central) de un JWT.
 * Lanza Error si el formato no es `header.payload.signature`
 * o si el payload no es JSON válido (el caller decide la redirección).
 */
export function parseJwtPayload(token: string): JwtPayload {
  const parts = token.split('.');
  if (parts.length !== 3) throw new Error('JWT format invalid');
  // atob + JSON.parse: mismos pasos que el middleware original; sin verificación de firma.
  return JSON.parse(atob(parts[1])) as JwtPayload;
}

/**
 * true si el token tiene `exp` en el pasado.
 * Sin `exp` ⇒ false (token no expira por tiempo).
 * Lanza si el token es inválido (mismas excepciones que parseJwtPayload).
 * @param now segundos Unix (por defecto el reloj actual).
 */
export function isTokenExpired(token: string, now: number = Math.floor(Date.now() / 1000)): boolean {
  const payload = parseJwtPayload(token);
  return Boolean(payload.exp && payload.exp < now);
}
