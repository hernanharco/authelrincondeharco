<script lang="ts">
  interface Props {
    src?: string;
    alt?: string;
    name?: string;
    size?: 'sm' | 'md' | 'lg' | 'xl';
    class?: string;
  }

  let { src, alt = '', name = '', size = 'md', class: className = '' }: Props = $props();

  const sizeClasses = {
    sm: 'w-6 h-6 text-xs',
    md: 'w-8 h-8 text-sm',
    lg: 'w-12 h-12 text-lg',
    xl: 'w-16 h-16 text-xl',
  };

  function getInitials(name: string): string {
    return name
      .split(' ')
      .map((part) => part.charAt(0).toUpperCase())
      .slice(0, 2)
      .join('');
  }

  function getAvatarColor(name: string): string {
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
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }

    return colors[Math.abs(hash) % colors.length];
  }

  const avatarColor = $derived(getAvatarColor(name));
  const initials = $derived(getInitials(name));
</script>

{#if src}
  <img {src} {alt} class={`${sizeClasses[size]} rounded-full object-cover ${className}`} />
{:else if name}
  <div
    class={`${sizeClasses[size]} ${avatarColor} rounded-full flex items-center justify-center text-white font-semibold ${className}`}
  >
    {initials}
  </div>
{:else}
  <div
    class={`${sizeClasses[size]} bg-[#2D3148] rounded-full flex items-center justify-center text-[#9CA3AF] ${className}`}
  >
    <svg
      class="w-1/2 h-1/2 max-w-[20px] max-h-[20px]"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
      />
    </svg>
  </div>
{/if}
