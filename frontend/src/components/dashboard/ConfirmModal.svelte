<script lang="ts">
  interface Props {
    isOpen: boolean;
    title: string;
    message: string;
    confirmText?: string;
    cancelText?: string;
    danger?: boolean;
    onConfirm: () => void;
    onCancel: () => void;
  }

  let {
    isOpen,
    title,
    message,
    confirmText = 'Confirmar',
    cancelText = 'Cancelar',
    danger = false,
    onConfirm,
    onCancel,
  }: Props = $props();

  function handleConfirm() {
    onConfirm();
  }

  function handleCancel() {
    onCancel();
  }

  function handleBackdropClick(event: MouseEvent) {
    if (event.target === event.currentTarget) {
      handleCancel();
    }
  }
</script>

{#if isOpen}
  <div
    class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
    role="dialog"
    aria-modal="true"
    aria-labelledby="modal-title"
    aria-describedby="modal-message"
    tabindex="-1"
    onclick={handleBackdropClick}
    onkeydown={(e) => e.key === 'Escape' && handleCancel()}
  >
    <div class="bg-[#1E2130] border border-[#2D3148] rounded-lg p-6 max-w-md w-full mx-4">
      <h3 id="modal-title" class="text-lg font-semibold text-[#F9FAFB] mb-2">{title}</h3>
      <p id="modal-message" class="text-[#9CA3AF] mb-6">{message}</p>

      <div class="flex justify-end space-x-3">
        <button
          type="button"
          class="px-4 py-2 text-sm font-medium text-[#9CA3AF] bg-[#2D3148] rounded-lg hover:bg-[#374151] transition-colors"
          onclick={handleCancel}
        >
          {cancelText}
        </button>
        <button
          type="button"
          class={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
            danger
              ? 'bg-[#EF4444] text-white hover:bg-[#DC2626]'
              : 'bg-[#6366F1] text-white hover:bg-[#5558E3]'
          }`}
          onclick={handleConfirm}
        >
          {confirmText}
        </button>
      </div>
    </div>
  </div>
{/if}
