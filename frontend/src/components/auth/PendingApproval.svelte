<script lang="ts">
  let { email = "" } = $props();
</script>

<div class="flex flex-col items-center text-center px-6 py-10 space-y-6">
  <div class="relative">
    <div class="w-24 h-24 rounded-full bg-yellow-500/10 border-2 border-yellow-500/30 flex items-center justify-center animate-pulse">
      <svg class="w-12 h-12 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    </div>
    <div class="absolute -top-1 -right-1 w-6 h-6 bg-yellow-400 rounded-full flex items-center justify-center">
      <span class="text-xs font-bold text-yellow-900">!</span>
    </div>
  </div>

  <div class="space-y-2">
    <h2 class="text-2xl font-bold text-white">Solicitud Recibida</h2>
    <p class="text-yellow-400 font-medium">Tu cuenta esta pendiente de aprobacion</p>
  </div>

  <div class="bg-yellow-500/5 border border-yellow-500/20 rounded-xl p-5 text-left space-y-3 w-full max-w-sm">
    <p class="text-sm text-gray-300 leading-relaxed">
      Hemos registrado tu cuenta con Google exitosamente.
      Un administrador revisara tu solicitud y te dara acceso al sistema.
    </p>
    {#if email}
      <div class="flex items-center gap-2 pt-1">
        <svg class="w-4 h-4 text-yellow-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
        <span class="text-xs text-gray-400">
          Recibiras una notificacion en
          <span class="text-white font-medium">{email}</span>
        </span>
      </div>
    {/if}
  </div>

  <div class="w-full max-w-sm space-y-3">
    <p class="text-xs text-gray-500 uppercase tracking-wider font-medium">Que sigue?</p>
    {#each [
      { step: "1", text: "Tu solicitud fue enviada al administrador" },
      { step: "2", text: "El administrador revisara tu perfil" },
      { step: "3", text: "Recibiras acceso una vez aprobado" },
    ] as item}
      <div class="flex items-center gap-3 text-left">
        <div class="w-6 h-6 rounded-full bg-[#2D3148] border border-[#3D4168] flex items-center justify-center shrink-0">
          <span class="text-xs text-gray-400 font-medium">{item.step}</span>
        </div>
        <span class="text-sm text-gray-400">{item.text}</span>
      </div>
    {/each}
  </div>

  <a href="/login" class="text-sm text-gray-500 hover:text-gray-300 transition-colors flex items-center gap-1">
    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
    </svg>
    Volver al inicio
  </a>
</div>