<script lang="ts">
  import { onMount } from 'svelte';
  import { apiUrl, ENDPOINTS } from '../../config/api.config';
  import PhoneInput from './PhoneInput.svelte';

  interface Props {
    token: string;
    userId?: number; // si no se pasa, se usa /me
  }

  let { token, userId }: Props = $props();

  let loading = $state(false);
  let saving = $state(false);
  let error = $state<string | null>(null);
  let success = $state<string | null>(null);

  let form = $state({
    company_name: '',
    cif: '',
    address: '',
    iban: '',
    phone: '',
    contact_name: '',
  });

  let profileExists = $state(false);

  async function loadProfile() {
    loading = true;
    error = null;
    try {
      const endpoint = userId
        ? ENDPOINTS.company.byId(userId)
        : ENDPOINTS.company.me;

      const res = await fetch(apiUrl(endpoint), {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.ok) {
        const data = await res.json();
        form = {
          company_name: data.company_name || '',
          cif: data.cif || '',
          address: data.address || '',
          iban: data.iban || '',
          phone: data.phone || '',
          contact_name: data.contact_name || '',
        };
        profileExists = true;
      } else if (res.status === 404) {
        profileExists = false;
      } else {
        const data = await res.json();
        error = data.detail || 'Error al cargar el perfil';
      }
    } catch (e) {
      error = 'Error de conexión al cargar el perfil';
    } finally {
      loading = false;
    }
  }

  async function handleSubmit(event: SubmitEvent) {
    event.preventDefault();
    saving = true;
    error = null;
    success = null;

    try {
      // Si no hay userId, se usa PUT /me (crea o actualiza, idempotente)
      const targetUrl = userId
        ? apiUrl(profileExists ? ENDPOINTS.company.update(userId) : ENDPOINTS.company.create(userId))
        : apiUrl(ENDPOINTS.company.me);
      const method = userId ? (profileExists ? 'PUT' : 'POST') : 'PUT';

      const res = await fetch(targetUrl, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(form),
      });

      if (res.ok) {
        profileExists = true;
        success = 'Perfil de empresa guardado correctamente';
        setTimeout(() => (success = null), 3000);
      } else {
        const data = await res.json();
        error = data.detail || 'Error al guardar el perfil';
      }
    } catch (e) {
      console.error('Error al guardar perfil empresa:', e);
      error = e instanceof TypeError
        ? 'Error de conexión con el servidor — ¿está el backend corriendo?'
        : `Error inesperado: ${e}`;
    } finally {
      saving = false;
    }
  }

  onMount(() => {
    loadProfile();
  });
</script>

