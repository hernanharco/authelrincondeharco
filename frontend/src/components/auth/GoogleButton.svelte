<script lang="ts">
  let isLoading = $state(false);
  let error = $state<string | null>(null);

  async function handleGoogleLogin() {
    if (isLoading) return;
    isLoading = true;
    error = null;

    try {
      const popup = window.open(
        'http://localhost:8001/api/v1/auth/google',
        'google-auth',
        'width=500,height=600,scrollbars=yes,resizable=yes',
      );

      if (!popup) {
        throw new Error('No se pudo abrir la ventana emergente. Verifica que tu navegador permita popups.');
      }

      const handleMessage = (event: MessageEvent) => {
        if (event.origin !== 'http://localhost:8001') return;

        const data = event.data;

        if (data.type === 'AUTH_SUCCESS') {
          // Guardar SOLO como cookie para que el middleware la lea
          document.cookie = `session=${data.payload.token}; path=/; max-age=86400; SameSite=Lax`;

          popup.close();
          window.location.href = '/dashboard';
        } else if (data.type === 'AUTH_ERROR') {
          error = data.error || 'Error en la autenticación con Google';
          popup.close();
        }
      };

      window.addEventListener('message', handleMessage);

      const checkClosed = setInterval(() => {
        if (popup.closed) {
          clearInterval(checkClosed);
          window.removeEventListener('message', handleMessage);
          isLoading = false;
        }
      }, 1000);
    } catch (err) {
      error = err instanceof Error ? err.message : 'Error al iniciar autenticación con Google';
      isLoading = false;
    }
  }

  function clearMessages() {
    error = null;
  }
</script>

<div class="w-full max-w-md mx-auto">
  <div class="relative my-6">
    <div class="absolute inset-0 flex items-center">
      <div class="w-full border-t border-gray-300"></div>
    </div>
    <div class="relative flex justify-center text-sm">
      <span class="px-2 bg-white text-gray-500">O continúa con</span>
    </div>
  </div>

  {#if error}
    <div class="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
      {error}
    </div>
  {/if}

  <button
    type="button"
    onclick={handleGoogleLogin}
    onfocus={clearMessages}
    disabled={isLoading}
    class="w-full flex justify-center items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
  >
    {#if isLoading}
      <span class="inline-block animate-spin mr-2">⏳</span>
      Conectando con Google...
    {:else}
      <svg class="w-5 h-5 mr-2" viewBox="0 0 24 24">
        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
      </svg>
      Continuar con Google
    {/if}
  </button>
</div>
