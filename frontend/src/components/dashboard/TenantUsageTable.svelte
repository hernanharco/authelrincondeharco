<script lang="ts">
  import { formatDate } from '../../utils/date';
  import { apiUrl, ENDPOINTS } from '../../config/api.config';
  import UserAvatar from './UserAvatar.svelte';
  import RoleBadge from './RoleBadge.svelte';
  import StatusBadge from './StatusBadge.svelte';

  interface UsageRow {
    slug: string;
    name: string;
    personas: number;
    admins: number;
    activas_30d: number;
    activos: number;
    ultimo_acceso: string | null;
  }

  interface TenantMember {
    id: string;
    username: string;
    email: string;
    role_tenant: string;
    status: string;
    login_count: number;
    last_login: string | null;
  }

  interface RowState {
    expanded: boolean;
    loading: boolean;
    error: string | null;
    members: TenantMember[] | null;
  }

  // `token` lo inyecta la página desde el SSR (cookie access_token httpOnly,
  // ilegible desde JS y el frontend y el backend son dominios distintos)
  let { usage, token }: { usage: UsageRow[]; token: string } = $props();

  // Cache de miembros por slug: sin refetch al re-expandir
  const memberCache = new Map<string, TenantMember[]>();
  // Estado reactivo por fila (expansión, loading, error, miembros).
  // Se crea perezosamente desde los handlers (nunca en la plantilla: Svelte 5
  // prohíbe mutar $state en expresiones de template).
  let rowStates = $state<Record<string, RowState>>({});
  const defaultState: RowState = { expanded: false, loading: false, error: null, members: null };

  function stateFor(slug: string): RowState {
    return rowStates[slug] ?? defaultState;
  }

  function ensureState(slug: string): RowState {
    if (!rowStates[slug]) {
      rowStates[slug] = {
        expanded: false,
        loading: false,
        error: null,
        members: memberCache.get(slug) ?? null,
      };
    }
    return rowStates[slug];
  }

  // Los badges esperan las claves en mayúsculas (ADMIN/ACTIVE); el backend
  // puede devolverlas en otro case según cómo se escribió role_tenant.
  function enumKey(value: string): string {
    return value.trim().toUpperCase();
  }

  async function loadMembers(slug: string): Promise<void> {
    const state = ensureState(slug);
    state.loading = true;
    state.error = null;
    try {
      const headers = { Authorization: `Bearer ${token}` };
      // Paso A: resolver el id del tenant por slug
      const tenantRes = await fetch(apiUrl(ENDPOINTS.tenants.bySlug(slug)), { headers });
      if (!tenantRes.ok) throw new Error('tenant fetch failed');
      const tenant: { id: string } = await tenantRes.json();
      // Paso B: cargar miembros
      const res = await fetch(apiUrl(ENDPOINTS.tenants.users(tenant.id)), { headers });
      if (!res.ok) throw new Error('members fetch failed');
      const members: TenantMember[] = await res.json();
      memberCache.set(slug, members);
      state.members = members;
    } catch {
      state.error = 'No se pudieron cargar los miembros';
    } finally {
      state.loading = false;
    }
  }

  async function toggle(slug: string): Promise<void> {
    const state = ensureState(slug);
    state.expanded = !state.expanded;
    if (state.expanded && state.members === null && !state.loading) {
      await loadMembers(slug);
    }
  }
</script>

