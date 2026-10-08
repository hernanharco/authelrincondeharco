/**
 * Tests para servicio de autenticación (src/services/authService.ts)
 * Clase AuthService: login(), getCurrentUser(), handleResponse() con fetch
 * `credentials: 'include'` (sesión por cookie httpOnly del backend).
 *
 * El viejo suite testeaba funciones de módulo (logout, getToken,
 * makeAuthenticatedRequest, refreshToken, isAuthenticated, isValidToken,
 * setAuthLoading…) que ya no existen: el storage lo maneja el backend vía
 * cookies httpOnly y esas funciones nunca se implementaron en esta clase.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { authService, AuthService } from '../../src/services/authService';
import { apiUrl, ENDPOINTS } from '../../src/config/api.config';

const mockFetch = vi.fn();

function jsonResponse(body: unknown, ok = true, status = 200): Response {
  return {
    ok,
    status,
    json: () => Promise.resolve(body),
  } as unknown as Response;
}

describe('AuthService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal('fetch', mockFetch);
    localStorage.clear();
  });

  describe('login()', () => {
    it('debería hacer POST a /api/v1/auth/login con credentials include', async () => {
      mockFetch.mockResolvedValue(jsonResponse({ access_token: 't', token_type: 'bearer', user: {} }));

      await authService.login({ username: 'alice', password: 'secret' });

      expect(mockFetch).toHaveBeenCalledWith(apiUrl(ENDPOINTS.auth.login), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: 'alice', password: 'secret' }),
        credentials: 'include',
      });
    });

    it('debería resolver con la respuesta del backend en un login exitoso', async () => {
      const body = {
        access_token: 'jwt',
        token_type: 'bearer',
        user: { id: '1', email: 'a@b.c', username: 'alice', role: 'ADMIN', status: 'active' },
      };
      mockFetch.mockResolvedValue(jsonResponse(body));

      const result = await authService.login({ username: 'alice', password: 'secret' });

      expect(result).toEqual(body);
    });

    it('debería lanzar Error con el `detail` string del backend (401)', async () => {
      mockFetch.mockResolvedValue(jsonResponse({ detail: 'Credenciales inválidas' }, false, 401));

      await expect(authService.login({ username: 'x', password: 'y' })).rejects.toThrow(
        'Credenciales inválidas'
      );
    });

    it('debería lanzar el primer msg de un `detail` array (errores 422 de validación)', async () => {
      const detail = [{ msg: 'Field required' }, { msg: 'Otro error' }];
      mockFetch.mockResolvedValue(jsonResponse({ detail }, false, 422));

      await expect(authService.login({ username: '', password: '' })).rejects.toThrow(
        'Field required'
      );
    });

    it('debería lanzar mensaje genérico cuando no hay `detail` utilizable', async () => {
      mockFetch.mockResolvedValue(jsonResponse({}, false, 500));

      await expect(authService.login({ username: 'a', password: 'b' })).rejects.toThrow(
        'Error en la operación'
      );
    });

    it('debería propagar errores de red sin lanzar nada propio', async () => {
      mockFetch.mockRejectedValue(new Error('Error de red'));

      await expect(authService.login({ username: 'a', password: 'b' })).rejects.toThrow(
        'Error de red'
      );
    });

    it('no debería guardar nada en localStorage (la sesión vive en cookies httpOnly)', async () => {
      mockFetch.mockResolvedValue(jsonResponse({ access_token: 'jwt', token_type: 'bearer', user: {} }));

      await authService.login({ username: 'alice', password: 'secret' });

      expect(localStorage.getItem('session')).toBeNull();
      expect(localStorage.getItem('user')).toBeNull();
      expect(localStorage.length).toBe(0);
    });
  });

  describe('getCurrentUser()', () => {
    it('debería hacer GET a /api/v1/users/me con credentials include', async () => {
      mockFetch.mockResolvedValue(jsonResponse({ id: '1', username: 'alice' }));

      await authService.getCurrentUser();

      expect(mockFetch).toHaveBeenCalledWith(apiUrl(ENDPOINTS.users.me), {
        method: 'GET',
        credentials: 'include',
      });
    });

    it('debería resolver con el usuario cuando la respuesta es ok', async () => {
      const user = { id: '1', email: 'a@b.c', username: 'alice', role: 'ADMIN', status: 'active' };
      mockFetch.mockResolvedValue(jsonResponse(user));

      await expect(authService.getCurrentUser()).resolves.toEqual(user);
    });

    it('debería devolver null cuando la respuesta no es ok (401 sin sesión)', async () => {
      mockFetch.mockResolvedValue(jsonResponse({ detail: 'Not authenticated' }, false, 401));

      await expect(authService.getCurrentUser()).resolves.toBeNull();
    });

    it('debería devolver null cuando falla la red', async () => {
      mockFetch.mockRejectedValue(new Error('network down'));

      await expect(authService.getCurrentUser()).resolves.toBeNull();
    });

    it('debería devolver null cuando el body no es JSON válido', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.reject(new Error('invalid json')),
      } as unknown as Response);

      await expect(authService.getCurrentUser()).resolves.toBeNull();
    });
  });

  describe('exportaciones', () => {
    it('debería exportar el singleton authService como instancia de AuthService', () => {
      expect(authService).toBeInstanceOf(AuthService);
    });

    it('debería exponer login y getCurrentUser como métodos públicos', () => {
      expect(typeof authService.login).toBe('function');
      expect(typeof authService.getCurrentUser).toBe('function');
    });
  });
});
