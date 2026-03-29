<script>
  let { data = [] } = $props();
  let total = $derived(data.reduce((acc, curr) => acc + (curr.value || 0), 0));
</script>

<div class="space-y-6">
  <div class="flex items-end h-64 gap-3 px-4 border-b border-gray-100 bg-gray-50/50 rounded-xl p-4">
    {#each data as item}
      <div class="flex-1 flex flex-col items-center group h-full justify-end">
        <div 
          class="w-full bg-blue-500 rounded-t-lg transition-all duration-500 hover:bg-indigo-600 relative"
          style="height: {total > 0 ? (item.value / total * 100) : 0}%"
        >
          <span class="absolute -top-10 left-1/2 -translate-x-1/2 bg-gray-800 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
            {item.value} usuarios
          </span>
        </div>
        <span class="text-[10px] text-gray-400 mt-3 truncate w-full text-center font-bold uppercase tracking-tighter">
          {item.name}
        </span>
      </div>
    {/each}
  </div>

  <div class="flex justify-between items-center text-xs px-2">
    <p class="text-gray-400 italic">Visualización de tráfico por origen</p>
    <p class="font-semibold text-gray-700">Total: {total}</p>
  </div>
</div>
