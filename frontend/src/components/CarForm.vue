<template>
  <div class="car-form">
    <button type="button" class="close-button" aria-label="Close form" @click="emit('close')">
      &times;
    </button>

    <h2>Add a Car</h2>

    <form class="form-section" @submit.prevent="handleCreateCar">
      <div class="form-layout">
        <div class="form-left">
          <div class="form-group">
            <label>Year</label>
            <input v-model="year" min="1900" max="9999" placeholder="Enter Car Year" />
          </div>

          <div class="form-group">
            <label>Make</label>
            <input v-model.trim="make" placeholder="Enter Car Make" />
          </div>

          <div class="form-group">
            <label>Model</label>
            <input v-model.trim="model" placeholder="Enter Car Model" />
          </div>

          <div class="form-group">
            <label>License Plate</label>
            <input v-model="licensePlate" placeholder="e.g. ABC-1234" />
          </div>
        </div>

        <div class="form-right">
          <div class="form-group">
            <label>Fuel Type</label>
            <select v-model="fuelType">
              <option value="Gasoline">Gasoline</option>
              <option value="Diesel">Diesel</option>
              <option value="Electric">Electric</option>
            </select>
          </div>

          <button 
            type="button" 
            class="advanced-toggle" 
            @click="showAdvanced = !showAdvanced"
          >
            {{ showAdvanced ? '▼ Hide Advanced Options' : '▶ Show Advanced Options' }}
          </button>

          <div v-show="showAdvanced" class="advanced-options">
            <div class="form-group">
              <label>Purchased Date</label>
              <input v-model="purchasedDate" type="date" />
            </div>

            <div class="form-group">
              <label>Purchased Price</label>
              <input v-model="purchasedPrice" type="number" placeholder="e.g. 25000" />
            </div>

            <div class="form-group">
              <label>VIN</label>
              <input v-model="vin" placeholder="e.g. 1HGBH41JXMN109186" />
            </div>

            <div class="form-group">
              <label>Mileage</label>
              <input v-model="mileage" min="0" placeholder="50000" />
            </div>
          </div>
        </div>
      </div>

      <div class="form-actions">
        <button type="button" class="cancel-button" @click="emit('close')">Cancel</button>
        <button type="submit" class="submit-button">Create Car</button>
      </div>
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

const showAdvanced = ref(false)

const vin = ref('')
const licensePlate = ref('')
const fuelType = ref('Gasoline')
const purchasedDate = ref('')
const purchasedPrice = ref('')

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
    mileage: mileageNumber.value,
    vin: vin.value.trim(),
    licensePlate: licensePlate.value.trim(),
    fuelType: fuelType.value.trim(),
    purchasedDate: purchasedDate.value.trim(),
    purchasedPrice: purchasedPrice.value.trim()
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
  vin.value = ''
  licensePlate.value = ''
  fuelType.value = ''
  purchasedDate.value = ''
  purchasedPrice.value = ''
  showToast('Car created successfully', 'success')
}
</script>

<style scoped>
.car-form {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 20px;
  border: 1px solid #444;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.3);
  width: 100%;
  max-width: 900px;
  background: #2a2a2a;
}

.car-form h2 {
  margin: 0;
  margin-top: -10px;
  text-align: left;
  font-size: 1.5rem;
  color: #fff;
}

.close-button {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 4px;
  background: transparent;
  color: #999;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-button:hover {
  color: #fff;
  background-color: rgba(255, 255, 255, 0.1);
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
}

.form-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
  width: 100%;
}

.form-left {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-right {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 0.95rem;
  font-weight: 500;
  color: #fff;
}

.form-group input,
.form-group select {
  padding: 10px 12px;
  border: 1px solid #555;
  border-radius: 4px;
  background-color: #1e1e1e;
  color: #fff;
  font-size: 0.95rem;
}

.form-group input::placeholder {
  color: #666;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1);
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 10px;
  padding-top: 20px;
  border-top: 1px solid #444;
}

.submit-button,
.cancel-button {
  padding: 10px 24px;
  border: none;
  border-radius: 4px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.submit-button {
  background-color: #007bff;
  color: white;
}

.submit-button:hover {
  background-color: #0056b3;
}

.cancel-button {
  background-color: #6c757d;
  color: white;
}

.cancel-button:hover {
  background-color: #5a6268;
}

.advanced-toggle {
  padding: 10px 12px;
  border: 1px solid #007bff;
  border-radius: 4px;
  background-color: transparent;
  color: #007bff;
  font-weight: 500;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.advanced-toggle:hover {
  background-color: #007bff;
  color: white;
}

.advanced-options {
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding: 15px;
  border: 1px solid #555;
  border-radius: 4px;
  background-color: rgba(0, 123, 255, 0.05);
}
</style>