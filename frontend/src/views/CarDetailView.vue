<template>

  <NavBar />
  
  <main class="car-detail">
    <header class="detail-header">
      <span>Vehicle dashboard</span>
      <h1>{{ carMake }}</h1>
      <p v-if="car?.access && !isOwner" class="shared-badge">Shared by {{ car.access.owner_username }}</p>
      <div class="vehicle-actions">
        <button v-if="canEdit('vehicle')" type="button" @click="editOpen = true">Edit vehicle</button>
        <button v-if="isOwner" type="button" @click="sharingOpen = true">Share / manage sharing</button>
      </div>
    </header>
    <p v-if="loadFailed" role="alert">Unable to load this vehicle. It may no longer be shared with you.</p>

    <div v-if="car" class="dashboard-tabs" role="tablist" aria-label="Dashboard sections">
      <button id="overview-tab" role="tab" :aria-selected="activeTab === 'overview'" aria-controls="overview-panel" :tabindex="activeTab === 'overview' ? 0 : -1" @click="activeTab = 'overview'" @keydown.right.prevent="selectTab('reminders')" @keydown.left.prevent="selectTab('reminders')">Overview</button>
      <button v-if="canView('maintenance')" id="reminders-tab" role="tab" :aria-selected="activeTab === 'reminders'" aria-controls="reminders-panel" :tabindex="activeTab === 'reminders' ? 0 : -1" @click="activeTab = 'reminders'" @keydown.right.prevent="selectTab('overview')" @keydown.left.prevent="selectTab('overview')">Reminders <span v-if="dueCount">({{ dueCount }} due)</span></button>
    </div>
    <div v-show="activeTab === 'overview'" id="overview-panel" role="tabpanel" aria-labelledby="overview-tab" tabindex="0">
    <section v-if="car" class="vehicle-details" aria-label="Vehicle details">
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

    <section class="car-stats" v-if="canView('maintenance') && stats">
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
    </div>
    <section id="reminders-panel" role="tabpanel" aria-labelledby="reminders-tab" tabindex="0" class="car-reminders" v-if="canView('maintenance')" v-show="activeTab === 'reminders'">
      <h2>Reminders</h2>
      <p v-if="remindersLoading" role="status">Loading reminders...</p>
      <p v-if="remindersError" role="alert">Unable to load reminders. <button @click="handleFetchReminders" :disabled="remindersLoading">Retry</button></p>
      <p v-else-if="!remindersLoading && !reminders.length">No reminders configured. Schedule the next service when adding a maintenance log.</p>
      <ul>
        <li v-for="r in reminders" :key="r.log_id">
          <ReminderCard :reminder="r" :car-id="carId" :editable="canEdit('maintenance')" @updated="handleFetchReminders" />
        </li>
      </ul>
    </section>
  </main>
  <VehicleSharing v-if="sharingOpen && isOwner" :car="car" @close="sharingOpen = false" />
  <VehicleEdit v-if="editOpen && canEdit('vehicle')" :car="car" @close="editOpen = false" @updated="handleVehicleUpdated" />
</template>

<script setup>
import { API_BASE, useApiClient } from '../utils/auth'
import { provideVehicleAccess } from '../utils/vehicleAccess'
import VehicleSharing from '../components/VehicleSharing.vue'
import VehicleEdit from '../components/VehicleEdit.vue'
import ReminderCard from '../components/ReminderCard.vue'
import { computed, onMounted, onBeforeUnmount, ref, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { showToast } from '../components/Toast.vue'
import NavBar from '../components/NavBar.vue'
const route = useRoute()
const carId = route.params.carId
const car = ref(null)
const { canView, canEdit, isOwner } = provideVehicleAccess(car)
const sharingOpen = ref(false)
const editOpen = ref(false)
const loadFailed = ref(false)
const stats = ref(null)
const fetch = useApiClient()
const reminders = ref([])
const remindersLoading = ref(false)
const remindersError = ref(false)
const activeTab = ref(route.query.tab === 'reminders' ? 'reminders' : 'overview')
let reminderTimer
onBeforeUnmount(() => clearInterval(reminderTimer))
watch(() => route.query.tab, tab => { activeTab.value = tab === 'reminders' ? 'reminders' : 'overview' })
const dueCount = computed(() => reminders.value.filter(r => r.is_due || r.is_overdue).length)
async function selectTab(tab) {
  if (tab === 'reminders' && !canView('maintenance')) return
  activeTab.value = tab
  await nextTick(); document.getElementById(`${tab}-tab`)?.focus()
}

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

onMounted(async () => {
  reminderTimer = setInterval(() => { if (car.value && !remindersLoading.value) handleFetchReminders() }, 60000)
  try {
    await handleFetchCar()
    if (!canView('maintenance')) activeTab.value = 'overview'
    if (canView('maintenance')) await Promise.all([
      handleFetchStats().catch(() => showToast('Unable to load statistics', 'error')),
      handleFetchReminders()
    ])
  } catch { loadFailed.value = true }
})

async function handleVehicleUpdated(updated) {
  car.value = updated
  editOpen.value = false
  stats.value = null
  reminders.value = []
  if (canView('maintenance')) await Promise.all([
    handleFetchStats().catch(() => showToast('Unable to load statistics', 'error')),
    handleFetchReminders()
  ])
}

async function handleFetchCar() {
  car.value = null
  const response = await fetch(`${API_BASE}/cars/${carId}`)
  if (!response.ok) {
    showToast('Failed to fetch car', 'error')
    throw new Error('Failed to fetch car')
  }
  const data = await response.json()
  car.value = data
  showToast('Car fetched successfully', 'success')
}

async function handleFetchReminders() {
  if (!canView('maintenance')) return
  remindersLoading.value = true
  remindersError.value = false
  try {
    const fetchedReminders = []
    const pageSize = 100

    while (true) {
      if (!canView('maintenance')) return
      const res = await fetch(`${API_BASE}/cars/${carId}/reminders/?skip=${fetchedReminders.length}&limit=${pageSize}`)
      if (!res.ok) {
        throw new Error('Unable to load reminders')
      }
      const page = await res.json()
      fetchedReminders.push(...page)
      if (page.length < pageSize) break
    }

    reminders.value = fetchedReminders.filter(r => r.interval_miles != null || r.interval_months != null || r.reminder_date != null || r.reminder_mileage != null)
  } catch (err) {
    if (err.name !== 'AbortError') remindersError.value = true
  } finally { remindersLoading.value = false }
}

async function handleFetchStats() {
  if (!canView('maintenance')) return
  const response = await fetch(`${API_BASE}/cars/${carId}/stats/`)
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
.dashboard-tabs { display: flex; gap: 12px; margin-bottom: 24px; }
.dashboard-tabs button { padding: 12px 18px; background: var(--gb-surface); color: var(--gb-heading); border: 1px solid var(--gb-border); border-radius: 8px; cursor: pointer; }
.dashboard-tabs [aria-selected=true] { border-color: var(--gb-accent); color: var(--gb-accent); }
.shared-badge { display: inline-block; margin-top: 14px; padding: 6px 11px; border: 1px solid var(--gb-border-strong); border-radius: 999px; color: var(--gb-accent); }
.vehicle-actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 20px; }
.vehicle-actions button { padding: 10px 16px; border: 1px solid var(--gb-border-strong); border-radius: 9px; background: var(--gb-surface); color: var(--gb-accent); cursor: pointer; }
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
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 250px), 1fr));
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
