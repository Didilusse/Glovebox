<template>
  <div class="garage-container">
    <h2 class="title">Garage</h2>
    
    <div v-for="car in inventory" :key="car.id" class="car-card">
      <div class="car-info-main">
        {{ car.make }} {{ car.model }}
      </div>
      <div class="car-stats">
        Year: {{ car.year || 'N/A' }}
      </div>
      <div class="car-stats">
       Mileage: {{ car.mileage !== null ? car.mileage + ' miles' : 'N/A' }}
      </div>
    </div>
  </div>
</template>

<script setup>
const cars = defineProps({
  inventory: Array
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

  .car-info-main {
    font-weight: bold;
    font-size: 1.1rem;
    margin-bottom: 5px;
  }

  .car-stats {
    font-size: 0.9rem;
    color: #666;
  }
</style>