<template>
  <div class="car-detail">
    <h1>{{ carMake }}</h1>
    <p><strong>Model:</strong> {{ model }}</p>
    <p><strong>Year:</strong> {{ year }}</p>
    <p><strong>Mileage:</strong> {{ mileage }}</p>
    <p><strong>Initial Mileage:</strong> {{ initial_mileage }}</p>
    <p><strong>VIN:</strong> {{ vin }}</p>
    <p><strong>License Plate:</strong> {{ license_plate }}</p>
    <p><strong>Fuel Type:</strong> {{ fuel_type }}</p>
    <p><strong>Purchase Date:</strong> {{ purchase_date }}</p>
    <p><strong>Purchase Price:</strong> {{ purchase_price }}</p>
  </div>
  <button @click="handleBack">Back</button>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import Toast, { showToast } from '../components/Toast.vue'
const route = useRoute()
const car = ref(null)
const envApiBase = import.meta.env.VITE_API_BASE_URL?.trim()
const API_BASE = envApiBase || `${window.location.protocol}//${window.location.hostname}:8000`

const carMake = computed(() => {
  if (!car.value) {
    return 'Loading car...'
  }
  
  return `${car.value.make ?? ''} ${car.value.model ?? ''}`.trim() || 'Car details'
})

const model = computed(() => car.value?.model ?? '')
const year = computed(() => car.value?.year ?? '')
const mileage = computed(() => car.value?.mileage ?? '')
const initial_mileage = computed(() => car.value?.initial_mileage ?? '')
const vin = computed(() => car.value?.vin ?? '')
const license_plate = computed(() => car.value?.license_plate ?? '')
const fuel_type = computed(() => car.value?.fuel_type ?? '')
const purchase_date = computed(() => car.value?.purchase_date ?? '')
const purchase_price = computed(() => car.value?.purchase_price ?? '')

onMounted(() => {
  handleFetchCar()
})

async function handleFetchCar() {
  const response = await fetch(`${API_BASE}/cars/${route.params.carId}`)
  if (!response.ok) {
    showToast('Failed to fetch car', 'error')
    throw new Error('Failed to fetch car')
  }
  const data = await response.json()
  car.value = data
  showToast('Car fetched successfully', 'success')
}

function handleBack() {
  window.history.back()
}

</script>

<style scoped>

</style>