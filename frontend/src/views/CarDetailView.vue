<template>

  <NavBar />
  
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

    <div class="car-stats" v-if="stats">
      <h2>Stats</h2>
      <p><strong>Log Count:</strong> {{ stats.log_count }}</p>
      <p><strong>Avg Cost per Service:</strong> {{ stats.avg_cost_per_service }}</p>
      <p><strong>Total Spent:</strong> {{ stats.total_spent }}</p>
      <p><strong>Max Cost:</strong> {{ stats.max_cost }}</p>
      <p><strong>Distance Travelled:</strong> {{ stats.distance_travelled ?? 'N/A' }}</p>

      <div v-if="stats.cost_by_done_by">
        <h3>Cost by Done By</h3>
        <div v-for="(val, key) in stats.cost_by_done_by" :key="key">
          <p><strong>{{ key }}:</strong> Total {{ val.total_spent }} — Count {{ val.count }}</p>
        </div>
      </div>
    </div>
    <div class="car-reminders" v-if="reminders && reminders.length">
      <h2>Reminders</h2>
      <ul>
        <li v-for="r in reminders" :key="r.log_id" class="reminder-item">
          <strong>{{ r.work_done }}</strong>
          <div>Date: {{ r.date_of_service }}</div>
          <div>Reminder date: {{ r.reminder_date ?? 'N/A' }}</div>
          <div>Reminder mileage: {{ r.reminder_mileage ?? 'N/A' }}</div>
          <div>Due: {{ r.is_due ? 'Yes' : 'No' }} {{ r.due_reason ? `(${r.due_reason})` : '' }}</div>
          <div>
            <button @click="handleEditReminder(r)">Edit Reminder</button>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import Toast, { showToast } from '../components/Toast.vue'
import NavBar from '../components/NavBar.vue'
const route = useRoute()
const car = ref(null)
const stats = ref(null)
const envApiBase = import.meta.env.VITE_API_BASE_URL?.trim()
const API_BASE = envApiBase || `${window.location.protocol}//${window.location.hostname}:8000`
const reminders = ref([])

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
  handleFetchStats()
  handleFetchReminders()
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

async function handleFetchReminders() {
  try {
    const res = await fetch(`${API_BASE}/cars/${route.params.carId}/reminders/`)
    if (!res.ok) {
      reminders.value = []
      return
    }
    const data = await res.json()
    reminders.value = Array.isArray(data) ? data : []
  } catch (err) {
    reminders.value = []
  }
}

async function handleEditReminder(reminder) {
  try {
    const months = window.prompt('Enter interval months (leave blank to skip)', reminder.interval_months ?? '')
    const miles = window.prompt('Enter interval miles (leave blank to skip)', reminder.interval_mileage ?? '')

    const body = {}
    if (months !== null && months !== '') body.interval_months = Number(months)
    if (miles !== null && miles !== '') body.interval_miles = Number(miles)

    if (!Object.keys(body).length) return

    const response = await fetch(`${API_BASE}/cars/${route.params.carId}/logs/${reminder.log_id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })

    if (!response.ok) {
      showToast('Failed to update reminder', 'error')
      return
    }

    showToast('Reminder updated', 'success')
    await handleFetchReminders()
  } catch (err) {
    showToast('Failed to update reminder', 'error')
  }
}

async function handleFetchStats() {
  const response = await fetch(`${API_BASE}/cars/${route.params.carId}/stats/`)
  if (!response.ok) {
    showToast('Failed to fetch car stats', 'error')
    throw new Error('Failed to fetch car stats')
  }
  const data = await response.json()
  stats.value = data

  showToast('Car stats fetched successfully', 'success')
}
function handleBack() {
  window.history.back()
}

</script>

<style scoped>

</style>