<template>
  <header class="maintenance-header">
    <div>
      <h1 class="title">Maintenance</h1>
      <p class="subtitle">Service history for this car.</p>
    </div>

    <div class="actions">
      <button type="button" class="import-button" @click="$emit('import')">Import CARFAX</button>
      <button type="button" class="add-button" @click="$emit('add')">Add new</button>
    </div>
  </header>
</template>

<script setup>
defineEmits(['add', 'import'])
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

.actions {
  display: flex;
  gap: 10px;
  margin-left: auto;
}

.add-button,
.import-button {
  border: none;
  border-radius: 999px;
  padding: 10px 16px;
  background: var(--gb-accent);
  color: #141820;
  font-weight: 700;
  cursor: pointer;
}

.add-button:hover {
  background: var(--gb-accent-hover);
}

.import-button {
  border: 1px solid var(--gb-border-strong);
  background: transparent;
  color: var(--gb-accent);
}

.import-button:hover {
  border-color: var(--gb-accent);
}

@media (max-width: 600px) {
  .maintenance-header {
    flex-direction: column;
  }

  .actions {
    width: 100%;
    margin-left: 0;
  }

  .actions button {
    flex: 1;
  }
}
</style>
