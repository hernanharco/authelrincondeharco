<script lang="ts">
  interface Props {
    role: string;
    editable?: boolean;
    onRoleChange?: (newRole: string) => void;
    class?: string;
  }

  let { role, editable = false, onRoleChange, class: className = '' }: Props = $props();

  let isOpen = $state(false);
  let selectedRole = $state(role);

  const roles = ['SUPERADMIN', 'ADMIN', 'MANAGER', 'USER', 'VIEWER', 'NONE'];

  const roleColors = {
    SUPERADMIN: 'bg-[#DC2626] text-white',
    ADMIN: 'bg-[#7C3AED] text-white',
    MANAGER: 'bg-[#2563EB] text-white',
    USER: 'bg-[#10B981] text-white',
    VIEWER: 'bg-[#6B7280] text-white',
    NONE: 'bg-[#374151] text-white',
  };

  function handleRoleChange(newRole: string) {
    role = newRole;
    isOpen = false;
    if (onRoleChange) {
      onRoleChange(newRole);
    }
  }

  function getRoleLabel(role: string): string {
    const labels = {
      SUPERADMIN: 'Superadmin',
      ADMIN: 'Admin',
      MANAGER: 'Manager',
      USER: 'Usuario',
      VIEWER: 'Lector',
      NONE: 'Sin rol',
    };
    return labels[role as keyof typeof labels] || role;
  }
</script>

<div class="relative">
  {#if editable}
    <button
      class={`px-2 py-1 rounded-full text-xs font-medium transition-colors ${roleColors[role as keyof typeof roleColors]} ${className} hover:opacity-80 cursor-pointer`}
      onclick={() => (isOpen = !isOpen)}
    >
      {getRoleLabel(role)}
      <svg class="w-3 h-3 ml-1 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    {#if isOpen}
      <div
        class="absolute z-10 mt-1 bg-[#1E2130] border border-[#2D3148] rounded-lg shadow-lg min-w-[120px]"
      >
        {#each roles as r}
          <button
            class="block w-full text-left px-3 py-2 text-sm hover:bg-[#2D3148] transition-colors"
            onclick={() => handleRoleChange(r)}
          >
            {getRoleLabel(r)}
          </button>
        {/each}
      </div>
    {/if}
  {:else}
    <span
      class={`px-2 py-1 rounded-full text-xs font-medium ${roleColors[role as keyof typeof roleColors]} ${className}`}
    >
      {getRoleLabel(role)}
    </span>
  {/if}
</div>
