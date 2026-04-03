/**
 * Tests para servicio de autenticación
 * Manejo de tokens, llamadas API y estado
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock de fetch global
const mockFetch = vi.fn();

describe('AuthService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mockear fetch global
    vi.stubGlobal('fetch', mockFetch);
    // Limpiar localStorage
    localStorage.clear();
  });

  it('debería guardar token en localStorage', () => {
    const mockToken = 'mock_jwt_token';
    const mockUser = { id: 1, username: 'testuser' };

    // Simular login exitoso
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        access_token: mockToken,
        user: mockUser
      })
    });

    // Importar y usar el servicio
    const { login } = require('../../src/services/authService.ts');

    login('testuser', 'testpass');

    expect(localStorage.getItem('session')).toBe(mockToken);
    expect(localStorage.getItem('user')).toBe(JSON.stringify(mockUser));
  });

  it('debería manejar error de login', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: () => Promise.resolve({
        detail: 'Credenciales inválidas'
      })
    });

    const { login } = require('../../src/services/authService.ts');

    try {
      await login('wronguser', 'wrongpass');
      expect.fail('Debería haber lanzado error');
    } catch (error) {
      expect(error.message).toBe('Credenciales inválidas');
    }

    expect(localStorage.getItem('session')).toBeNull();
  });

  it('debería eliminar token al hacer logout', () => {
    // Configurar token inicial
    localStorage.setItem('session', 'mock_token');
    localStorage.setItem('user', JSON.stringify({ id: 1 }));

    const { logout } = require('../../src/services/authService.ts');

    logout();

    expect(localStorage.getItem('session')).toBeNull();
    expect(localStorage.getItem('user')).toBeNull();
  });

  it('debería verificar si usuario está autenticado', () => {
    const { isAuthenticated } = require('../../src/services/authService.ts');

    // Sin token
    expect(isAuthenticated()).toBe(false);

    // Con token
    localStorage.setItem('session', 'mock_token');
    expect(isAuthenticated()).toBe(true);
  });

  it('debería obtener usuario actual', () => {
    const mockUser = { id: 1, username: 'testuser', email: 'test@example.com' };
    localStorage.setItem('user', JSON.stringify(mockUser));

    const { getCurrentUser } = require('../../src/services/authService.ts');

    expect(getCurrentUser()).toEqual(mockUser);
  });

  it('debería obtener token actual', () => {
    const mockToken = 'mock_jwt_token';
    localStorage.setItem('session', mockToken);

    const { getToken } = require('../../src/services/authService.ts');

    expect(getToken()).toBe(mockToken);
  });

  it('debería manejar token expirado', () => {
    // Simular respuesta 401
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: () => Promise.resolve({
        detail: 'Token expirado'
      })
    });

    const { makeAuthenticatedRequest } = require('../../src/services/authService.ts');

    // Configurar token
    localStorage.setItem('session', 'expired_token');

    return makeAuthenticatedRequest('/api/v1/users/me')
      .then(() => expect.fail('Debería haber fallado'))
      .catch(error => {
        expect(error.message).toBe('Token expirado');
        expect(localStorage.getItem('session')).toBeNull();
      });
  });

  it('debería incluir headers de autorización', async () => {
    const mockToken = 'mock_jwt_token';
    localStorage.setItem('session', mockToken);

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ data: 'success' })
    });

    const { makeAuthenticatedRequest } = require('../../src/services/authService.ts');

    await makeAuthenticatedRequest('/api/v1/users/me');

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/v1/users/me',
      expect.objectContaining({
        headers: expect.objectContaining({
          'Authorization': `Bearer ${mockToken}`,
          'Content-Type': 'application/json'
        })
      })
    );
  });

  it('debería manejar errores de red', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Error de red'));

    const { login } = require('../../src/services/authService.ts');

    try {
      await login('testuser', 'testpass');
      expect.fail('Debería haber lanzado error');
    } catch (error) {
      expect(error.message).toBe('Error de red');
    }
  });

  it('debería refrescar token', async () => {
    const newToken = 'new_jwt_token';
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        access_token: newToken,
        user: { id: 1, username: 'testuser' }
      })
    });

    const { refreshToken } = require('../../src/services/authService.ts');

    await refreshToken();

    expect(localStorage.getItem('session')).toBe(newToken);
  });

  it('debería validar formato de token', () => {
    const { isValidToken } = require('../../src/services/authService.ts');

    // Token inválido (no JWT)
    expect(isValidToken('invalid_token')).toBe(false);

    // Token JWT válido simulado
    const mockJWT = 'header.payload.signature';
    expect(isValidToken(mockJWT)).toBe(true);
  });

  it('debería manejar estado de carga', () => {
    const { setAuthLoading } = require('../../src/services/authService.ts');
    const { getAuthLoading } = require('../../src/services/authService.ts');

    expect(getAuthLoading()).toBe(false);

    setAuthLoading(true);
    expect(getAuthLoading()).toBe(true);

    setAuthLoading(false);
    expect(getAuthLoading()).toBe(false);
  });

  it('debería persistir estado entre recargas', () => {
    // Simular evento de recarga
    const mockStorageEvent = new StorageEvent('storage', {
      key: 'session',
      newValue: 'new_token'
    });

    // Disparar evento
    window.dispatchEvent(mockStorageEvent);

    // Verificar que el servicio detecta el cambio
    const { getToken } = require('../../src/services/authService.ts');
    expect(getToken()).toBe('new_token');
  });

  it('debería limpiar datos sensibles al logout', () => {
    // Configurar múltiples datos
    localStorage.setItem('session', 'token');
    localStorage.setItem('user', 'user_data');
    localStorage.setItem('preferences', 'user_prefs');

    const { logout } = require('../../src/services/authService.ts');

    logout();

    // Solo debe limpiar datos de autenticación
    expect(localStorage.getItem('session')).toBeNull();
    expect(localStorage.getItem('user')).toBeNull();
    // No debe limpiar preferencias
    expect(localStorage.getItem('preferences')).toBe('user_prefs');
  });
});
