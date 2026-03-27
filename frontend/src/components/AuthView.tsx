'use client';

import { useState } from 'react';
import { useGoogleLogin } from '@react-oauth/google';
import { useAuth } from '@/hooks/useAuth';
import { useRouter, useSearchParams } from 'next/navigation';
import LoginForm from '@/components/forms/LoginForm';
import GoogleButton from '@/components/ui/GoogleButton';
import Alert from '@/components/ui/Alert';

export const AuthView = () => {
  const auth = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [view, setView] = useState<'login' | 'forgot' | 'reset'>('login');

  // --- LÓGICA DE REDIRECCIÓN ---
  const handleRedirect = () => {
    const redirectTo = searchParams.get('redirect');
    if (redirectTo && redirectTo !== 'null') {
      window.location.href = redirectTo;
    } else {
      router.push('/dashboard');
    }
  };

  // --- CONFIGURACIÓN DE GOOGLE ---
  const handleGoogleSuccess = async (token: string) => {
    const result = await auth.loginWithGoogle(token);
    if (result) {
      handleRedirect();
    }
  };

  const handleGoogleError = (error: any) => {
    console.error('Error en Google OAuth:', error);
  };

  // --- RENDER PRINCIPAL ---
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            {view === 'login' && 'Iniciar Sesión'}
            {view === 'forgot' && 'Recuperar Contraseña'}
            {view === 'reset' && 'Restablecer Contraseña'}
          </h2>
        </div>

        {/* Alertas */}
        {auth.error && (
          <Alert variant="error" dismissible onDismiss={auth.clearMessages}>
            {auth.error.message}
          </Alert>
        )}

        {auth.success && (
          <Alert variant="success" dismissible onDismiss={auth.clearMessages}>
            {auth.success}
          </Alert>
        )}

        <div className="bg-white shadow-lg rounded-lg p-8">
          {view === 'login' && (
            <>
              <LoginForm onSuccess={handleRedirect} />

              {/* Separador */}
              <div className="mt-6">
                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-300" />
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="px-2 bg-white text-gray-500">O continuar con</span>
                  </div>
                </div>

                {/* Botón Google */}
                <div className="mt-4">
                  <GoogleButton
                    onSuccess={handleGoogleSuccess}
                    onError={handleGoogleError}
                    disabled={auth.isLoading}
                  />
                </div>
              </div>
            </>
          )}

          {/* Aquí irían los otros formularios */}
          {view === 'forgot' && <div>Formulario de recuperación</div>}
          {view === 'reset' && <div>Formulario de reset</div>}

          <div className="mt-6 text-center">
            {view === 'login' && (
              <button onClick={() => setView('forgot')} className="text-sm text-blue-600 hover:text-blue-500">
                ¿Olvidaste tu contraseña?
              </button>
            )}
            {(view === 'forgot' || view === 'reset') && (
              <button onClick={() => setView('login')} className="text-sm text-blue-600 hover:text-blue-500">
                Volver al inicio de sesión
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};