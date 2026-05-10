<template>
  <div class="car-form">
    <button type="button" class="close-button" aria-label="Close form" @click="emit('close')">
      &times;
    </button>

    <h2>Add a Car</h2>

    <form class="form-section" @submit.prevent="handleCreateCar">
      <label>
        <span>Enter Car Make:</span>
        <input v-model.trim="make" placeholder="Toyota" />
      </label>

      <label>
        <span>Enter Car Model:</span>
        <input v-model.trim="model" placeholder="Camry" />
      </label>

      <label>
        <span>Enter Car Year:</span>
        <input v-model="year" min="1900" max="9999" placeholder="2020" />
      </label>

      <label>
        <span>Enter Car Mileage:</span>
        <input v-model="mileage" min="0" placeholder="50000" />
      </label>

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

const emit = defineEmits(['created', 'close'])

const make = ref('')
const model = ref('')
const year = ref('')
const mileage = ref('')

const yearNumber = computed(() => Number(year.value))
const mileageNumber = computed(() => Number(mileage.value))

const isFormValid = computed(() => {
  return make.value.length > 0 &&
    model.value.length > 0 &&
    Number.isInteger(yearNumber.value) &&
    yearNumber.value >= 1900 &&
    yearNumber.value <= 9999 &&
    Number.isFinite(mileageNumber.value) &&
    mileageNumber.value >= 0
})

async function handleCreateCar() {
  if (!isFormValid.value) {
    showToast('Please fill in all required fields correctly', 'warning')
    return
  }

  const payload = {
    make: make.value.trim(),
    model: model.value.trim(),
    year: yearNumber.value,
    mileage: mileageNumber.value
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
.car-form {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border: 1px solid #1e1e1e;
  padding: 25px;
  margin: 0;
  border-radius: 8px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.2);
  width: 100%;
  max-width: 420px;
  text-align: center;
  background: #1e1e1e;

}

.close-button {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 999px;
  background: #1e1e1e;
  color: #333;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
}

.form-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
}

.form-section label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}

.form-section input,
.form-section button {
  width: 320px;
  max-width: 100%;
}

.form-section button {
  cursor: pointer;
}
</style>