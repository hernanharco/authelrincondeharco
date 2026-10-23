<script lang="ts">
  /**
   * TenantMembers — card "Miembros" de la ficha de tenant (S3).
   *
   * Misma tabla que renderizaba la página Astro, más la asignación manual
   * usuario↔tenant: alta (POST) con selector de no-miembros y rol de
   * membresía, y baja (DELETE) por miembro. Tras cada mutación recarga la
   * lista desde el API. El token llega por prop (SSR): la cookie
   * access_token es httpOnly y este dominio no la lee.
   */
  import { formatDate } from '../../utils/date';
  import { displayMemberRole, memberRoleTooltip } from '../../utils/auth.roles';
  import { apiUrl, ENDPOINTS } from '../../config/api.config';
  import UserAvatar from './UserAvatar.svelte';
  import RoleBadge from './RoleBadge.svelte';
  import StatusBadge from './StatusBadge.svelte';

  interface TenantMember {
    id: number;
    username: string;
    email: string;
    role_tenant: string;
    role_global?: string | null;
    status: string;
    login_count: number;
    last_login: string | null;
  }

  interface PanelUser {
    id: number;
    username: string;
    email: string;
  }

  let { tenantId, token, members: initialMembers, allUsers } = $props<{
    tenantId: string;
    token: string;
    members: TenantMember[];
    allUsers: PanelUser[];
  }>();

  // Lista fresca tras cada mutación; hasta entonces se lee la prop SSR.
  // (Sembrar $state con la prop dispararía state_referenced_locally.)
  let refreshedMembers = $state<TenantMember[] | null>(null);
  const members = $derived(refreshedMembers ?? initialMembers);

  let selectedUserId = $state('');
  let selectedRole = $state('USER');
  let sending = $state(false);
  let error = $state<string | null>(null);

  // Usuarios que aún no son miembros: salen del selector de alta
  const assignable = $derived(
    allUsers.filter((u) => !members.some((m) => m.id === u.id)),
  );

  function enumKey(value: string): string {
    return value.trim().toUpperCase();
  }

  async function reloadMembers(): Promise<void> {
    const res = await fetch(apiUrl(ENDPOINTS.tenants.users(tenantId)), {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) refreshedMembers = await res.json();
  }

  async function addMember(): Promise<void> {
    if (!selectedUserId || sending) return;
    sending = true;
    error = null;
    try {
      const res = await fetch(apiUrl(ENDPOINTS.tenants.users(tenantId)), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ user_id: Number(selectedUserId), role: selectedRole }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        error = typeof body.detail === 'string' ? body.detail : 'No se pudo asignar';
        return;
      }
      selectedUserId = '';
      await reloadMembers();
    } catch {
      error = 'Error de conexión al asignar';
    } finally {
      sending = false;
    }
  }

  async function removeMember(member: TenantMember): Promise<void> {
    if (sending) return;
    sending = true;
    error = null;
    try {
      const res = await fetch(
        apiUrl(`${ENDPOINTS.tenants.users(tenantId)}/${member.id}`),
        { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } },
      );
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        error = typeof body.detail === 'string' ? body.detail : 'No se pudo quitar';
        return;
      }
      await reloadMembers();
    } catch {
      error = 'Error de conexión al quitar';
    } finally {
      sending = false;
    }
  }
</script>

