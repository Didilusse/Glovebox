<template>

  <NavBar />
  
  <main class="car-detail">
    <header class="detail-header">
      <div>
        <span class="eyebrow">Vehicle dashboard</span>
        <h1>{{ carMake }}</h1>
        <div v-if="car" class="vehicle-context">
          <span v-if="year">{{ year }}</span>
           <span v-if="fuel_type">{{ formatFuel(fuel_type) }}</span>
          <span v-if="mileage !== ''">{{ formatNumber(mileage) }} mi</span>
        </div>
        <p v-if="car?.access && !isOwner" class="shared-badge">Shared by {{ car.access.owner_username }}</p>
      </div>
      <div class="vehicle-actions">
        <button v-if="canEdit('vehicle')" type="button" @click="editOpen = true">Edit vehicle</button>
        <button v-if="isOwner" class="secondary-action" type="button" @click="sharingOpen = true">Share / manage sharing</button>
      </div>
    </header>
    <p v-if="loadFailed" role="alert">Unable to load this vehicle. It may no longer be shared with you.</p>

    <div v-if="car" class="dashboard-tabs" role="tablist" aria-label="Dashboard sections">
      <button id="overview-tab" role="tab" :aria-selected="activeTab === 'overview'" aria-controls="overview-panel" :tabindex="activeTab === 'overview' ? 0 : -1" @click="activateTab('overview')" @keydown.right.prevent="selectTab('reminders')" @keydown.left.prevent="selectTab('reminders')">Overview</button>
      <button v-if="canView('maintenance')" id="reminders-tab" role="tab" :aria-selected="activeTab === 'reminders'" aria-controls="reminders-panel" :tabindex="activeTab === 'reminders' ? 0 : -1" @click="activateTab('reminders')" @keydown.right.prevent="selectTab('overview')" @keydown.left.prevent="selectTab('overview')">Reminders <span v-if="dueCount" class="tab-count">{{ dueCount }}<span class="visually-hidden"> due</span></span></button>
    </div>
    <div v-show="activeTab === 'overview'" id="overview-panel" role="tabpanel" aria-labelledby="overview-tab" tabindex="0">
    <section v-if="car" class="dashboard-summary" aria-labelledby="status-heading">
      <div class="status-card" :class="{ 'needs-attention': dueCount }">
        <div class="status-icon" aria-hidden="true">
          <svg v-if="dueCount" viewBox="0 0 24 24"><path d="M12 4 3 20h18L12 4Zm0 5v5m0 3v.1" /></svg>
          <svg v-else viewBox="0 0 24 24"><path d="m6 12 4 4 8-8" /></svg>
        </div>
        <div>
          <p class="section-kicker">Vehicle status</p>
          <h2 id="status-heading">{{ dueCount ? `${dueCount} ${dueCount === 1 ? 'service needs' : 'services need'} attention` : 'Everything looks on track' }}</h2>
          <p>{{ dueCount ? 'Review the due items and plan your next service.' : remindersLoading ? 'Checking your maintenance schedule...' : 'No maintenance reminders are currently due.' }}</p>
        </div>
        <button v-if="canView('maintenance')" type="button" @click="activateTab('reminders')">{{ dueCount ? 'Review reminders' : 'View schedule' }}</button>
      </div>

      <dl class="snapshot-grid">
        <div><dt>Current mileage</dt><dd>{{ mileage === '' ? 'N/A' : formatNumber(mileage) }}</dd><span v-if="mileage !== ''">miles</span></div>
        <div v-if="canView('maintenance')"><dt>Service records</dt><dd>{{ stats ? formatNumber(stats.log_count) : '...' }}</dd><span>logged</span></div>
        <div v-if="canView('maintenance')"><dt>Total spent</dt><dd>{{ stats ? formatCurrency(stats.total_spent) : '...' }}</dd><span>on maintenance</span></div>
      </dl>
    </section>

    <section class="dashboard-section car-stats" v-if="canView('maintenance') && stats" aria-labelledby="stats-heading">
      <div class="section-heading">
        <div>
          <p class="section-kicker">Maintenance</p>
          <h2 id="stats-heading">Service history</h2>
        </div>
        <p>A clear view of your maintenance activity and spend.</p>
      </div>
      <div class="stats-grid">
        <p><strong>Service records</strong><span>{{ formatNumber(stats.log_count) }}</span></p>
        <p><strong>Total spent</strong><span>{{ formatCurrency(stats.total_spent) }}</span></p>
        <p><strong>Average service</strong><span>{{ formatCurrency(stats.avg_cost_per_service) }}</span></p>
        <p><strong>Highest service</strong><span>{{ formatCurrency(stats.max_cost) }}</span></p>
        <p><strong>Distance travelled</strong><span>{{ stats.distance_travelled == null ? 'N/A' : `${formatNumber(stats.distance_travelled)} mi` }}</span></p>
      </div>

      <div v-if="stats.cost_by_done_by" class="cost-breakdown">
        <div class="breakdown-heading">
          <h3>Spend by provider</h3>
          <p>How maintenance costs are split.</p>
        </div>
        <dl>
          <div v-for="(val, key) in stats.cost_by_done_by" :key="key">
            <dt>{{ key }} <span>{{ val.count }} {{ val.count === 1 ? 'service' : 'services' }}</span></dt>
            <dd>{{ formatCurrency(val.total_spent) }}</dd>
          </div>
        </dl>
      </div>
    </section>

    <details v-if="car" class="dashboard-section vehicle-profile">
      <summary>
        <span>
          <span class="section-kicker">Vehicle profile</span>
          <strong id="vehicle-details-heading">Registration and purchase details</strong>
        </span>
        <span class="summary-action">View details <span aria-hidden="true">+</span></span>
      </summary>
      <dl class="vehicle-details" aria-labelledby="vehicle-details-heading">
        <div><dt>Model</dt><dd>{{ model || 'N/A' }}</dd></div>
        <div><dt>Year</dt><dd>{{ year || 'N/A' }}</dd></div>
        <div><dt>Current mileage</dt><dd>{{ mileage === '' ? 'N/A' : `${formatNumber(mileage)} mi` }}</dd></div>
        <div><dt>Starting mileage</dt><dd>{{ initial_mileage === '' ? 'N/A' : `${formatNumber(initial_mileage)} mi` }}</dd></div>
        <div><dt>License plate</dt><dd>{{ license_plate || 'N/A' }}</dd></div>
         <div><dt>Fuel type</dt><dd>{{ fuel_type ? formatFuel(fuel_type) : 'N/A' }}</dd></div>
        <div class="detail-wide"><dt>VIN</dt><dd>{{ vin || 'N/A' }}</dd></div>
        <div><dt>Purchased</dt><dd>{{ purchased_date || 'N/A' }}</dd></div>
        <div><dt>Purchase price</dt><dd>{{ formatCurrency(purchased_price) }}</dd></div>
      </dl>
    </details>
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
import { useRoute, useRouter } from 'vue-router'
import { showToast } from '../components/Toast.vue'
import NavBar from '../components/NavBar.vue'
const route = useRoute()
const router = useRouter()
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
  await activateTab(tab)
  await nextTick(); document.getElementById(`${tab}-tab`)?.focus()
}

