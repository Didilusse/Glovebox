<template>
  <div class="app-container">
    <Toast />

    <div class="main-container">
      <NewCar
        v-if="isNewCarVisible"
        :api-base="API_BASE"
        @created="handleCarCreated"
      />
      <CarList
        :inventory="cars"
        @add="handleShowNewCar"
        @delete="handleDeleteCar"
        @view="handleViewCar"
        class="car-list-section"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import CarList from '../components/CarList.vue'
import NewCar from '../components/NewCar.vue'

import Toast, { showToast } from '../components/Toast.vue'
const envApiBase = import.meta.env.VITE_API_BASE_URL?.trim()
const API_BASE = envApiBase || `${window.location.protocol}//${window.location.hostname}:8000`
const router = useRouter()
const cars = ref([])
const isNewCarVisible = ref(false)

onMounted(async () => {
  await handleFetchCars()
})
function handleViewCar(carId) {
  router.push(`/car/${carId}`)
}

function handleShowNewCar() {
  isNewCarVisible.value = true
}

async function handleFetchCars() {
  const response = await fetch(`${API_BASE}/cars/`)
  if (!response.ok) {
    showToast('Failed to fetch cars', 'error')
    throw new Error('Failed to fetch cars')
  }
  const data = await response.json()
  cars.value = data
}

async function handleCarCreated(car) {
  await handleFetchCars()
  isNewCarVisible.value = false
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