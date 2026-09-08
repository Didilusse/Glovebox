<template>
  <dialog ref="dialog" class="vehicle-dialog" :aria-label="title" @cancel.prevent="$emit('close')" @click="onBackdrop">
    <header><h2>{{ title }}</h2><button type="button" aria-label="Close dialog" @click="$emit('close')">Close</button></header>
    <slot />
  </dialog>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue'
defineProps({ title: { type: String, required: true } })
const emit = defineEmits(['close'])
const dialog = ref(null)
const previousFocus = document.activeElement
onMounted(() => {
  if (dialog.value.showModal) dialog.value.showModal()
  else dialog.value.setAttribute('open', '')
})
onBeforeUnmount(() => {
  dialog.value?.close?.()
  previousFocus?.focus()
})
function onBackdrop(event) {
  if (event.target !== dialog.value) return
  const rect = dialog.value.getBoundingClientRect()
  if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) emit('close')
}
</script>

<style>
.vehicle-dialog { width: min(680px, calc(100% - 28px)); max-height: calc(100dvh - 40px); margin: auto; padding: 24px; overflow: auto; border: 1px solid var(--gb-border-strong); border-radius: 16px; background: var(--gb-surface); color: var(--gb-text); }
.vehicle-dialog::backdrop { background: rgb(0 0 0 / 65%); }
.vehicle-dialog header { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 20px; }
.vehicle-dialog h2 { color: var(--gb-heading); font-size: 1.4rem; }
.vehicle-dialog form, .vehicle-dialog fieldset { display: grid; gap: 14px; }
.vehicle-dialog fieldset { min-width: 0; border: 0; padding: 0; }
.vehicle-dialog label { display: grid; gap: 5px; }
.vehicle-dialog input, .vehicle-dialog select { width: 100%; min-width: 0; padding: 10px; border: 1px solid var(--gb-border-strong); border-radius: 8px; background: var(--gb-background-deep); color: var(--gb-heading); font: inherit; }
.vehicle-dialog button { padding: 9px 14px; border: 1px solid var(--gb-border-strong); border-radius: 8px; background: var(--gb-background-deep); color: var(--gb-accent); cursor: pointer; }
.vehicle-dialog button:disabled { opacity: .5; cursor: wait; }
.vehicle-dialog small { color: var(--gb-text-muted); }
.vehicle-dialog [role=alert] { margin: 12px 0; color: var(--gb-danger); }
.vehicle-dialog .dialog-actions { display: flex; flex-wrap: wrap; gap: 8px; }
</style>
