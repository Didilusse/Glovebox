<template>

  <NavBar />
  
  <main class="car-detail">
    <header class="detail-header">
      <span>Vehicle dashboard</span>
      <h1>{{ carMake }}</h1>
    </header>

    <section class="vehicle-details" aria-label="Vehicle details">
      <p><strong>Model</strong><span>{{ model || 'N/A' }}</span></p>
      <p><strong>Year</strong><span>{{ year || 'N/A' }}</span></p>
      <p><strong>Mileage</strong><span>{{ mileage || 'N/A' }}</span></p>
      <p><strong>Initial Mileage</strong><span>{{ initial_mileage || 'N/A' }}</span></p>
      <p><strong>VIN</strong><span>{{ vin || 'N/A' }}</span></p>
      <p><strong>License Plate</strong><span>{{ license_plate || 'N/A' }}</span></p>
      <p><strong>Fuel Type</strong><span>{{ fuel_type || 'N/A' }}</span></p>
      <p><strong>Purchase Date</strong><span>{{ purchased_date || 'N/A' }}</span></p>
      <p><strong>Purchase Price</strong><span>{{ purchased_price || 'N/A' }}</span></p>
    </section>

    <section class="car-stats" v-if="stats">
      <h2>Stats</h2>
      <div class="stats-grid">
        <p><strong>Log Count</strong><span>{{ stats.log_count }}</span></p>
        <p><strong>Avg Cost per Service</strong><span>{{ stats.avg_cost_per_service }}</span></p>
        <p><strong>Total Spent</strong><span>{{ stats.total_spent }}</span></p>
        <p><strong>Max Cost</strong><span>{{ stats.max_cost }}</span></p>
        <p><strong>Distance Travelled</strong><span>{{ stats.distance_travelled ?? 'N/A' }}</span></p>
      </div>

      <div v-if="stats.cost_by_done_by" class="cost-breakdown">
        <h3>Cost by Done By</h3>
        <div v-for="(val, key) in stats.cost_by_done_by" :key="key">
          <p><strong>{{ key }}:</strong> Total {{ val.total_spent }} — Count {{ val.count }}</p>
        </div>
      </div>
    </section>
    <section class="car-reminders" v-if="reminders && reminders.length">
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
    </section>
  </main>
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
const purchased_date = computed(() => car.value?.purchased_date ?? '')
const purchased_price = computed(() => car.value?.purchased_price ?? '')

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
    const fetchedReminders = []
    const pageSize = 100

    while (true) {
      const res = await fetch(`${API_BASE}/cars/${route.params.carId}/reminders/?skip=${fetchedReminders.length}&limit=${pageSize}`)
      if (!res.ok) {
        reminders.value = []
        return
      }
      const page = await res.json()
      fetchedReminders.push(...page)
      if (page.length < pageSize) break
    }

    reminders.value = fetchedReminders
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
.car-detail {
  width: min(100% - 40px, 1200px);
  min-height: calc(100vh - 70px);
  margin: 0 auto;
  padding: clamp(40px, 7vw, 72px) 0 80px;
}

.detail-header {
  margin-bottom: 34px;
}

.detail-header > span {
  display: inline-block;
  margin-bottom: 12px;
  padding: 6px 11px;
  border-radius: 999px;
  background: rgba(179, 199, 255, 0.1);
  color: var(--gb-accent);
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
}

.detail-header h1 {
  color: var(--gb-heading);
  font-size: clamp(2rem, 5vw, 3.5rem);
  font-weight: 700;
  line-height: 1.1;
}

.vehicle-details,
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1px;
  overflow: hidden;
  border: 1px solid var(--gb-border);
  border-radius: 16px;
  background: var(--gb-border);
}

.vehicle-details p,
.stats-grid p {
  min-width: 0;
  padding: 18px;
  background: var(--gb-surface);
}

.vehicle-details strong,
.vehicle-details span,
.stats-grid strong,
.stats-grid span {
  display: block;
}

.vehicle-details strong,
.stats-grid strong {
  color: #7f8b9f;
  font-size: 0.7rem;
  font-weight: 500;
  text-transform: uppercase;
}

.vehicle-details span,
.stats-grid span {
  overflow: hidden;
  margin-top: 5px;
  color: var(--gb-heading);
  font-size: 0.95rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.car-stats,
.car-reminders {
  margin-top: 42px;
}

.car-stats h2,
.car-reminders h2 {
  margin-bottom: 18px;
  color: var(--gb-heading);
  font-size: 1.6rem;
  font-weight: 600;
}

.cost-breakdown {
  margin-top: 16px;
  padding: 20px;
  border: 1px solid var(--gb-border);
  border-radius: 16px;
  background: var(--gb-surface);
}

.cost-breakdown h3 {
  margin-bottom: 8px;
  color: var(--gb-heading);
  font-size: 1rem;
  font-weight: 600;
}

.cost-breakdown p {
  color: var(--gb-text-muted);
}

.car-reminders ul {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 14px;
  padding: 0;
  list-style: none;
}

.reminder-item {
  padding: 20px;
  border: 1px solid var(--gb-border);
  border-radius: 16px;
  background: var(--gb-surface);
  color: var(--gb-text-muted);
}

.reminder-item > strong {
  display: block;
  margin-bottom: 10px;
  color: var(--gb-heading);
  font-size: 1.05rem;
  font-weight: 600;
}

.reminder-item button {
  margin-top: 14px;
  padding: 8px 13px;
  border: 1px solid var(--gb-border-strong);
  border-radius: 999px;
  background: transparent;
  color: var(--gb-accent);
  cursor: pointer;
}

.reminder-item button:hover {
  border-color: var(--gb-accent);
}

@media (max-width: 700px) {
  .car-detail {
    width: min(100% - 28px, 1200px);
    padding-top: 36px;
  }

  .vehicle-details,
  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }
}

</style>
