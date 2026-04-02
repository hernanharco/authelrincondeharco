<script lang="ts">
  import Icon from '../common/Icon.svelte';

  interface Props {
    title: string;
    value: string | number;
    iconName?: string;
    trend?: { value: number; isPositive: boolean };
    color?: 'primary' | 'success' | 'warning' | 'danger' | 'muted';
  }

  let { title, value, iconName, trend, color = 'primary' }: Props = $props();

  const bgColors = {
    primary: 'bg-[#6366F1]/10 text-[#6366F1]',
    success: 'bg-[#10B981]/10 text-[#10B981]',
    warning: 'bg-[#F59E0B]/10 text-[#F59E0B]',
    danger: 'bg-[#EF4444]/10 text-[#EF4444]',
    muted: 'bg-[#6B7280]/10 text-[#6B7280]',
  };
</script>

<div class="bg-[#1E2130] border border-[#2D3148] rounded-xl p-6 shadow-sm overflow-hidden">
  <div class="flex items-start justify-between gap-4">
    <div class="min-w-0 flex-1">
      <p class="text-sm text-[#9CA3AF] mb-1 truncate font-medium">{title}</p>
      <p class="text-2xl font-bold text-[#F9FAFB] truncate">{value}</p>

      {#if trend}
        <div
          class="flex items-center mt-2 text-xs font-semibold {trend.isPositive
            ? 'text-[#10B981]'
            : 'text-[#EF4444]'}"
        >
          <Icon name={trend.isPositive ? 'check' : 'arrow'} size="3" class="mr-1" />
          <span>{Math.abs(trend.value)}%</span>
        </div>
      {/if}
    </div>

    {#if iconName}
      <div
        class="rounded-xl flex items-center justify-center shrink-0 {bgColors[color]}"
        style="width: 48px; height: 48px; min-width: 48px;"
      >
        <Icon name={iconName} size="6" />
      </div>
    {/if}
  </div>
</div>
