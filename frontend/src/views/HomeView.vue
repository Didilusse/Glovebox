<template>
  <div class="app-container">
    <Toast />

    <div class="main-container">
      <CarList
        :inventory="cars"
        @add="handleShowCarForm"
        @delete="handleDeleteCar"
        @view="handleViewCar"
        class="car-list-section"
      />

      <transition name="fade">
        <div
          v-if="isCarFormVisible"
          class="popup-overlay"
          @click.self="handleCloseCarForm"
        >
          <CarForm
            :api-base="API_BASE"
            @created="handleCarCreated"
            @close="handleCloseCarForm"
          />
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import CarList from '../components/CarList.vue'
import CarForm from '../components/CarForm.vue'

import Toast, { showToast } from '../components/Toast.vue'
const envApiBase = import.meta.env.VITE_API_BASE_URL?.trim()
const API_BASE = envApiBase || `${window.location.protocol}//${window.location.hostname}:8000`
const router = useRouter()
const cars = ref([])
const isCarFormVisible = ref(false)

onMounted(async () => {
  await handleFetchCars()
})
function handleViewCar(carId) {
  router.push(`/car/${carId}`)
}

function handleShowCarForm() {
  isCarFormVisible.value = true
}

function handleCloseCarForm() {
  isCarFormVisible.value = false
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

function handleCarCreated(car) {
  cars.value = [...cars.value, car]
  handleCloseCarForm()
}


async function handleDeleteCar(carId) {
  const response = await fetch(`${API_BASE}/cars/${carId}`, {
    method: 'DELETE'
  })
  if (!response.ok) {
    showToast('Failed to delete car', 'error')
    throw new Error('Failed to delete car')
  }
  cars.value = cars.value.filter(existingCar => existingCar._id !== carId)
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

.popup-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 72px 24px 24px;
  background: rgba(0, 0, 0, 0.6);
  z-index: 1000;
}

.car-list-section {
  width: 100%;
  max-width: 420px;
  justify-self: center;
  align-self: center;
  display: block;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

</style>