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
  font-size: 1.75rem;
}

.subtitle {
  margin: 4px 0 0;
  color: #666;
}

.add-button {
  border: none;
  border-radius: 8px;
  padding: 10px 16px;
  background: #222;
  color: white;
  cursor: pointer;
  margin-left: auto;
}
</style>