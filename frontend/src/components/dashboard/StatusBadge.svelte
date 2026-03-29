<script lang="ts">
  interface Props {
    status: string;
    editable?: boolean;
    onStatusChange?: (newStatus: string) => void;
    class?: string;
  }

  let { status, editable = false, onStatusChange, class: className = '' }: Props = $props();

  let isOpen = $state(false);
  let selectedStatus = $state(status);

  const statuses = ['ACTIVE', 'INACTIVE', 'SUSPENDED', 'PENDING'];

  const statusColors = {
    ACTIVE: 'bg-[#10B981] text-white',
    INACTIVE: 'bg-[#6B7280] text-white',
    SUSPENDED: 'bg-[#EF4444] text-white',
    PENDING: 'bg-[#F59E0B] text-white',
  };

  function handleStatusChange(newStatus: string) {
    status = newStatus;
    isOpen = false;
    if (onStatusChange) {
      onStatusChange(newStatus);
    }
  }

  function getStatusLabel(status: string): string {
    const labels = {
      ACTIVE: 'Activo',
      INACTIVE: 'Inactivo',
      SUSPENDED: 'Suspendido',
      PENDING: 'Pendiente',
    };
    return labels[status as keyof typeof labels] || status;
  }
</script>

<div class="relative">
  {#if editable}
    <button
      class={`px-2 py-1 rounded-full text-xs font-medium transition-colors ${statusColors[status as keyof typeof statusColors]} ${className} hover:opacity-80 cursor-pointer`}
      onclick={() => (isOpen = !isOpen)}
    >
      {getStatusLabel(status)}
      <svg class="w-3 h-3 ml-1 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    {#if isOpen}
      <div
        class="absolute z-10 mt-1 bg-[#1E2130] border border-[#2D3148] rounded-lg shadow-lg min-w-[120px]"
      >
        {#each statuses as s}
          <button
            class="block w-full text-left px-3 py-2 text-sm hover:bg-[#2D3148] transition-colors"
            onclick={() => handleStatusChange(s)}
          >
            {getStatusLabel(s)}
          </button>
        {/each}
      </div>
    {/if}
  {:else}
    <span
      class={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[status as keyof typeof statusColors]} ${className}`}
    >
      {getStatusLabel(status)}
    </span>
  {/if}
</div>
