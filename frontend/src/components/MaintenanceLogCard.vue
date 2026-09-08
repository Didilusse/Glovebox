<template>
  <article class="service-record">
    <time class="date-block" :datetime="log.date_of_service">
      <span>{{ dateParts.month }}</span>
      <strong>{{ dateParts.day }}</strong>
      <small>{{ dateParts.year }}</small>
    </time>

    <div class="record-body">
      <div class="record-heading">
        <div class="identity">
          <span class="category">{{ categoryLabel }}</span>
          <h3>{{ log.work_done || 'Maintenance' }}</h3>
          <p>{{ providerLine }}</p>
        </div>
        <div class="cost">
          <span>Service cost</span>
          <strong>{{ formatMoney(log.cost) }}</strong>
        </div>
      </div>

      <div class="service-meta">
        <span>
          <svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="6.5" /><path d="M10 10 13.5 7M5.5 14.5h9" /></svg>
          {{ formatMileage(log.mileage) }}
        </span>
        <span>
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d="m12.7 5.5 1.8-1.8a3.6 3.6 0 0 1-4.7 4.7l-5.4 5.4a1.3 1.3 0 0 0 1.8 1.8l5.4-5.4a3.6 3.6 0 0 0 4.7-4.7l-1.8 1.8-1.8-1.8Z" /></svg>
          {{ log.done_by === 'self' ? 'DIY service' : 'Shop service' }}
        </span>
        <span v-if="log.source" class="source">Imported from {{ log.source.toUpperCase() }}</span>
      </div>

      <div v-if="log.reminder_date || log.reminder_mileage" class="reminder">
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 3.5a4 4 0 0 0-4 4v2.3L4.5 13h11L14 9.8V7.5a4 4 0 0 0-4-4ZM8.5 15.5h3" /></svg>
        <span>Next service</span>
        <strong>{{ reminderText }}</strong>
      </div>

      <p v-if="log.notes" class="notes">{{ log.notes }}</p>
    </div>

    <div v-if="!readOnly" class="record-actions">
      <button type="button" class="edit" aria-label="Edit service record" title="Edit service record" @click="$emit('edit', log)">
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="m12 4 4 4-8 8H4v-4l8-8Zm-2 2 4 4" /></svg>
      </button>
      <button type="button" class="delete" aria-label="Delete service record" title="Delete service record" @click="$emit('delete', log._id)">
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 6h12M8 3h4l1 3H7l1-3Zm-2 3 1 11h6l1-11M9 9v5m2-5v5" /></svg>
      </button>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ log: { type: Object, required: true }, readOnly: Boolean })
defineEmits(['delete', 'edit'])

const parsedDate = computed(() => props.log.date_of_service ? new Date(`${props.log.date_of_service}T00:00:00Z`) : null)
const dateParts = computed(() => {
  if (!parsedDate.value) return { month: 'Date', day: '--', year: 'unknown' }
  return {
    month: new Intl.DateTimeFormat(undefined, { month: 'short', timeZone: 'UTC' }).format(parsedDate.value),
    day: new Intl.DateTimeFormat(undefined, { day: '2-digit', timeZone: 'UTC' }).format(parsedDate.value),
    year: new Intl.DateTimeFormat(undefined, { year: 'numeric', timeZone: 'UTC' }).format(parsedDate.value)
  }
})
const categoryLabel = computed(() => titleCase(props.log.category || 'other'))
const providerLine = computed(() => props.log.service_provider || (props.log.done_by === 'self' ? 'Performed by owner' : 'Provider not recorded'))
const reminderText = computed(() => {
  const parts = []
  if (props.log.reminder_date) parts.push(formatDate(props.log.reminder_date))
  if (props.log.reminder_mileage) parts.push(`${new Intl.NumberFormat().format(props.log.reminder_mileage)} mi`)
  return parts.join(' or ')
})

