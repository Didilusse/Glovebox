<template>
  <section class="maintenance-list">
    <div v-if="!maintenances.length" class="empty-state">
      {{ hasRecords ? 'No maintenance records match your search.' : 'No maintenance logs yet.' }}
    </div>

    <MaintenanceLogCard
      v-for="log in maintenances"
      :key="log._id"
      :log="log"
      @delete="$emit('delete', $event)"
      @edit="$emit('edit', $event)"
    />
  </section>
</template>

<script setup>
import MaintenanceLogCard from './MaintenanceLogCard.vue'

defineEmits(['delete', 'edit'])

defineProps({
  maintenances: {
    type: Array,
    default: () => []
  },
  hasRecords: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.maintenance-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.empty-state {
  padding: 32px;
  border: 1px dashed var(--gb-border-strong);
  border-radius: 16px;
  color: var(--gb-text-muted);
  text-align: center;
}
</style>