<div class="bg-[#1E2130] border border-[#2D3148] rounded-lg p-6">
  <h3 class="text-lg font-semibold text-[#F9FAFB] mb-4">Miembros</h3>

  {#if error}
    <div
      class="mb-4 bg-[#EF4444]/10 border border-[#EF4444]/20 rounded-lg px-4 py-3 text-sm text-[#EF4444]"
      role="alert"
    >
      {error}
    </div>
  {/if}

  {#if members.length > 0}
    <div class="overflow-x-auto">
      <table class="w-full">
        <thead>
          <tr class="border-b border-[#2D3148]">
            <th class="text-left py-3 px-4 text-xs font-semibold uppercase tracking-wider text-[#6B7280]">Usuario</th>
            <th class="text-left py-3 px-4 text-xs font-semibold uppercase tracking-wider text-[#6B7280]">Rol</th>
            <th class="text-left py-3 px-4 text-xs font-semibold uppercase tracking-wider text-[#6B7280]">Estado</th>
            <th class="text-left py-3 px-4 text-xs font-semibold uppercase tracking-wider text-[#6B7280]">Logins</th>
            <th class="text-left py-3 px-4 text-xs font-semibold uppercase tracking-wider text-[#6B7280]">Último acceso</th>
            <th class="text-left py-3 px-4 text-xs font-semibold uppercase tracking-wider text-[#6B7280]">Acciones</th>
          </tr>
        </thead>
        <tbody>
          {#each members as member (member.id)}
            <tr class="border-b border-[#2D3148] hover:bg-[#2D3148]/40 transition-colors">
              <td class="py-3 px-4">
                <div class="flex items-center gap-3">
                  <UserAvatar name={member.username} size="sm" class="shrink-0" />
                  <div class="min-w-0">
                    <div class="truncate text-sm font-medium text-[#F9FAFB]">{member.username}</div>
                    <div class="truncate text-xs text-[#9CA3AF]">{member.email}</div>
                  </div>
                </div>
              </td>
              <td class="py-3 px-4">
                <RoleBadge
                  role={displayMemberRole(member.role_tenant, member.role_global)}
                  title={memberRoleTooltip(member.role_tenant, member.role_global)}
                />
              </td>
              <td class="py-3 px-4">
                <StatusBadge status={enumKey(member.status)} />
              </td>
              <td class="py-3 px-4 text-sm font-semibold tabular-nums text-[#F9FAFB]">{member.login_count}</td>
              <td class="py-3 px-4 text-sm text-[#9CA3AF] tabular-nums">
                {member.last_login ? formatDate(member.last_login) : '—'}
              </td>
              <td class="py-3 px-4">
                <button
                  type="button"
                  class="px-3 py-1.5 bg-[#EF4444]/10 text-[#EF4444] text-xs font-medium rounded-lg hover:bg-[#EF4444]/20 transition-colors disabled:opacity-50"
                  disabled={sending}
                  onclick={() => removeMember(member)}
                >
                  Quitar a {member.username}
                </button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {:else}
    <p class="text-center text-sm text-[#6B7280] py-8">Este tenant aún no tiene miembros</p>
  {/if}

  <!-- Alta manual de membresía -->
  <form
    class="mt-6 border-t border-[#2D3148] pt-5 flex flex-wrap items-end gap-3"
    onsubmit={(e) => {
      e.preventDefault();
      addMember();
    }}
  >
    <div class="flex flex-col gap-1">
      <label for="member-user" class="text-xs font-medium text-[#9CA3AF]">Usuario</label>
      <select
        id="member-user"
        bind:value={selectedUserId}
        disabled={sending}
        class="bg-[#2D3148] border border-[#374151] text-[#F9FAFB] text-sm rounded-lg px-3 py-2 min-w-48"
      >
        <option value="" disabled>Selecciona un usuario…</option>
        {#each assignable as user (user.id)}
          <option value={String(user.id)}>{user.username} ({user.email})</option>
        {/each}
      </select>
    </div>
    <div class="flex flex-col gap-1">
      <label for="member-role" class="text-xs font-medium text-[#9CA3AF]">Rol en el tenant</label>
      <select
        id="member-role"
        bind:value={selectedRole}
        disabled={sending}
        class="bg-[#2D3148] border border-[#374151] text-[#F9FAFB] text-sm rounded-lg px-3 py-2"
      >
        <option value="USER">USER</option>
        <option value="ADMIN">ADMIN</option>
        <option value="MANAGER">MANAGER</option>
        <option value="VIEWER">VIEWER</option>
      </select>
    </div>
    <button
      type="submit"
      disabled={!selectedUserId || sending}
      class="px-4 py-2 bg-[#6366F1] text-white text-sm font-medium rounded-lg hover:bg-[#5558E3] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {sending ? 'Guardando…' : 'Asignar'}
    </button>
  </form>
</div>