function formatMoney(value) {
  return Number.isFinite(value) ? new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value) : 'Not recorded'
}
function formatMileage(value) { return Number.isFinite(value) ? `${new Intl.NumberFormat().format(value)} mi` : 'Mileage unknown' }
function formatDate(value) { return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${value}T00:00:00Z`)) }
function titleCase(value) { return value.charAt(0).toUpperCase() + value.slice(1) }
</script>

<style scoped>
.service-record { position: relative; display: grid; grid-template-columns: 64px minmax(0, 1fr) auto; gap: 18px; padding: 18px; border: 1px solid rgba(179, 199, 255, .1); border-radius: 10px; background: #242a32; transition: border-color 150ms, background 150ms; }
.service-record:hover { border-color: rgba(179, 199, 255, .22); background: #272e37; }
.date-block { display: flex; align-items: center; align-self: start; flex-direction: column; padding: 8px 6px; border-radius: 8px; background: #1a1f25; font-variant-numeric: tabular-nums; text-align: center; }
.date-block span { color: var(--gb-accent); font-size: .68rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
.date-block strong { color: var(--gb-heading); font-size: 1.35rem; font-weight: 680; line-height: 1.15; }
.date-block small { color: var(--gb-text-muted); font-size: .68rem; }
.record-body { min-width: 0; }
.record-heading, .service-meta, .service-meta span, .reminder, .record-actions { display: flex; align-items: center; }
.record-heading { align-items: flex-start; justify-content: space-between; gap: 16px; }
.identity { min-width: 0; }
.category { color: var(--gb-accent); font-size: .68rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
h3 { margin-top: 3px; color: var(--gb-heading); font-size: 1.02rem; font-weight: 680; letter-spacing: -.015em; line-height: 1.3; }
.identity p { margin-top: 3px; color: var(--gb-text-muted); font-size: .76rem; }
.cost { flex: 0 0 auto; text-align: right; }
.cost span { display: block; color: var(--gb-text-muted); font-size: .65rem; }
.cost strong { color: var(--gb-accent); font-size: .95rem; font-weight: 700; }
.service-meta { flex-wrap: wrap; gap: 8px 16px; margin-top: 12px; }
.service-meta span { gap: 5px; color: #aeb7c5; font-size: .73rem; }
.service-meta svg, .reminder svg { width: 14px; height: 14px; fill: none; stroke: currentColor; stroke-linecap: round; stroke-linejoin: round; stroke-width: 1.5; }
.service-meta .source { color: #8893a2; }
.reminder { gap: 7px; margin-top: 12px; padding: 8px 10px; border-radius: 7px; background: rgba(179, 199, 255, .055); color: var(--gb-text-muted); font-size: .73rem; }
.reminder svg { color: var(--gb-accent); }
.reminder strong { margin-left: auto; color: var(--gb-heading); font-size: .73rem; font-weight: 600; }
.notes { margin-top: 11px; color: var(--gb-text-muted); font-size: .8rem; line-height: 1.5; }
.record-actions { align-self: start; gap: 3px; }
.record-actions button { display: grid; width: 30px; height: 30px; padding: 0; place-items: center; border: 0; border-radius: 6px; background: transparent; color: var(--gb-text-muted); cursor: pointer; }
.record-actions button:hover { background: #343c47; color: var(--gb-heading); }
.record-actions button:active { transform: translateY(1px); }
.record-actions button:focus-visible { outline: 2px solid var(--gb-accent); outline-offset: 1px; }
.record-actions .delete:hover { color: var(--gb-danger); }
.record-actions svg { width: 15px; height: 15px; fill: none; stroke: currentColor; stroke-linecap: round; stroke-linejoin: round; stroke-width: 1.5; }

@media (max-width: 650px) {
  .service-record { grid-template-columns: 54px minmax(0, 1fr); gap: 14px; padding: 14px; }
  .record-actions { position: absolute; right: 10px; bottom: 10px; }
  .record-heading { flex-direction: column; gap: 8px; }
  .cost { text-align: left; }
  .cost span { display: none; }
  .reminder { align-items: flex-start; flex-wrap: wrap; padding-right: 66px; }
  .reminder strong { width: 100%; margin-left: 21px; }
  .notes { padding-right: 66px; }
}
</style>
