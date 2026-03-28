// src/services/authService.ts

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

export interface ApiErrorResponse {
  detail: string | { msg: string }[];
}

export type User = LoginResponse['user'];

export interface AuthError {
  message: string;
  field?: string;
}

export interface AuthState {
  isLoading: boolean;
  error: AuthError | null;
  success: string | null;
  user: User | null;
}

const API_CONFIG = {
  baseUrl: import.meta.env.PUBLIC_API_URL || 'http://localhost:8000',
  endpoints: {
    auth: {
      login: '/api/v1/auth/login',
      google: '/api/v1/auth/google',
      forgotPassword: '/api/v1/auth/forgot-password',
      resetPassword: '/api/v1/auth/reset-password',
    },
    users: {
      base: '/api/v1/users',
      me: '/api/v1/users/me',
    },
  },
};

export class AuthService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_CONFIG.baseUrl;
  }

  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await fetch(`${this.baseUrl}${API_CONFIG.endpoints.auth.login}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: credentials.username,
        password: credentials.password
      }),
      credentials: 'include',
    });

    const data = await response.json();

    if (!response.ok) {
      const errorData = data as ApiErrorResponse;
      throw new Error(typeof errorData.detail === 'string' ? errorData.detail : 'Credenciales incorrectas');
    }

    return data as LoginResponse;
  }

  async loginWithGoogle(code: string): Promise<LoginResponse> {
    if (!code) {
      throw new Error("No se recibió el código de autorización de Google");
    }

    const response = await fetch(`${this.baseUrl}${API_CONFIG.endpoints.auth.google}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        token: code,
        origin: "google" 
      }),
      credentials: 'include',
    });

    const data = await response.json();

    if (!response.ok) {
      console.error("Error Backend Google Auth:", data);
      
      let errorMsg = 'Error en Google Auth';
      if (typeof data.detail === 'string') {
        errorMsg = data.detail;
      } else if (Array.isArray(data.detail)) {
        errorMsg = data.detail[0]?.msg || JSON.stringify(data.detail);
      }

      throw new Error(errorMsg);
    }

    return data as LoginResponse;
  }

  async forgotPassword(email: string): Promise<{ message: string }> {
    const response = await fetch(`${this.baseUrl}${API_CONFIG.endpoints.auth.forgotPassword}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'Error al procesar');
    }

    return data;
  }

  async resetPassword(token: string, newPassword: string): Promise<{ message: string }> {
    const response = await fetch(`${this.baseUrl}${API_CONFIG.endpoints.auth.resetPassword}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, newPassword }),
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'Error al restablecer');
    }

    return data;
  }

  async getCurrentUser(): Promise<User | null> {
    try {
      const response = await fetch(`${this.baseUrl}${API_CONFIG.endpoints.users.me}`, {
        method: 'GET',
        credentials: 'include',
      });

      if (!response.ok) {
        return null;
      }

      const data = await response.json();
      return data as User;
    } catch (error) {
      console.error('Error fetching current user:', error);
      return null;
    }
  }
}

// Singleton instance
export const authService = new AuthService();
