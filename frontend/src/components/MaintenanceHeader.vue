<template>
  <header class="maintenance-header">
    <div>
      <h1 class="title">Maintenance</h1>
      <p class="subtitle">Service history for this car.</p>
    </div>

    <button type="button" class="add-button" @click="$emit('add')">
      Add new
    </button>
  </header>
</template>

<script setup>
defineEmits(['add'])
</script>

<style scoped>
.maintenance-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.title {
  margin: 0;
  color: var(--gb-heading);
  font-size: clamp(1.8rem, 4vw, 2.5rem);
  font-weight: 700;
}

.subtitle {
  margin: 4px 0 0;
  color: var(--gb-text-muted);
}

.add-button {
  border: none;
  border-radius: 999px;
  padding: 10px 16px;
  background: var(--gb-accent);
  color: #141820;
  font-weight: 700;
  cursor: pointer;
  margin-left: auto;
}

.add-button:hover {
  background: var(--gb-accent-hover);
}
</style>
