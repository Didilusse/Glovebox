<template>
  <div class="garage-container">
    <h2 class="title">Garage</h2>

    <div v-for="car in inventory" :key="car._id" class="car-card">
      <div class="car-info-main">
        {{ car.make }} {{ car.model }}
      </div>
      <div class="car-stats">
        Year: {{ car.year || 'N/A' }}
      </div>
      <div class="car-stats">
       Mileage: {{ car.mileage !== null ? car.mileage + ' miles' : 'N/A' }}
      </div>
      <button class="view" @click="handleView(car._id)">View</button>
      <button class="delete" @click="handleDelete(car._id)">Delete</button>
    </div>

    <button type="button" @click="handleAdd" class="add-car-card">
      <h2>Add a new car</h2>
    </button>
  </div>
</template>

<script setup>
const emit = defineEmits(['view', 'delete', 'add'])

defineProps({
  inventory: Array
})

function handleView(carId) {
  emit('view', carId)
}

function handleDelete(carId) {
  emit('delete', carId)
}

function handleAdd() {
  emit('add')
}
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
  .delete {
    background-color: #dc3545;
    color: white;
    border: 1px solid #dc3545;
    padding: 5px 10px;
    border-radius: 5px;
    cursor: pointer;
    margin-left: 10px;
  }

  .view {
    background-color: #007bff;
    color: white;
    border: 1px solid #007bff;
    padding: 5px 10px;
    border-radius: 5px;
    cursor: pointer;
    margin-left: 10px;
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
</style>