{#if usage.length === 0}
  <p class="text-center text-sm text-[#6B7280] py-8">No hay tenants con usuarios todavía</p>
{:else}
  <div class="overflow-x-auto">
    <table class="w-full">
      <thead>
        <tr class="border-b border-[#2D3148]">
          <th class="text-left py-3 px-4 text-xs font-semibold uppercase tracking-wider text-[#6B7280]">Tenant</th>
          <th class="text-left py-3 px-4 text-xs font-semibold uppercase tracking-wider text-[#6B7280]">Personas</th>
          <th class="text-left py-3 px-4 text-xs font-semibold uppercase tracking-wider text-[#6B7280]">Admins</th>
          <th class="text-left py-3 px-4 text-xs font-semibold uppercase tracking-wider text-[#6B7280]">Activas 30d</th>
          <th class="text-left py-3 px-4 text-xs font-semibold uppercase tracking-wider text-[#6B7280]">Último acceso</th>
        </tr>
      </thead>
      <tbody>
        {#each usage as row, i (row.slug)}
          {@const state = stateFor(row.slug)}
          <tr class="relative border-b border-[#2D3148] hover:bg-[#2D3148]/40 transition-colors cursor-pointer">
            <td class="py-3 px-4">
              <div class="flex items-center gap-3">
                <span class="w-5 shrink-0 text-right text-xs font-medium tabular-nums text-[#4B5563]" aria-hidden="true">
                  {i + 1}
                </span>
                <UserAvatar name={row.name} size="sm" class="shrink-0" />
                <div class="min-w-0">
                  <a
                    href={`/dashboard/tenants/${row.slug}`}
                    class="z-10 relative block text-sm font-medium text-[#F9FAFB] hover:text-[#818CF8] transition-colors after:absolute after:inset-0 after:content-['']"
                  >
                    {row.name}
                  </a>
                  <div class="text-xs text-[#9CA3AF]">{row.slug}</div>
                </div>
              </div>
            </td>
            <td class="py-3 px-4 text-sm font-semibold tabular-nums {row.personas > 0 ? 'text-[#F9FAFB]' : 'text-[#4B5563]'}">
              {row.personas}
            </td>
            <td class="py-3 px-4 text-sm font-semibold tabular-nums {row.admins > 0 ? 'text-[#F9FAFB]' : 'text-[#4B5563]'}">
              {row.admins}
            </td>
            <td class="py-3 px-4 text-sm font-semibold tabular-nums {row.activas_30d > 0 ? 'text-[#818CF8]' : 'text-[#4B5563]'}">
              {row.activas_30d}
            </td>
            <td class="py-3 px-4 text-sm text-[#9CA3AF] tabular-nums">
              <div class="flex items-center justify-between gap-2">
                <span>{row.ultimo_acceso ? formatDate(row.ultimo_acceso) : '—'}</span>
                <!-- Chevron por encima del stretched-link (z-20) que no navega -->
                <button
                  type="button"
                  class="relative z-20 p-1.5 rounded-md text-[#9CA3AF] hover:text-[#818CF8] hover:bg-[#2D3148] transition-colors cursor-pointer"
                  aria-expanded={state.expanded}
                  aria-label={`Ver miembros de ${row.name}`}
                  onclick={(e) => { e.stopPropagation(); e.preventDefault(); toggle(row.slug); }}
                >
                  <svg
                    class={`w-4 h-4 transition-transform ${state.expanded ? 'rotate-180' : ''}`}
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      fill-rule="evenodd"
                      d="M5.23 7.21a.75.75 0 011.06.02L10 11.17l3.71-3.94a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
                      clip-rule="evenodd"
                    />
                  </svg>
                </button>
              </div>
            </td>
          </tr>
          {#if state.expanded}
            <tr class="border-b border-[#2D3148]">
              <td colspan={5} class="px-4 py-3 bg-[#111827]/60">
                {#if state.loading}
                  <div class="flex items-center gap-2 px-1 py-1 text-sm text-[#9CA3AF]">
                    <svg class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                    </svg>
                    Cargando miembros…
                  </div>
                {:else if state.error}
                  <div class="px-1 py-1">
                    <p class="text-sm text-[#F9FAFB]">{state.error}.</p>
                    <a
                      href={`/dashboard/tenants/${row.slug}`}
                      class="text-sm text-[#818CF8] hover:underline"
                    >
                      Ver ficha completa del tenant
                    </a>
                  </div>
                {:else if state.members === null || state.members.length === 0}
                  <p class="px-1 py-1 text-sm text-[#9CA3AF]">Sin miembros</p>
                {:else}
                  <ul class="rounded-lg border border-[#2D3148] divide-y divide-[#2D3148] overflow-hidden">
                    {#each state.members as member (member.id)}
                      <li class="flex flex-wrap items-center gap-x-4 gap-y-2 bg-[#1E2130] px-4 py-2.5 transition-colors hover:bg-[#2D3148]/50">
                        <UserAvatar name={member.username} size="sm" class="shrink-0" />
                        <div class="min-w-0 flex-1">
                          <div class="truncate text-sm font-medium text-[#F9FAFB]">{member.username}</div>
                          <div class="truncate text-xs text-[#9CA3AF]">{member.email}</div>
                        </div>
                        <div class="flex shrink-0 items-center gap-2">
                          <RoleBadge role={enumKey(member.role_tenant)} />
                          <StatusBadge status={enumKey(member.status)} />
                        </div>
                        <div class="w-28 shrink-0 text-right text-xs tabular-nums text-[#9CA3AF]">
                          {member.last_login ? formatDate(member.last_login) : '—'}
                        </div>
                      </li>
                    {/each}
                  </ul>
                {/if}
              </td>
            </tr>
          {/if}
        {/each}
      </tbody>
    </table>
  </div>
{/if}
