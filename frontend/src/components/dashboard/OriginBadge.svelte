<script lang="ts">
  interface Props {
    origin: string;
    class?: string;
  }

  let { origin, class: className = '' }: Props = $props();

  function getDomainColor(domain: string): string {
    const colors = [
      'bg-[#6366F1]',
      'bg-[#10B981]',
      'bg-[#F59E0B]',
      'bg-[#EF4444]',
      'bg-[#8B5CF6]',
      'bg-[#EC4899]',
      'bg-[#14B8A6]',
      'bg-[#F97316]',
    ];

    let hash = 0;
    for (let i = 0; i < domain.length; i++) {
      hash = domain.charCodeAt(i) + ((hash << 5) - hash);
    }

    return colors[Math.abs(hash) % colors.length];
  }

  function getDomainDisplay(origin: string): string {
    if (!origin || origin === 'unknown') return 'Desconocido';

    try {
      const url = new URL(origin);
      return url.hostname;
    } catch {
      return origin;
    }
  }

  const domainColor = $derived(getDomainColor(origin));
  const domainDisplay = $derived(getDomainDisplay(origin));
</script>

<span class={`px-2 py-1 rounded-full text-xs font-medium text-white ${domainColor} ${className}`}>
  {domainDisplay}
</span>
