<script lang="ts">
  import { getSortedCountryCodes, searchCountryCodes, type CountryCode } from '../../data/countryCodes';

  interface Props {
    value: string;          // Valor completo del teléfono (ej: "+34 612 345 678")
    onChange?: (val: string) => void;
    disabled?: boolean;
    required?: boolean;
  }

  let { value = '', onChange, disabled = false, required = false }: Props = $props();

  const allCountries = getSortedCountryCodes();

  // ── Funciones helper ──

  function detectCountryFromPhone(phone: string): CountryCode {
    if (!phone) return allCountries[0];
    for (const c of allCountries) {
      if (phone.startsWith(c.dial)) return c;
    }
    return allCountries[0];
  }

  function extractLocalNumber(phone: string): string {
    if (!phone) return '';
    const country = detectCountryFromPhone(phone);
    return phone.replace(country.dial, '').trim();
  }

  // ── Estado reactivo ──

  let isOpen = $state(false);
  let searchQuery = $state('');
  let selectedCountry = $state(detectCountryFromPhone(value));
  let localNumber = $state(extractLocalNumber(value));

  // Sincroniza estado interno cuando cambia el value desde afuera
  $effect(() => {
    selectedCountry = detectCountryFromPhone(value);
    localNumber = extractLocalNumber(value);
  });

  let filteredCountries = $derived(
    searchQuery ? searchCountryCodes(searchQuery) : allCountries
  );

  // ── Refs al DOM ──

  let dropdownRef: HTMLDivElement | undefined = $state();
  let searchInputRef: HTMLInputElement | undefined = $state();

  // ── Handlers ──

  function selectCountry(country: CountryCode) {
    selectedCountry = country;
    isOpen = false;
    searchQuery = '';
    emitChange();
  }

  function handleLocalNumberChange(e: Event) {
    const target = e.target as HTMLInputElement;
    localNumber = target.value;
    emitChange();
  }

  function emitChange() {
    const full = `${selectedCountry.dial} ${localNumber}`.trim();
    onChange?.(full);
  }

  function handleClickOutside(e: MouseEvent) {
    if (dropdownRef && !dropdownRef.contains(e.target as Node)) {
      isOpen = false;
      searchQuery = '';
    }
  }

  // ── Efectos ──

  let clickHandlerAttached = $state(false);

  $effect(() => {
    if (isOpen && !clickHandlerAttached) {
      clickHandlerAttached = true;
      document.addEventListener('click', handleClickOutside);
      setTimeout(() => searchInputRef?.focus(), 50);
    }
    if (!isOpen && clickHandlerAttached) {
      clickHandlerAttached = false;
      document.removeEventListener('click', handleClickOutside);
    }
  });
</script>

<div class="flex gap-0">
  <!-- Selector de país -->
  <div class="relative" bind:this={dropdownRef}>
    <button
      type="button"
      onclick={() => (isOpen = !isOpen)}
      disabled={disabled}
      class="flex items-center gap-1.5 px-3 py-3 bg-[#111827] border border-[#2D3148] rounded-l-xl text-white hover:bg-[#1E2130] transition-colors disabled:opacity-50 disabled:cursor-not-allowed min-w-[80px]"
    >
      <span class="text-lg leading-none">{selectedCountry.flag}</span>
      <span class="text-sm font-medium">{selectedCountry.dial}</span>
      <svg
        class="w-3 h-3 text-[#9CA3AF] transition-transform {isOpen ? 'rotate-180' : ''}"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <!-- Dropdown con buscador -->
    {#if isOpen}
      <div class="absolute top-full left-0 mt-1 z-50 w-72 bg-[#1E2130] border border-[#2D3148] rounded-xl shadow-2xl overflow-hidden">
        <!-- Buscador -->
        <div class="p-2 border-b border-[#2D3148]">
          <input
            bind:this={searchInputRef}
            type="text"
            bind:value={searchQuery}
            placeholder="Buscar país o código..."
            class="w-full px-3 py-2 bg-[#111827] border border-[#2D3148] rounded-lg text-white text-sm placeholder:text-[#6B7280] focus:outline-none focus:ring-2 focus:ring-[#6366F1]"
          />
        </div>

        <!-- Lista de países -->
        <div class="max-h-60 overflow-y-auto">
          {#each filteredCountries as country (country.code)}
            <button
              type="button"
              onclick={() => selectCountry(country)}
              class="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-left hover:bg-[#2D3148] transition-colors {selectedCountry.code === country.code ? 'bg-[#6366F1]/10 text-[#6366F1]' : 'text-[#F9FAFB]'}"
            >
              <span class="text-lg">{country.flag}</span>
              <span class="font-medium">{country.name}</span>
              <span class="ml-auto text-[#9CA3AF]">{country.dial}</span>
            </button>
          {/each}
          {#if filteredCountries.length === 0}
            <div class="px-4 py-8 text-center text-sm text-[#6B7280]">
              No se encontraron países para "{searchQuery}"
            </div>
          {/if}
        </div>
      </div>
    {/if}
  </div>

  <!-- Input del número -->
  <input
    type="tel"
    value={localNumber}
    oninput={handleLocalNumberChange}
    placeholder="612 345 678"
    required={required}
    disabled={disabled}
    class="flex-1 px-4 py-3 bg-[#111827] border border-l-0 border-[#2D3148] rounded-r-xl text-white focus:ring-2 focus:ring-[#6366F1] focus:border-transparent outline-none transition-all placeholder:text-[#4B5563] disabled:opacity-50 disabled:cursor-not-allowed"
  />
</div>
