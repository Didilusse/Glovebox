<template>
  <div class="garage-container">
    <h2 class="title">Maintenance List</h2>

    <div v-if="!maintenances.length" class="empty-state">
      No maintenance logs yet.
    </div>

    <div v-for="log in maintenances" :key="log._id" class="car-card">
      <div class="car-info-main">
        {{ log.work_done || 'Maintenance' }}
      </div>
      <div class="car-stats">Date: {{ log.date_of_service || 'N/A' }}</div>
      <div class="car-stats">Mileage: {{ log.mileage ?? 'N/A' }}</div>
      <div class="car-stats">Cost: {{ log.cost ?? 'N/A' }}</div>
      <div class="car-stats">Done by: {{ log.done_by || 'N/A' }}</div>
      <div class="car-stats" v-if="log.notes">Notes: {{ log.notes }}</div>
    </div>

    <button type="button" class="add-car-card">
      <h2>Total logs: {{ maintenances.length }}</h2>
    </button>
  </div>
</template>

<script setup>
defineProps({
  maintenances: {
    type: Array,
    default: () => []
  }
})
</script>

<style scoped>
  .garage-container {
    padding: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    border: 1px solid #ccc;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .title {
    font-weight: bold;
    text-align: center;
    margin-bottom: 20px;
  }

  .car-card {
    border: 1px solid #ccc;
    padding: 15px;
    margin: 10px 0;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    width: 100%;
    max-width: 300px;
    text-align: center; 
  }

  .add-car-card {
    appearance: none;
    border: 1px dashed #ccc;
    padding: 15px;
    margin: 10px 0;
    border-radius: 8px;
    box-shadow: none;
    width: 100%;
    max-width: 300px;
    text-align: center; 
    font-weight: bold;
    cursor: pointer;
    background: transparent;
    color: inherit;
  }

  .car-info-main {
    font-weight: bold;
    font-size: 1.1rem;
    margin-bottom: 5px;
  }

  .car-stats {
    font-size: 0.9rem;
    color: #666;
  }

  .empty-state {
    color: #666;
    margin-bottom: 12px;
  }
</style>