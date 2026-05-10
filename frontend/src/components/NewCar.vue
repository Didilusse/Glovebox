<template>
  <div class="new-car">
    <h2>Add a Car</h2>

    <form class="form-section" @submit.prevent="handleCreateCar">
      <div>Enter Car Make:</div>
      <input v-model="make" placeholder="Toyota" />

      <div>Enter Car Model:</div>
      <input v-model="model" placeholder="Camry" />

      <div>Enter Car Year:</div>
      <input v-model="year" placeholder="2020" />

      <div>Enter Car Mileage:</div>
      <input v-model="mileage" placeholder="50000" />

      <button type="submit">Create Car</button>
    </form>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { showToast } from './Toast.vue'

const props = defineProps({
  apiBase: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['created'])

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

  const response = await fetch(`${props.apiBase}/cars/`, {
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
  emit('created', data)

  make.value = ''
  model.value = ''
  year.value = ''
  mileage.value = ''
  showToast('Car created successfully', 'success')
}
</script>

<style scoped>
.new-car {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border: 1px solid #ccc;
  padding: 20px;
  margin: 20px 0;
  border-radius: 8px;
  box-shadow: none;
  width: 100%;
  max-width: 420px;
  text-align: center;
}

.form-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
}

.form-section input,
.form-section button {
  width: 320px;
  max-width: 100%;
}
</style>