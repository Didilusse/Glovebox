<template>
  <header class="maintenance-header">
    <div class="title-row">
      <div>
        <span class="context">Maintenance record</span>
        <h1>{{ title }}</h1>
        <p>A clear history of the work that keeps this car on the road.</p>
      </div>

      <div v-if="!readOnly" class="actions">
        <button type="button" class="import-button" @click="$emit('import')">
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 3v9m0 0 3-3m-3 3L7 9M4 14v2h12v-2" /></svg>
          Import CARFAX
        </button>
        <button type="button" class="add-button" @click="$emit('add')">
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 4v12M4 10h12" /></svg>
          Log service
        </button>
      </div>
    </div>

    <section class="overview" aria-label="Maintenance overview">
      <div class="attention" :class="{ due: dueReminders.length }">
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 3 2.8 16h14.4L10 3Zm0 4.5v4m0 2.3v.2" /></svg>
        <div>
          <span>{{ dueReminders.length ? 'Needs attention' : 'Service status' }}</span>
          <strong>{{ reminderSummary }}</strong>
        </div>
      </div>

      <dl>
        <div>
          <dt>Current mileage</dt>
          <dd>{{ formatMileage(car?.mileage) }}</dd>
        </div>
        <div>
          <dt>Maintenance spend</dt>
          <dd>{{ formatMoney(totalSpent) }}</dd>
        </div>
        <div>
          <dt>Last recorded service</dt>
          <dd>{{ lastServiceDate }}</dd>
        </div>
      </dl>
    </section>
  </header>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  readOnly: Boolean,
  car: { type: Object, default: null },
  maintenances: { type: Array, default: () => [] },
  reminders: { type: Array, default: () => [] }
})

defineEmits(['add', 'import'])

const title = computed(() => {
  const name = `${props.car?.make ?? ''} ${props.car?.model ?? ''}`.trim()
  return name ? `${name} service history` : 'Service history'
})
const dueReminders = computed(() => props.reminders.filter(reminder => reminder.is_due))
const totalSpent = computed(() => props.maintenances.reduce((total, log) => total + (Number(log.cost) || 0), 0))
const latestLog = computed(() => [...props.maintenances].sort((a, b) => Date.parse(b.date_of_service) - Date.parse(a.date_of_service))[0])
const lastServiceDate = computed(() => latestLog.value ? formatDate(latestLog.value.date_of_service) : 'No history yet')
const reminderSummary = computed(() => {
  if (dueReminders.value.length === 1) return `${dueReminders.value[0].work_done} is due`
  if (dueReminders.value.length > 1) return `${dueReminders.value.length} services are due`
  if (props.reminders.length) return 'No service is currently due'
  return 'No reminders have been set'
})

function formatMoney(value) {
  return new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)
}

function formatMileage(value) {
  return Number.isFinite(value) ? `${new Intl.NumberFormat().format(value)} mi` : 'Not recorded'
}

function formatDate(value) {
  return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${value}T00:00:00Z`))
}
</script>

<style scoped>
.maintenance-header { display: flex; flex-direction: column; gap: 24px; }
.title-row, .actions, .add-button, .import-button, .attention { display: flex; align-items: center; }
.title-row { justify-content: space-between; gap: 24px; }
.context { color: var(--gb-accent); font-size: .72rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; }
h1 { margin-top: 4px; color: var(--gb-heading); font-size: clamp(1.5rem, 3vw, 1.75rem); font-weight: 720; letter-spacing: -.025em; line-height: 1.15; }
.title-row p { margin-top: 5px; color: var(--gb-text-muted); font-size: .9rem; }
.actions { gap: 8px; }
.add-button, .import-button { gap: 7px; padding: 10px 14px; border-radius: 9px; font-weight: 700; cursor: pointer; transition: background 150ms, border-color 150ms, transform 100ms; }
.add-button { border: 0; background: var(--gb-accent); color: #141820; }
.add-button:hover { background: var(--gb-accent-hover); }
.import-button { border: 1px solid var(--gb-border-strong); background: transparent; color: var(--gb-heading); }
.import-button:hover { border-color: var(--gb-accent); background: rgba(179, 199, 255, .05); }
.add-button:active, .import-button:active { transform: translateY(1px); }
.add-button:focus-visible, .import-button:focus-visible { outline: 3px solid rgba(179, 199, 255, .2); outline-offset: 2px; }
button svg { width: 17px; height: 17px; fill: none; stroke: currentColor; stroke-linecap: round; stroke-linejoin: round; stroke-width: 1.7; }

.overview { display: grid; grid-template-columns: minmax(270px, 1.05fr) minmax(480px, 1.95fr); border: 1px solid rgba(179, 199, 255, .1); border-radius: 12px; background: #1c2128; }
.attention { gap: 12px; padding: 18px 20px; border-right: 1px solid rgba(179, 199, 255, .1); }
.attention > svg { width: 20px; height: 20px; fill: none; stroke: #8bd2ac; stroke-linecap: round; stroke-linejoin: round; stroke-width: 1.6; }
.attention.due > svg { stroke: #e3c27f; }
.attention div { display: flex; min-width: 0; flex-direction: column; }
.attention span, dt { color: var(--gb-text-muted); font-size: .72rem; }
.attention strong { overflow: hidden; color: var(--gb-heading); font-size: .86rem; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
dl { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); }
dl div { display: flex; flex-direction: column; justify-content: center; padding: 15px 18px; }
dl div + div { border-left: 1px solid rgba(179, 199, 255, .1); }
dd { margin-top: 2px; color: var(--gb-heading); font-size: .96rem; font-weight: 650; }

@media (max-width: 880px) {
  .overview { grid-template-columns: 1fr; }
  .attention { border-right: 0; border-bottom: 1px solid rgba(179, 199, 255, .1); }
}

@media (max-width: 650px) {
  .title-row { align-items: flex-start; flex-direction: column; }
  .actions { width: 100%; }
  .actions button { flex: 1; justify-content: center; }
  dl { grid-template-columns: 1fr 1fr; }
  dl div + div { border-left: 0; }
  dl div:nth-child(2) { border-left: 1px solid rgba(179, 199, 255, .1); }
  dl div:last-child { grid-column: 1 / -1; border-top: 1px solid rgba(179, 199, 255, .1); }
}
</style>