<div class="bg-[#1E2130] border border-[#2D3148] rounded-lg p-6">
  <div class="flex items-center justify-between mb-6">
    <div>
      <h2 class="text-lg font-semibold text-[#F9FAFB]">
        {userId ? `Perfil de Empresa` : 'Mi Perfil de Empresa'}
      </h2>
      <p class="text-sm text-[#9CA3AF] mt-1">
        {profileExists
          ? 'Actualizá los datos de tu empresa'
          : 'Completá los datos de tu empresa'}
      </p>
    </div>
    {#if profileExists}
      <span class="px-3 py-1 bg-green-500/10 text-green-400 text-xs font-medium rounded-full border border-green-500/20">
        Perfil activo
      </span>
    {/if}
  </div>

  {#if loading}
    <div class="flex items-center justify-center py-12">
      <svg class="w-8 h-8 animate-spin text-indigo-400" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
      </svg>
      <span class="ml-3 text-[#9CA3AF]">Cargando perfil...</span>
    </div>
  {:else}
    <form onsubmit={handleSubmit} class="space-y-5">
      <!-- Nombre de la empresa -->
      <div>
        <label for="company_name" class="block text-sm font-medium text-[#9CA3AF] mb-1.5">
          Nombre de la empresa <span class="text-red-400">*</span>
        </label>
        <input
          id="company_name"
          type="text"
          bind:value={form.company_name}
          class="w-full px-4 py-3 bg-[#111827] border border-[#2D3148] rounded-xl text-white focus:ring-2 focus:ring-[#6366F1] focus:border-transparent outline-none transition-all placeholder:text-[#4B5563]"
          placeholder="Nombre legal de tu empresa"
          required
          disabled={saving}
        />
      </div>

      <!-- CIF + Móvil (2 columnas) -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label for="cif" class="block text-sm font-medium text-[#9CA3AF] mb-1.5">
            CIF / NIF
          </label>
          <input
            id="cif"
            type="text"
            bind:value={form.cif}
            class="w-full px-4 py-3 bg-[#111827] border border-[#2D3148] rounded-xl text-white focus:ring-2 focus:ring-[#6366F1] focus:border-transparent outline-none transition-all placeholder:text-[#4B5563]"
            placeholder="B12345678"
            maxlength={20}
            disabled={saving}
          />
        </div>
        <div>
          <label for="phone" class="block text-sm font-medium text-[#9CA3AF] mb-1.5">
            Móvil <span class="text-xs text-[#6B7280]">(con indicativo)</span>
          </label>
          <PhoneInput
            value={form.phone}
            onChange={(val) => (form.phone = val)}
            disabled={saving}
          />
        </div>
      </div>

      <!-- Dirección -->
      <div>
        <label for="address" class="block text-sm font-medium text-[#9CA3AF] mb-1.5">
          Dirección fiscal
        </label>
        <textarea
          id="address"
          bind:value={form.address}
          rows={2}
          class="w-full px-4 py-3 bg-[#111827] border border-[#2D3148] rounded-xl text-white focus:ring-2 focus:ring-[#6366F1] focus:border-transparent outline-none transition-all placeholder:text-[#4B5563] resize-none"
          placeholder="Calle, número, ciudad, CP..."
          disabled={saving}
        ></textarea>
      </div>

      <!-- IBAN + Contacto (2 columnas) -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label for="iban" class="block text-sm font-medium text-[#9CA3AF] mb-1.5">
            IBAN
          </label>
          <input
            id="iban"
            type="text"
            bind:value={form.iban}
            class="w-full px-4 py-3 bg-[#111827] border border-[#2D3148] rounded-xl text-white focus:ring-2 focus:ring-[#6366F1] focus:border-transparent outline-none transition-all placeholder:text-[#4B5563]"
            placeholder="ES00 0000 0000 0000 0000 0000"
            maxlength={34}
            disabled={saving}
          />
        </div>
        <div>
          <label for="contact_name" class="block text-sm font-medium text-[#9CA3AF] mb-1.5">
            Nombre del contacto
          </label>
          <input
            id="contact_name"
            type="text"
            bind:value={form.contact_name}
            class="w-full px-4 py-3 bg-[#111827] border border-[#2D3148] rounded-xl text-white focus:ring-2 focus:ring-[#6366F1] focus:border-transparent outline-none transition-all placeholder:text-[#4B5563]"
            placeholder="Nombre del dueño o responsable"
            maxlength={255}
            disabled={saving}
          />
        </div>
      </div>

      <!-- Feedback -->
      {#if error}
        <div class="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm text-center">
          {error}
        </div>
      {/if}

      {#if success}
        <div class="p-3 rounded-lg bg-green-500/10 border border-green-500/20 text-green-400 text-sm text-center">
          {success}
        </div>
      {/if}

      <!-- Botón -->
      <div class="pt-2">
        <button
          type="submit"
          disabled={saving || !form.company_name}
          class="w-full py-3 px-4 bg-[#6366F1] hover:bg-[#4F46E5] text-white rounded-xl font-semibold shadow-lg shadow-indigo-500/20 transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center gap-2"
        >
          {#if saving}
            <svg class="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Guardando...
          {:else}
            {profileExists ? 'Actualizar perfil' : 'Crear perfil'}
          {/if}
        </button>
      </div>
    </form>
  {/if}
</div>
