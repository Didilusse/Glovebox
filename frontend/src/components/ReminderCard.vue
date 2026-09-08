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
  <article class="reminder-card" :class="{ overdue: reminder.is_overdue }">
    <h3>{{ reminder.work_done }}</h3>
    <strong v-if="reminder.is_due || reminder.is_overdue" class="due-badge">{{ reminder.is_overdue ? 'Overdue' : 'Due' }}</strong>
    <p>Last service: {{ reminder.date_of_service }}</p>
    <div v-if="reminder.interval_miles != null || reminder.reminder_mileage != null">
      <p v-if="reminder.interval_miles != null">Mileage: every {{ reminder.interval_miles }} mi</p>
      <p>Due at {{ reminder.reminder_mileage ?? 'unknown' }} mi</p>
      <label v-if="reminder.progress_miles != null">Mileage progress: {{ Math.round(reminder.progress_miles) }}%
        <progress :value="reminder.progress_miles" max="100" aria-label="Mileage progress" />
      </label>
      <p v-else>Mileage progress unavailable</p>
    </div>
    <div v-if="reminder.interval_months != null || reminder.reminder_date != null">
      <p v-if="reminder.interval_months != null">Time: every {{ reminder.interval_months }} months</p>
      <p>Due date: {{ reminder.reminder_date ?? 'unknown' }}</p>
      <label v-if="reminder.progress_time != null">Time progress: {{ Math.round(reminder.progress_time) }}%
        <progress :value="reminder.progress_time" max="100" aria-label="Time progress" />
      </label>
      <p v-else>Time progress unavailable</p>
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
.reminder-card { padding: 20px; border: 1px solid var(--gb-border); border-radius: 14px; background: var(--gb-surface); overflow-wrap: anywhere; }
h3 { color: var(--gb-heading); }
.overdue { border-color: var(--gb-danger); background: linear-gradient(rgba(239, 139, 128, .055), rgba(239, 139, 128, .055)), var(--gb-surface); }
.overdue h3, .overdue .due-badge, [role=alert] { color: var(--gb-danger); }
.due-badge { display: inline-block; padding: 3px 9px; margin: 8px 0; border: 1px solid currentColor; border-radius: 20px; color: var(--gb-accent); }
label { display: block; margin-top: 12px; }
progress { display: block; width: 100%; accent-color: var(--gb-accent); }
.overdue progress { accent-color: var(--gb-danger); }
input { width: 100%; padding: 8px; background: var(--gb-background-deep); color: var(--gb-heading); border: 1px solid var(--gb-border-strong); border-radius: 6px; }
.due-reason { margin-top: 14px; color: var(--gb-text-muted); font-size: .8rem; }
button { margin: 14px 8px 0 0; padding: 8px 12px; background: transparent; color: var(--gb-accent); border: 1px solid var(--gb-border-strong); border-radius: 8px; cursor: pointer; }
</style>