async function activateTab(tab) {
  if (tab === 'reminders' && !canView('maintenance')) return
  activeTab.value = tab
  const query = { ...route.query }
  if (tab === 'reminders') query.tab = 'reminders'
  else delete query.tab
  await router.replace({ query })
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

function formatNumber(value) {
  if (value === null || value === undefined || value === '') return 'N/A'
  const number = Number(value)
  return Number.isFinite(number) ? new Intl.NumberFormat('en-US').format(number) : 'N/A'
}

function formatFuel(fuelType) {
  return fuelType.charAt(0).toUpperCase() + fuelType.slice(1)
}

function formatCurrency(value) {
  if (value === null || value === undefined || value === '') return 'N/A'
  const number = Number(value)
  return Number.isFinite(number) ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(number) : 'N/A'
}

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
.dashboard-tabs { display: flex; gap: 26px; margin: 26px 0 28px; border-bottom: 1px solid var(--gb-border); }
.dashboard-tabs button { position: relative; padding: 0 0 13px; border: 0; background: transparent; color: var(--gb-text-muted); cursor: pointer; font-size: 0.88rem; }
.dashboard-tabs [aria-selected=true] { color: var(--gb-heading); font-weight: 600; }
.dashboard-tabs [aria-selected=true]::after { position: absolute; right: 0; bottom: -1px; left: 0; height: 2px; background: var(--gb-accent); content: ''; }
.tab-count { display: inline-grid; min-width: 19px; height: 19px; margin-left: 5px; place-items: center; border-radius: 999px; background: rgba(239, 139, 128, .14); color: var(--gb-danger); font-size: 0.67rem; font-weight: 700; }
.visually-hidden { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); clip-path: inset(50%); white-space: nowrap; }
.shared-badge { display: inline-flex; margin-top: 14px; padding: 4px 9px; border: 1px solid var(--gb-border); border-radius: 999px; color: var(--gb-text-muted); font-size: 0.78rem; }
.vehicle-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 10px; }
.vehicle-actions button { min-height: 40px; padding: 9px 14px; border: 1px solid var(--gb-accent); border-radius: 8px; background: var(--gb-accent); color: #171b24; font-size: 0.82rem; font-weight: 700; cursor: pointer; }
.vehicle-actions .secondary-action { border-color: var(--gb-border-strong); background: transparent; color: var(--gb-text); }
.vehicle-actions button:hover { background: var(--gb-accent-hover); }
.vehicle-actions .secondary-action:hover { border-color: var(--gb-text-muted); background: var(--gb-surface); }
.car-detail {
  width: min(100% - 40px, 1200px);
  min-height: calc(100vh - 70px);
  margin: 0 auto;
  padding: clamp(40px, 7vw, 72px) 0 80px;
}

.detail-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 28px;
  padding-bottom: 32px;
  border-bottom: 1px solid var(--gb-border);
}

