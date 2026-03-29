/**
 * src/services/authService.ts
 * Responsabilidad: Lógica de negocio de autenticación.
 * Centraliza las llamadas a la API y el flujo de OAuth.
 */
import { apiUrl, ENDPOINTS } from '../config/api.config';

// Interfaces para mantener el tipado fuerte
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    username: string;
    full_name?: string;
    role: string;
    status: string;
  };
}

export interface AuthState {
  isLoading: boolean;
  error: string | null;
  success: string | null;
  user: LoginResponse['user'] | null;
}

export class AuthService {
  /**
   * Login tradicional (Username/Password)
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await fetch(apiUrl(ENDPOINTS.auth.login), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
      credentials: 'include', // Importante para manejar cookies httpOnly de FastAPI
    });

    return this.handleResponse<LoginResponse>(response);
  }

  /**
   * Recuperar usuario logueado (Session check)
   */
  async getCurrentUser(): Promise<LoginResponse['user'] | null> {
    try {
      const response = await fetch(apiUrl(ENDPOINTS.users.me), {
        method: 'GET',
        credentials: 'include',
      });
      if (!response.ok) return null;
      return await response.json();
    } catch {
      return null;
    }
  }

  /**
   * Manejador de respuestas genérico (SRP)
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    const data = await response.json();

    if (!response.ok) {
      const message = typeof data.detail === 'string'
        ? data.detail
        : (Array.isArray(data.detail) ? data.detail[0]?.msg : 'Error en la operación');
      throw new Error(message);
    }

    return data as T;
  }
}

// Exportamos una única instancia (Singleton)
export const authService = new AuthService();