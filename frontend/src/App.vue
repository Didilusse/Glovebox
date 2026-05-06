<template>

<div>Enter Car Make:</div>
<input v-model="make" placeholder="Toyota" />

<div>Enter Car Model:</div>
<input v-model="model" placeholder="Camry" />

<div>Enter Car Year:</div>
<input v-model="year" placeholder="2020" />

<div>Enter Car Mileage:</div>
<input v-model="mileage" placeholder="50000" />


<CarList :inventory="cars" />



<div> {{ selected }}</div>

<button @click="handleCreateCar">Create Car</button>

</template>


<script setup>
import { ref, onMounted } from 'vue'
import CarList from './components/CarList.vue'
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const make = ref('')
const model = ref('')
const year = ref('')
const mileage = ref('')
const selected = ref('')


const cars = ref([])

onMounted(async () => {
  const response = await fetch(`${API_BASE}/cars/`)
  if (!response.ok) {
    status.value = 'Failed to fetch cars'
    throw new Error('Failed to fetch cars')
  }
  const data = await response.json()
  cars.value = data
})

async function handleCreateCar() {
  const payload = {
    make: make.value,
    model: model.value,
    year: year.value,
    mileage: mileage.value
  }

  console.log(payload)

  const response = await fetch(`${API_BASE}/cars/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  })
  if (!response.ok) {
    // status.value = 'Failed to create car'
    throw new Error('Failed to create car')
  }
  // status.value = 'Car created successfully'

  const data = await response.json()
  selected.value = data
  cars.value.push(data)
  make.value = ''
  model.value = ''
  year.value = ''
  mileage.value = ''
}
</script>

<style>
  div {
    align-items: center;
  }
</style>