.eyebrow,
.section-kicker {
  display: inline-block;
  margin-bottom: 10px;
  color: var(--gb-accent);
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.detail-header h1 {
  color: var(--gb-heading);
  font-size: clamp(2rem, 5vw, 3.5rem);
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.04em;
}

.vehicle-context { display: flex; flex-wrap: wrap; gap: 0; margin-top: 14px; color: var(--gb-text-muted); font-size: 0.92rem; }
.vehicle-context span + span::before { margin: 0 10px; color: var(--gb-border-strong); content: '/'; }

.dashboard-summary { display: grid; grid-template-columns: minmax(0, 1.7fr) minmax(320px, 1fr); gap: 14px; }
.status-card { display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 16px; min-height: 154px; padding: 24px; border: 1px solid var(--gb-border); border-radius: 14px; background: linear-gradient(135deg, rgba(179, 199, 255, .07), transparent 58%), var(--gb-surface); }
.status-card.needs-attention { background: linear-gradient(135deg, rgba(239, 139, 128, .08), transparent 58%), var(--gb-surface); }
.status-icon { width: 42px; height: 42px; display: grid; place-items: center; border-radius: 12px; background: rgba(179, 199, 255, .12); color: var(--gb-accent); }
.needs-attention .status-icon { background: rgba(239, 139, 128, .12); color: var(--gb-danger); }
.status-icon svg { width: 21px; height: 21px; fill: none; stroke: currentColor; stroke-linecap: round; stroke-linejoin: round; stroke-width: 1.7; }
.status-card .section-kicker { margin-bottom: 2px; }
.status-card h2 { color: var(--gb-heading); font-size: clamp(1.15rem, 2vw, 1.45rem); font-weight: 650; letter-spacing: -0.025em; }
.status-card h2 + p { margin-top: 4px; color: var(--gb-text-muted); font-size: 0.83rem; }
.status-card button { min-height: 38px; padding: 8px 12px; border: 1px solid var(--gb-border-strong); border-radius: 8px; background: transparent; color: var(--gb-heading); font-size: 0.78rem; font-weight: 600; cursor: pointer; }
.status-card button:hover { border-color: var(--gb-accent); color: var(--gb-accent); }

.snapshot-grid { display: grid; grid-template-columns: repeat(3, 1fr); overflow: hidden; border: 1px solid var(--gb-border); border-radius: 14px; background: var(--gb-surface); }
.snapshot-grid > div { display: flex; min-width: 0; padding: 18px 19px; flex-direction: column; justify-content: center; border-right: 1px solid var(--gb-border); }
.snapshot-grid > div:last-child { border-right: 0; }
.snapshot-grid dt { color: #7f8b9f; font-size: 0.65rem; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; }
.snapshot-grid dd { overflow: hidden; margin-top: 2px; color: var(--gb-heading); font-size: 1.12rem; font-weight: 650; text-overflow: ellipsis; white-space: nowrap; }
.snapshot-grid span { color: var(--gb-text-muted); font-size: 0.7rem; }

.dashboard-section { margin-top: 48px; }
.section-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 20px; margin-bottom: 18px; }
.section-heading .section-kicker { margin-bottom: 4px; }
.section-heading h2 { color: var(--gb-heading); font-size: 1.35rem; font-weight: 650; letter-spacing: -0.02em; }
.section-heading > p { max-width: 280px; color: var(--gb-text-muted); font-size: 0.84rem; text-align: right; }

.vehicle-details,
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px 32px;
  padding: 24px;
  border: 1px solid var(--gb-border);
  border-radius: 12px;
  background: var(--gb-surface);
}

