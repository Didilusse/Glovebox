<template>
  <div class="app-container">
    <Toast />

    <div class="main-container">
      <div class="form-section">
        <h2>Add a Car</h2>
        <div>Enter Car Make:</div>
        <input v-model="make" placeholder="Toyota" />

        <div>Enter Car Model:</div>
        <input v-model="model" placeholder="Camry" />

        <div>Enter Car Year:</div>
        <input v-model="year" placeholder="2020" />

        <div>Enter Car Mileage:</div>
        <input v-model="mileage" placeholder="50000" />
        <button @click="handleCreateCar">Create Car</button>
      </div>

      <CarList :inventory="cars" @delete="handleDeleteCar" class="car-list-section" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import CarList from './components/CarList.vue'
import Toast, { showToast } from './components/Toast.vue'
const envApiBase = import.meta.env.VITE_API_BASE_URL?.trim()
const API_BASE = envApiBase || `${window.location.protocol}//${window.location.hostname}:8000`
const make = ref('')
const model = ref('')
const year = ref('')
const mileage = ref('')
const isFormValid = computed(() => {
  return make.value.trim() !== '' &&
         model.value.trim() !== '' &&
         year.value.toString().length === 4 &&
         year.value > 0 &&
         mileage.value !== null &&
         mileage.value.toString().trim() !== '' &&
         mileage.value >= 0
})

const cars = ref([])

onMounted(async () => {
  await handleFetchCars()
})

async function handleFetchCars() {
  const response = await fetch(`${API_BASE}/cars/`)
  if (!response.ok) {
    showToast('Failed to fetch cars', 'error')
    throw new Error('Failed to fetch cars')
  }
  const data = await response.json()
  cars.value = data
}

async function handleCreateCar() {
  if (!isFormValid.value) {
    showToast('Please fill in all required fields correctly', 'warning')
    return
  }

  const payload = {
    make: make.value,
    model: model.value,
    year: year.value,
    mileage: mileage.value
  }

  const response = await fetch(`${API_BASE}/cars/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  })
  if (!response.ok) {
    showToast('Failed to create car', 'error')
    throw new Error('Failed to create car')
  }

  const data = await response.json()
  cars.value.push(data)
  make.value = ''
  model.value = ''
  year.value = ''
  mileage.value = ''
  await handleFetchCars()
  showToast('Car created successfully', 'success')
}


async function handleDeleteCar(carId) {
  const response = await fetch(`${API_BASE}/cars/${carId}`, {
    method: 'DELETE'
  })
  if (!response.ok) {
    showToast('Failed to delete car', 'error')
    throw new Error('Failed to delete car')
  }
  // Remove the deleted car from the list
  cars.value = cars.value.filter(car => car._id !== carId)
  console.log(`Car with ID ${carId} deleted successfully`)
  // Refresh the car list
  showToast('Car deleted successfully', 'success')
}
</script>

<style>
.app-container {
  min-height: 100vh;
  width: 100%;
  padding: 24px;
}

.main-container {
display: grid;
grid-template-columns: 1fr 1fr;
gap: 32px;
align-items: center;
margin-top: clamp(40px, 8vh, 100px);
}



.form-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
}


.form-section input,
.form-section button {
  width: 320px; /* keeps controls aligned */
  max-width: 100%;
}

.car-list-section {
width: 100%;
max-width: 420px;
justify-self: center;
align-self: center;
display: block;
}

.garage-container {
width: 100%;
max-width: 420px;
}

</style>