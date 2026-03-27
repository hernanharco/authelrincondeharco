'use client';

import { useState, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService, type IAuthService } from '@/services/authService';
import { APP_CONFIG, AUTH_MESSAGES } from '@/utils/constants';
import type { LoginRequest, User, AuthState, AuthError } from '@/types/auth';

// Hook principal de autenticación (SRP)
export const useAuth = (authServiceInstance: IAuthService = authService) => {
  const router = useRouter();
  const [state, setState] = useState<AuthState>({
    isLoading: false,
    error: null,
    success: null,
    user: null,
  });

  // Helpers de estado
  const setLoading = useCallback((loading: boolean) => {
    setState(prev => ({ ...prev, isLoading: loading }));
  }, []);

  const setError = useCallback((error: AuthError | null) => {
    setState(prev => ({ ...prev, error, success: null }));
  }, []);

  const setSuccess = useCallback((message: string | null) => {
    setState(prev => ({ ...prev, success: message, error: null }));
  }, []);

  const setUser = useCallback((user: User | null) => {
    setState(prev => ({ ...prev, user }));
    if (user) {
      localStorage.setItem('auth_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('auth_user');
    }
  }, []);

  // Persistencia de sesión
  useEffect(() => {
    const savedUser = localStorage.getItem('auth_user');
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        localStorage.removeItem('auth_user');
      }
    }
  }, [setUser]);

  // Acciones delegadas al servicio (DIP)
  const login = useCallback(async (credentials: LoginRequest): Promise<boolean> => {
    setLoading(true);
    setError(null);

    const result = await authServiceInstance.login(credentials);
    
    if (result.success && result.user) {
      setUser(result.user);
      setSuccess(AUTH_MESSAGES.LOGIN_SUCCESS);
      return true;
    } else {
      setError({ message: result.error || AUTH_MESSAGES.LOGIN_ERROR });
      return false;
    }
  }, [authServiceInstance, setLoading, setError, setSuccess, setUser]);

  const loginWithGoogle = useCallback(async (token: string): Promise<boolean> => {
    setLoading(true);
    setError(null);

    const result = await authServiceInstance.loginWithGoogle(token);
    
    if (result.success && result.user) {
      setUser(result.user);
      setSuccess(AUTH_MESSAGES.GOOGLE_SUCCESS);
      return true;
    } else {
      setError({ message: result.error || AUTH_MESSAGES.GOOGLE_ERROR });
      return false;
    }
  }, [authServiceInstance, setLoading, setError, setSuccess, setUser]);

  const logout = useCallback(async () => {
    setUser(null);
    await authServiceInstance.logout();
    if (typeof window !== 'undefined') {
      router.push('/login');
    }
  }, [authServiceInstance, setUser, router]);

  const forgotPassword = useCallback(async (email: string): Promise<boolean> => {
    setLoading(true);
    setError(null);

    const result = await authServiceInstance.forgotPassword(email);
    
    if (result.success) {
      setSuccess(result.message || AUTH_MESSAGES.FORGOT_PASSWORD_SENT);
      return true;
    } else {
      setError({ message: result.error || 'Error al procesar solicitud' });
      return false;
    }
  }, [authServiceInstance, setLoading, setError, setSuccess]);

  const resetPassword = useCallback(async (token: string, newPassword: string): Promise<boolean> => {
    setLoading(true);
    setError(null);

    const result = await authServiceInstance.resetPassword(token, newPassword);
    
    if (result.success) {
      setSuccess(result.message || AUTH_MESSAGES.PASSWORD_RESET_SUCCESS);
      return true;
    } else {
      setError({ message: result.error || 'Error al restablecer contraseña' });
      return false;
    }
  }, [authServiceInstance, setLoading, setError, setSuccess]);

  const clearMessages = useCallback(() => {
    setState(prev => ({ ...prev, error: null, success: null }));
  }, []);

  return {
    ...state,
    login,
    loginWithGoogle,
    logout,
    forgotPassword,
    resetPassword,
    clearMessages,
  };
};
