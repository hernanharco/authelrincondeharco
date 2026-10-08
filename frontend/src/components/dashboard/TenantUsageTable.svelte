<script lang="ts">
  import { formatDate } from '../../utils/date';

  interface UsageRow {
    slug: string;
    name: string;
    personas: number;
    admins: number;
    activas_30d: number;
    activos: number;
    ultimo_acceso: string | null;
  }

  let { usage }: { usage: UsageRow[] } = $props();
</script>

{#if usage.length === 0}
  <p class="text-center text-sm text-[#6B7280] py-8">No hay tenants con usuarios todavía</p>
{:else}
  <div class="overflow-x-auto">
    <table class="w-full">
      <thead>
        <tr class="border-b border-[#2D3148]">
          <th class="text-left py-3 px-4 text-sm font-medium text-[#9CA3AF]">Tenant</th>
          <th class="text-left py-3 px-4 text-sm font-medium text-[#9CA3AF]">Personas</th>
          <th class="text-left py-3 px-4 text-sm font-medium text-[#9CA3AF]">Admins</th>
          <th class="text-left py-3 px-4 text-sm font-medium text-[#9CA3AF]">Activas 30d</th>
          <th class="text-left py-3 px-4 text-sm font-medium text-[#9CA3AF]">Último acceso</th>
        </tr>
      </thead>
      <tbody>
        {#each usage as row (row.slug)}
          <tr class="relative border-b border-[#2D3148] hover:bg-[#2D3148]/50 transition-colors cursor-pointer">
            <td class="py-3 px-4">
              <a
                href={`/dashboard/tenants/${row.slug}`}
                class="z-10 relative text-sm font-medium text-[#F9FAFB] hover:text-[#818CF8] transition-colors after:absolute after:inset-0 after:content-['']"
              >
                {row.name}
              </a>
              <div class="text-xs text-[#9CA3AF]">{row.slug}</div>
            </td>
            <td class="py-3 px-4 text-sm text-[#9CA3AF]">{row.personas}</td>
            <td class="py-3 px-4 text-sm text-[#9CA3AF]">{row.admins}</td>
            <td class="py-3 px-4 text-sm text-[#9CA3AF]">{row.activas_30d}</td>
            <td class="py-3 px-4 text-sm text-[#9CA3AF]">
              {row.ultimo_acceso ? formatDate(row.ultimo_acceso) : '—'}
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}
