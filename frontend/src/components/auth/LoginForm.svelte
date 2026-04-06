<script lang="ts">
  import { authService, type LoginRequest, type AuthState } from '../../services/authService';

  /**
   * 1. DEFINICIÓN DE PROPS (Para evitar error de diagnóstico en Astro)
   */
  interface Props {
    redirectParam?: string;
  }

  // Recibimos la prop con un valor por defecto
  let { redirectParam = 'dashboard' }: Props = $props();

  /**
   * 2. ESTADO REACTIVO (Svelte 5 Runes)
   */
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

  /**
   * 3. LÓGICA DE REDIRECCIÓN DINÁMICA
   */
  function handleNavigation() {
    const currentOrigin = window.location.origin;
    
    // Si redirectParam es una URL completa, la usamos. Si no, construimos la ruta local.
    const destination = redirectParam.startsWith('http') 
      ? redirectParam 
      : `${currentOrigin}/${redirectParam.replace(/^\//, '')}`;

    window.location.href = destination;
  }

  /**
   * 4. MANEJADOR DE ENVÍO
   */
  async function handleSubmit(event: SubmitEvent) {
    event.preventDefault();
    
    authState.isLoading = true;
    authState.error = null;
    authState.success = null;

    try {
      const response = await authService.login(form);
      authState.user = response.user;
      authState.success = '¡Sesión iniciada con éxito!';
      
      // Guardamos en localStorage por si acaso (aunque la cookie mande)
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth_user', JSON.stringify(response.user));
      }
      
      // Ejecutamos la redirección inteligente
      handleNavigation();
      
    } catch (error) {
      // CAMBIO: Asignar el string directamente en lugar del objeto
      authState.error = error instanceof Error ? error.message : 'Credenciales inválidas';
    } finally {
      authState.isLoading = false;
    }
  }

  function clearMessages() {
    if (authState.error || authState.success) {
      authState.error = null;
      authState.success = null;
    }
  }
</script>

<div class="w-full max-w-md mx-auto">
  <!-- Svelte 5: usamos onsubmit directo -->
  <form onsubmit={handleSubmit} class="space-y-5">
    <div>
      <label for="username" class="block text-sm font-medium text-[#9CA3AF] mb-1.5">
        Nombre de usuario
      </label>
      <input
        id="username"
        type="text"
        bind:value={form.username}
        oninput={clearMessages}
        class="w-full px-4 py-3 bg-[#111827] border border-[#2D3148] rounded-xl text-white focus:ring-2 focus:ring-[#6366F1] focus:border-transparent outline-none transition-all placeholder:text-[#4B5563]"
        placeholder="Tu usuario..."
        required
        disabled={authState.isLoading}
      />
    </div>

    <div>
      <label for="password" class="block text-sm font-medium text-[#9CA3AF] mb-1.5">
        Contraseña
      </label>
      <input
        id="password"
        type="password"
        bind:value={form.password}
        oninput={clearMessages}
        class="w-full px-4 py-3 bg-[#111827] border border-[#2D3148] rounded-xl text-white focus:ring-2 focus:ring-[#6366F1] focus:border-transparent outline-none transition-all placeholder:text-[#4B5563]"
        placeholder="••••••••"
        required
        disabled={authState.isLoading}
      />
    </div>

    <!-- Feedback Visual -->
    {#if authState.error}
      <div class="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm text-center animate-in fade-in zoom-in duration-200">
        {authState.error}
      </div>
    {/if}

    {#if authState.success}
      <div class="p-3 rounded-lg bg-green-500/10 border border-green-500/20 text-green-400 text-sm text-center animate-in fade-in zoom-in duration-200">
        {authState.success}
      </div>
    {/if}

    <button
      type="submit"
      disabled={authState.isLoading || !form.username || !form.password}
      class="w-full py-3 px-4 bg-[#6366F1] hover:bg-[#4F46E5] text-white rounded-xl font-semibold shadow-lg shadow-indigo-500/20 transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center gap-2"
    >
      {#if authState.isLoading}
        <svg class="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        Validando...
      {:else}
        Entrar al sistema
      {/if}
    </button>
  </form>
</div>