.vehicle-details > div,
.stats-grid p {
  min-width: 0;
  padding: 8px 0;
}

.vehicle-details dt,
.vehicle-details dd,
.stats-grid strong,
.stats-grid span {
  display: block;
}

.vehicle-details dt,
.stats-grid strong {
  color: #7f8b9f;
  font-size: 0.7rem;
  font-weight: 500;
  text-transform: uppercase;
}

.vehicle-details dd,
.stats-grid span {
  overflow: hidden;
  margin-top: 5px;
  color: var(--gb-heading);
  font-size: 0.95rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stats-grid { grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 0; padding: 0; overflow: hidden; }
.stats-grid p { min-height: 112px; padding: 22px 20px; border-right: 1px solid var(--gb-border); }
.stats-grid p:last-child { border-right: 0; }
.stats-grid span { font-size: 1.15rem; font-weight: 600; }

.cost-breakdown {
  margin-top: 14px;
  padding: 22px 24px;
  border: 1px solid var(--gb-border);
  border-radius: 12px;
  background: var(--gb-background-deep);
}

.breakdown-heading { display: flex; align-items: baseline; justify-content: space-between; gap: 20px; margin-bottom: 14px; }
.cost-breakdown h3 {
  color: var(--gb-heading);
  font-size: 1rem;
  font-weight: 600;
}
.breakdown-heading p { color: var(--gb-text-muted); font-size: 0.8rem; }
.cost-breakdown dl { display: grid; gap: 10px; }
.cost-breakdown dl > div { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding-top: 10px; border-top: 1px solid var(--gb-border); }
.cost-breakdown dt { color: var(--gb-heading); text-transform: capitalize; }
.cost-breakdown dt span { margin-left: 7px; color: var(--gb-text-muted); font-size: 0.78rem; }
.cost-breakdown dd { color: var(--gb-accent); font-weight: 600; }

.vehicle-profile { overflow: hidden; border: 1px solid var(--gb-border); border-radius: 12px; background: var(--gb-background-deep); }
.vehicle-profile summary { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 19px 22px; cursor: pointer; list-style: none; }
.vehicle-profile summary::-webkit-details-marker { display: none; }
.vehicle-profile summary .section-kicker { display: block; margin-bottom: 1px; }
.vehicle-profile summary strong { display: block; color: var(--gb-heading); font-size: 0.95rem; font-weight: 600; }
.summary-action { color: var(--gb-text-muted); font-size: 0.76rem; }
.summary-action span { display: inline-block; margin-left: 7px; color: var(--gb-accent); font-size: 1rem; transition: transform .18s ease; }
.vehicle-profile[open] .summary-action span { transform: rotate(45deg); }
.vehicle-profile .vehicle-details { border: 0; border-top: 1px solid var(--gb-border); border-radius: 0; }

.car-reminders { margin-top: 8px; }
.car-reminders > h2 { margin-bottom: 5px; color: var(--gb-heading); font-size: 1.4rem; font-weight: 650; letter-spacing: -0.02em; }
.car-reminders > p { color: var(--gb-text-muted); }

.car-reminders ul {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 320px), 1fr));
  gap: 14px;
  margin-top: 20px;
  padding: 0;
  list-style: none;
}

@media (max-width: 700px) {
  .car-detail {
    width: min(100% - 28px, 1200px);
    padding-top: 36px;
  }

  .detail-header,
  .section-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .vehicle-actions { justify-content: flex-start; }
  .section-heading > p { text-align: left; }

  .dashboard-summary { grid-template-columns: 1fr; }
  .status-card { grid-template-columns: auto 1fr; min-height: auto; }
  .status-card button { grid-column: 1 / -1; }
  .vehicle-details {
    grid-template-columns: 1fr 1fr;
  }

  .stats-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .stats-grid p { min-height: 96px; border-bottom: 1px solid var(--gb-border); }
  .stats-grid p:nth-child(2n) { border-right: 0; }
  .stats-grid p:last-child { border-bottom: 0; }
}

@media (max-width: 430px) {
  .snapshot-grid { grid-template-columns: 1fr; }
  .snapshot-grid > div { border-right: 0; border-bottom: 1px solid var(--gb-border); }
  .snapshot-grid > div:last-child { border-bottom: 0; }
  .vehicle-details { grid-template-columns: 1fr; }
  .vehicle-profile summary { align-items: flex-start; }
  .summary-action { font-size: 0; }
  .summary-action span { font-size: 1rem; }
}

</style>
