import { API_CONFIG } from '@/config/api';
import type { LoginRequest, LoginResponse, User } from '@/types/auth';

// Interface para inyección de dependencias (DIP)
export interface IAuthService {
  login(credentials: LoginRequest): Promise<{ success: boolean; user?: User; error?: string }>;
  loginWithGoogle(token: string): Promise<{ success: boolean; user?: User; error?: string }>;
  logout(): Promise<void>;
  forgotPassword(email: string): Promise<{ success: boolean; message?: string; error?: string }>;
  resetPassword(token: string, newPassword: string): Promise<{ success: boolean; message?: string; error?: string }>;
}

// Implementación concreta (SRP)
export class AuthService implements IAuthService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_CONFIG.baseUrl;
  }

  async login(credentials: LoginRequest): Promise<{ success: boolean; user?: User; error?: string }> {
    try {
      const response = await fetch(`${this.baseUrl}${API_CONFIG.endpoints.auth.login}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
        credentials: 'include',
      });

      const data = await response.json();

      if (!response.ok) {
        const errorMsg = typeof data.detail === 'string' ? data.detail : 'Credenciales incorrectas';
        return { success: false, error: errorMsg };
      }

      return { success: true, user: data.user };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Error desconocido' };
    }
  }

  async loginWithGoogle(token: string): Promise<{ success: boolean; user?: User; error?: string }> {
    try {
      if (!token) {
        return { success: false, error: "No se recibió el token de Google" };
      }

      const response = await fetch(`${this.baseUrl}${API_CONFIG.endpoints.auth.google}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, origin: "google" }),
        credentials: 'include',
      });

      const data = await response.json();

      if (!response.ok) {
        let errorMsg = 'Error en Google Auth';
        if (typeof data.detail === 'string') {
          errorMsg = data.detail;
        } else if (Array.isArray(data.detail)) {
          errorMsg = data.detail[0]?.msg || JSON.stringify(data.detail);
        }
        return { success: false, error: errorMsg };
      }

      return { success: true, user: data.user };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Error en autenticación social' };
    }
  }

  async logout(): Promise<void> {
    try {
      await fetch(`${this.baseUrl}/api/v1/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      });
    } catch (error) {
      console.error('Error en logout:', error);
    }
  }

  async forgotPassword(email: string): Promise<{ success: boolean; message?: string; error?: string }> {
    try {
      const response = await fetch(`${this.baseUrl}${API_CONFIG.endpoints.auth.forgotPassword}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        return { success: false, error: data.detail || 'Error al procesar' };
      }

      return { success: true, message: data.message };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Error desconocido' };
    }
  }

  async resetPassword(token: string, newPassword: string): Promise<{ success: boolean; message?: string; error?: string }> {
    try {
      const response = await fetch(`${this.baseUrl}${API_CONFIG.endpoints.auth.resetPassword}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, newPassword }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        return { success: false, error: data.detail || 'Error al restablecer' };
      }

      return { success: true, message: data.message };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Error desconocido' };
    }
  }
}

// Singleton para inyección de dependencias
export const authService = new AuthService();
