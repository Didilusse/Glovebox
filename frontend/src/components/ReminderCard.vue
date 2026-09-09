<script setup>
import { ref, nextTick } from 'vue'
import { useApiRequest } from '../utils/auth'
const props = defineProps({ reminder: { type: Object, required: true }, carId: String, editable: Boolean })
const emit = defineEmits(['updated'])
const request = useApiRequest()
const editing = ref(false)
const miles = ref('')
const months = ref('')
const saving = ref(false)
const error = ref('')
const firstInput = ref(null)
const editButton = ref(null)
async function edit() {
  miles.value = props.reminder.interval_miles ?? ''
  months.value = props.reminder.interval_months ?? ''
  error.value = ''; editing.value = true
  await nextTick(); firstInput.value?.focus()
}
async function cancel() { editing.value = false; await nextTick(); editButton.value?.focus() }
async function save() {
  if (!props.editable || saving.value) return
  saving.value = true; error.value = ''
  try {
    await request(`/cars/${props.carId}/logs/${props.reminder.log_id}`, {
      interval_miles: miles.value === '' ? null : Number(miles.value),
      interval_months: months.value === '' ? null : Number(months.value)
    }, 'PATCH')
    await cancel(); emit('updated')
  } catch (e) { if (e.name !== 'AbortError') error.value = 'Unable to save reminder. Please retry.' }
  finally { saving.value = false }
}
</script>

<template>
  <article class="reminder-card" :class="{ overdue: reminder.is_overdue, due: reminder.is_due && !reminder.is_overdue }">
    <header>
      <div>
        <p class="card-kicker">Service reminder</p>
        <h3>{{ reminder.work_done }}</h3>
      </div>
      <strong v-if="reminder.is_due || reminder.is_overdue" class="due-badge">{{ reminder.is_overdue ? 'Overdue' : 'Due' }}</strong>
    </header>
    <p class="last-service">Last service <strong>{{ reminder.date_of_service || 'unknown' }}</strong></p>
    <div class="reminder-measures">
      <section v-if="reminder.interval_miles != null || reminder.reminder_mileage != null">
        <p class="measure-label">Mileage</p>
        <p v-if="reminder.interval_miles != null" class="measure-detail">Every {{ reminder.interval_miles }} mi</p>
        <p class="measure-target">Due at {{ reminder.reminder_mileage ?? 'unknown' }} mi</p>
        <label v-if="reminder.progress_miles != null">Mileage progress <span>{{ Math.round(reminder.progress_miles) }}%</span>
          <progress :value="reminder.progress_miles" max="100" aria-label="Mileage progress" />
        </label>
        <p v-else>Mileage progress unavailable</p>
      </section>
      <section v-if="reminder.interval_months != null || reminder.reminder_date != null">
        <p class="measure-label">Time</p>
        <p v-if="reminder.interval_months != null" class="measure-detail">Every {{ reminder.interval_months }} months</p>
        <p class="measure-target">Due {{ reminder.reminder_date ?? 'unknown' }}</p>
        <label v-if="reminder.progress_time != null">Time progress <span>{{ Math.round(reminder.progress_time) }}%</span>
          <progress :value="reminder.progress_time" max="100" aria-label="Time progress" />
        </label>
        <p v-else>Time progress unavailable</p>
      </section>
    </div>
    <p v-if="reminder.due_reason" class="due-reason">{{ reminder.due_reason === 'both' ? 'Both the time and mileage limits have been reached.' : reminder.due_reason === 'date' ? 'The scheduled service date has been reached.' : 'The service mileage limit has been reached.' }}</p>
    <form v-if="editing && editable" @submit.prevent="save" @keydown.esc.prevent="cancel">
      <p>Clear an interval to disable it. Clear both to remove this reminder.</p>
      <label>Mileage interval (miles)<input ref="firstInput" v-model.number="miles" type="number" min="1" step="1" :disabled="saving" /></label>
      <label>Time interval (months)<input v-model.number="months" type="number" min="1" step="1" :disabled="saving" /></label>
      <p v-if="error" role="alert">{{ error }}</p>
      <button type="submit" :disabled="saving">{{ saving ? 'Saving...' : 'Save reminder' }}</button>
      <button type="button" :disabled="saving" @click="cancel">Cancel</button>
    </form>
    <button v-else-if="editable" ref="editButton" type="button" @click="edit">Edit reminder</button>
  </article>
</template>

<style scoped>
.reminder-card { height: 100%; padding: 21px; border: 1px solid var(--gb-border); border-radius: 12px; background: var(--gb-surface); overflow-wrap: anywhere; }
.reminder-card > header { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.card-kicker, .measure-label { color: #7f8b9f; font-size: 0.68rem; font-weight: 600; letter-spacing: 0.07em; text-transform: uppercase; }
h3 { color: var(--gb-heading); font-size: 1.05rem; font-weight: 650; line-height: 1.3; }
.overdue { border-color: rgba(239, 139, 128, .5); background: linear-gradient(rgba(239, 139, 128, .06), rgba(239, 139, 128, .06)), var(--gb-surface); }
.due { border-color: rgba(179, 199, 255, .4); }
.overdue h3, .overdue .due-badge, [role=alert] { color: var(--gb-danger); }
.due-badge { flex: 0 0 auto; padding: 3px 8px; border-radius: 999px; background: rgba(179, 199, 255, .12); color: var(--gb-accent); font-size: 0.7rem; font-weight: 700; }
.overdue .due-badge { background: rgba(239, 139, 128, .12); }
.last-service { margin-top: 14px; color: var(--gb-text-muted); font-size: 0.8rem; }
.last-service strong { margin-left: 4px; color: var(--gb-text); font-weight: 500; }
.reminder-measures { display: grid; gap: 16px; margin-top: 18px; }
.reminder-measures section { padding-top: 14px; border-top: 1px solid var(--gb-border); }
.measure-detail { margin-top: 3px; color: var(--gb-heading); font-size: 0.92rem; font-weight: 600; }
.measure-target { margin-top: 1px; color: var(--gb-text-muted); font-size: 0.8rem; }
label { display: grid; grid-template-columns: 1fr auto; gap: 5px; margin-top: 10px; color: var(--gb-text-muted); font-size: 0.76rem; }
label span { color: var(--gb-text); }
progress { grid-column: 1 / -1; display: block; width: 100%; height: 5px; accent-color: var(--gb-accent); }
.overdue progress { accent-color: var(--gb-danger); }
input { width: 100%; padding: 8px; background: var(--gb-background-deep); color: var(--gb-heading); border: 1px solid var(--gb-border-strong); border-radius: 6px; }
.due-reason { margin-top: 14px; color: var(--gb-text-muted); font-size: .8rem; }
button { margin: 14px 8px 0 0; padding: 8px 12px; background: transparent; color: var(--gb-accent); border: 1px solid var(--gb-border-strong); border-radius: 8px; cursor: pointer; }
</style>
