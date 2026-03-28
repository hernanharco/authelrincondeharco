<script lang="ts">
  import { authService, type LoginRequest, type AuthState, type AuthError } from '../../services/authService';

  // Estado reactivo con Svelte 5 Runes
  let form = $state<LoginRequest>({
    username: '',
    password: ''
  });

  let authState = $state<AuthState>({
    isLoading: false,
    error: null,
    success: null,
    user: null
  });

  // Manejador de submit con sintaxis moderna
  async function handleSubmit(event: SubmitEvent) {
    event.preventDefault();
    
    authState.isLoading = true;
    authState.error = null;
    authState.success = null;

    try {
      const response = await authService.login(form);
      authState.user = response.user;
      authState.success = 'Inicio de sesión exitoso';
      
      // Guardar usuario en localStorage para persistencia
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth_user', JSON.stringify(response.user));
      }
      
      // Redireccionar al dashboard usando window.location
      if (typeof window !== 'undefined') {
        window.location.href = '/dashboard';
      }
    } catch (error) {
      authState.error = {
        message: error instanceof Error ? error.message : 'Error desconocido'
      };
    } finally {
      authState.isLoading = false;
    }
  }

  // Limpiar mensajes
  function clearMessages() {
    authState.error = null;
    authState.success = null;
  }

  // Recuperar usuario guardado al montar el componente
  $effect(() => {
    if (typeof window !== 'undefined') {
      const savedUser = localStorage.getItem('auth_user');
      if (savedUser) {
        try {
          authState.user = JSON.parse(savedUser);
        } catch (e) {
          localStorage.removeItem('auth_user');
        }
      }
    }
  });
</script>

<div class="w-full max-w-md mx-auto">
  <form onsubmit={handleSubmit} class="space-y-6">
    <div>
      <label for="username" class="block text-sm font-medium text-gray-700">
        Usuario
      </label>
      <input
        id="username"
        type="text"
        bind:value={form.username}
        oninput={clearMessages}
        class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        placeholder="Ingresa tu usuario"
        required
        disabled={authState.isLoading}
      />
    </div>

    <div>
      <label for="password" class="block text-sm font-medium text-gray-700">
        Contraseña
      </label>
      <input
        id="password"
        type="password"
        bind:value={form.password}
        oninput={clearMessages}
        class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        placeholder="Ingresa tu contraseña"
        required
        disabled={authState.isLoading}
      />
    </div>

    <!-- Mensajes de error -->
    {#if authState.error}
      <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {authState.error.message}
      </div>
    {/if}

    <!-- Mensajes de éxito -->
    {#if authState.success}
      <div class="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
        {authState.success}
      </div>
    {/if}

    <!-- Botón de submit -->
    <button
      type="submit"
      disabled={authState.isLoading || !form.username || !form.password}
      class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {#if authState.isLoading}
        <span class="inline-block animate-spin mr-2">⏳</span>
        Iniciando sesión...
      {:else}
        Iniciar Sesión
      {/if}
    </button>
  </form>
</div>
