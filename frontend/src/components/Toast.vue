<template>
  <transition name="fade">
    <div v-if="toastStore.visible" :class="['toast-popup', toastStore.type]">
      {{ toastStore.message }}
    </div>
  </transition>
</template>

<script>
import { reactive } from 'vue';

export const toastStore = reactive({
  message: '',
  type: 'success',
  visible: false
});

export function showToast(message, type = 'success') {
  toastStore.message = message;
  toastStore.type = type;
  toastStore.visible = true;

  setTimeout(() => {
    toastStore.visible = false;
  }, 3000);
}

export default {
  name: 'Toast',
  setup() {
    // We return toastStore so the <template> can see it
    return { toastStore };
  }
};
</script>

<style scoped>
.toast-popup {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  padding: 12px 24px;
  border-radius: 8px;
  color: white;
  font-weight: 500;
  z-index: 10000;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  min-width: 200px;
  text-align: center;
}
.success { background-color: #2e7d32; }
.error { background-color: #d32f2f; }
.warning { background-color: #ff9800; }
.info { background-color: #1976d2; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.4s ease, transform 0.4s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(10px); }
</style>