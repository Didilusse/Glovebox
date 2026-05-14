<template>
  <section class="maintenance-list">
    <div v-if="!maintenances.length" class="empty-state">
      No maintenance logs yet.
    </div>

    <MaintenanceLogCard
      v-for="log in maintenances"
      :key="log._id"
      :log="log"
      @delete="$emit('delete', $event)"
    />
  </section>
</template>

<script setup>
import MaintenanceLogCard from './MaintenanceLogCard.vue'

defineEmits(['delete'])

defineProps({
  maintenances: {
    type: Array,
    default: () => []
  }
})
</script>

<style scoped>
  .maintenance-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .empty-state {
    color: #666;
    padding: 12px 0;
  }
</style>