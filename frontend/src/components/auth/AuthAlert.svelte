<script lang="ts">
  // /src/components/auth/AuthAlert.svelte
  interface Props {
    status?: string | null;
    error?: string | null;
  }

  let { status = null, error = null }: Props = $props();
  let visible = $state(true);

  // Mapeo de mensajes según el error recibido
  const alertInfo = $derived.by(() => {
    if (error === "insufficient_permissions" || status === "pending") {
      return {
        title: "Permisos Insuficientes",
        text: "Tu cuenta no tiene los permisos adecuados para ingresar al sistema. Por favor, contacta con el administrador.",
        type: "warning"
      };
    }
    if (error === "auth_failed") {
      return {
        title: "Error de Acceso",
        text: "Hubo un problema al autenticar con Google. Inténtalo de nuevo.",
        type: "error"
      };
    }
    return null;
  });
</script>

{#if alertInfo && visible}
  <div class="mb-6 flex items-start gap-3 rounded-xl border p-4 shadow-lg animate-in fade-in slide-in-from-top-2 
    {alertInfo.type === 'warning' ? 'border-amber-500/30 bg-amber-500/10 text-amber-200' : 'border-red-500/30 bg-red-500/10 text-red-200'}">
    
    <div class="mt-0.5 shrink-0 {alertInfo.type === 'warning' ? 'text-amber-500' : 'text-red-500'}">
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
    </div>

    <div class="flex-1 text-sm">
      <span class="font-bold block text-base leading-tight mb-1">{alertInfo.title}</span>
      <p class="opacity-90 leading-relaxed">{alertInfo.text}</p>
    </div>

    <button onclick={() => visible = false} class="opacity-50 hover:opacity-100 transition-opacity p-1" aria-label="Cerrar alerta">
      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
    </button>
  </div>
{/if}