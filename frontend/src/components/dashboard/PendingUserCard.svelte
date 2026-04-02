<script>
  // Svelte 5: Recibimos las props y el callback para actualizar la lista
  let { user, onActionSuccess } = $props();
  let loading = $state(false);

  async function handleApprove() {
    if (loading) return;
    loading = true;
    
    try {
      // Importamos la configuración centralizada
      const { BACKEND_URL } = await import('../../config/api.config');
      const response = await fetch(`${BACKEND_URL}/api/v1/users/${user.id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'ACTIVE' }) // Cambiamos a ACTIVE
      });

      if (response.ok) {
        // Notificamos al padre para que elimine al usuario de la lista local
        onActionSuccess(user.id);
      } else {
        alert("Error al aprobar usuario");
      }
    } catch (e) {
      console.error("Error:", e);
    } finally {
      loading = false;
    }
  }
</script>

<div class="bg-[#1E2130] p-6 rounded-xl border border-gray-800 flex items-center justify-between mb-4">
  <div class="flex items-center gap-4">
    <div class="w-12 h-12 bg-indigo-600 rounded-full flex items-center justify-center text-xl font-bold">
      {user.full_name ? user.full_name[0].toUpperCase() : 'U'}
    </div>
    <div>
      <h3 class="font-semibold text-white">{user.full_name}</h3>
      <p class="text-gray-400 text-sm">@{user.username} • {user.email}</p>
      <div class="flex gap-2 mt-1">
        <span class="px-2 py-0.5 bg-blue-900/30 text-blue-400 text-[10px] rounded uppercase font-bold tracking-wider">
          {user.origin || 'unknown'}
        </span>
      </div>
    </div>
  </div>

  <div class="flex gap-3">
    <button 
      onclick={handleApprove}
      disabled={loading}
      class="px-4 py-2 bg-[#10B981] hover:bg-emerald-600 text-white rounded-lg text-sm font-bold transition-colors disabled:opacity-50"
    >
      {loading ? 'Procesando...' : 'Aprobar'}
    </button>
    
    <button class="px-4 py-2 bg-[#EF4444] hover:bg-red-600 text-white rounded-lg text-sm font-bold transition-colors">
      Rechazar
    </button>
  </div>
</div>
