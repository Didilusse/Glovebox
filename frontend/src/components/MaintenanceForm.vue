<template>
  <div class="overlay" @click.self="$emit('close')">
    <section class="panel" role="dialog" aria-modal="true" aria-labelledby="maintenance-form-title">
      <header>
        <div>
          <span>{{ isEditMode ? 'Update record' : 'New record' }}</span>
          <h2 id="maintenance-form-title">{{ isEditMode ? 'Edit service' : 'Log completed service' }}</h2>
        </div>
        <button type="button" class="close-button" :disabled="isSaving" @click="$emit('close')">Close</button>
      </header>

      <form @submit.prevent="handleSubmit">
        <section class="form-group">
          <div class="section-heading">
            <span>01</span>
            <div><h3>Work completed</h3><p>Record what was done and the vehicle state at the time.</p></div>
          </div>

          <div class="field full">
            <label for="work_done">Service performed</label>
            <input id="work_done" v-model="workDone" maxlength="500" placeholder="e.g. Engine oil and filter changed" :class="{ invalid: submitted && !workDone.trim() }" />
            <small v-if="submitted && !workDone.trim()" class="error">Describe the completed work.</small>
          </div>

          <div class="field-grid three-columns">
            <div class="field">
              <label for="date">Service date</label>
              <input id="date" v-model="serviceDate" type="date" :class="{ invalid: submitted && !serviceDate }" />
              <small v-if="submitted && !serviceDate" class="error">Date is required.</small>
            </div>
            <div class="field">
              <label for="mileage">Odometer</label>
              <div class="input-suffix"><input id="mileage" v-model.number="mileage" type="number" min="0" :class="{ invalid: submitted && !hasMileage }" /><span>mi</span></div>
              <small v-if="submitted && !hasMileage" class="error">Mileage is required.</small>
            </div>
            <div class="field">
              <label for="cost">Total cost</label>
              <div class="input-prefix"><span>$</span><input id="cost" v-model.number="cost" type="number" min="0" step="0.01" :class="{ invalid: submitted && !hasCost }" /></div>
              <small v-if="submitted && !hasCost" class="error">Cost is required.</small>
            </div>
          </div>

          <div class="field-grid">
            <div class="field">
              <label for="category">Category</label>
              <select id="category" v-model="category">
                <option v-for="option in categories" :key="option" :value="option">{{ titleCase(option) }}</option>
              </select>
            </div>
            <div class="field">
              <label for="done_by">Performed by</label>
              <select id="done_by" v-model="doneBy">
                <option value="self">Owner / DIY</option>
                <option value="shop">Service shop</option>
              </select>
            </div>
          </div>

          <div class="field full">
            <label for="notes">Parts and notes <small>Optional</small></label>
            <textarea id="notes" v-model="notes" rows="3" maxlength="5000" placeholder="Parts used, observations, warranty details..." />
          </div>
        </section>

        <section class="form-group reminder-group" :class="{ active: createReminder }">
          <div class="reminder-toggle">
            <div class="section-heading">
              <span>02</span>
              <div><h3>Schedule the next service</h3><p>Get a reminder by time, mileage, or whichever comes first.</p></div>
            </div>
            <label class="switch">
              <input v-model="createReminder" type="checkbox" aria-label="Schedule next service" @change="reminderTouched = true" />
              <span aria-hidden="true"></span>
              {{ createReminder ? 'On' : 'Off' }}
            </label>
          </div>

          <div v-if="createReminder" class="field-grid reminder-fields">
            <div class="field">
              <label for="interval_months">Time interval</label>
              <div class="input-suffix"><input id="interval_months" v-model.number="intervalMonths" type="number" min="1" placeholder="e.g. 6" @input="reminderTouched = true" /><span>months</span></div>
            </div>
            <div class="field">
              <label for="interval_miles">Mileage interval</label>
              <div class="input-suffix"><input id="interval_miles" v-model.number="intervalMiles" type="number" min="1" placeholder="e.g. 5000" @input="reminderTouched = true" /><span>mi</span></div>
            </div>
            <small>Clear either interval to disable it, or both to remove the reminder.</small>
          </div>
          <p v-if="defaultsLoading" role="status">Loading your oil service defaults...</p>
          <p v-if="defaultsError" role="status">Could not load oil defaults. Set intervals manually or leave reminders off.</p>
        </section>

        <div class="actions">
          <button type="button" class="secondary" :disabled="isSaving" @click="$emit('close')">Cancel</button>
          <button type="submit" class="primary" :disabled="isSaving || defaultsLoading">
            <span v-if="isSaving" class="button-spinner"></span>
            {{ isSaving ? 'Saving...' : isEditMode ? 'Save changes' : 'Save service' }}
          </button>
        </div>
      </form>
    </section>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useApiRequest } from '../utils/auth'

const props = defineProps({
  mode: { type: String, default: 'create' },
  maintenance: { type: Object, default: null },
  isSaving: { type: Boolean, default: false }
})
const emit = defineEmits(['close', 'created', 'updated'])
const categories = ['engine', 'suspension', 'exterior', 'interior', 'wheels', 'brakes', 'exhaust', 'fluids', 'other']

const serviceDate = ref('')
const mileage = ref(null)
const cost = ref(null)
const doneBy = ref('self')
const category = ref('other')
const workDone = ref('')
const notes = ref('')
const createReminder = ref(false)
const intervalMonths = ref(null)
const intervalMiles = ref(null)
const submitted = ref(false)
const reminderTouched = ref(false)
const defaultsError = ref(false)
const defaultsLoading = ref(false)
const request = useApiRequest()
let defaultsRequest
const isOilChange = computed(() => /\boil\b/i.test(workDone.value) && /\bchang(?:e|ed|ing)\b/i.test(workDone.value))

const isEditMode = computed(() => props.mode === 'edit')
const hasMileage = computed(() => isEditMode.value || (mileage.value !== null && mileage.value !== '' && Number(mileage.value) >= 0))
const hasCost = computed(() => isEditMode.value || (cost.value !== null && cost.value !== '' && Number(cost.value) >= 0))

watch(
  () => props.maintenance,
  (maintenance) => {
    serviceDate.value = maintenance?.date_of_service ?? new Date().toISOString().slice(0, 10)
    mileage.value = maintenance?.mileage ?? null
    cost.value = maintenance?.cost ?? null
    doneBy.value = maintenance?.done_by ?? 'self'
    category.value = maintenance?.category ?? 'other'
    workDone.value = maintenance?.work_done ?? ''
    notes.value = maintenance?.notes ?? ''
    createReminder.value = maintenance?.interval_months != null || maintenance?.interval_miles != null
    intervalMonths.value = maintenance?.interval_months ?? null
    intervalMiles.value = maintenance?.interval_miles ?? null
    submitted.value = false
    reminderTouched.value = false
  },
  { immediate: true }
)

watch(isOilChange, async oil => {
  if (isEditMode.value || reminderTouched.value) return
  if (!oil) { createReminder.value = false; intervalMiles.value = null; intervalMonths.value = null; return }
  defaultsLoading.value = true
  try {
    defaultsRequest ??= request('/settings', undefined, 'GET')
    const settings = await defaultsRequest
    if (isEditMode.value || !isOilChange.value || reminderTouched.value) return
    intervalMiles.value = settings.oil_interval_miles
    intervalMonths.value = settings.oil_interval_months
    createReminder.value = intervalMiles.value != null || intervalMonths.value != null
    defaultsError.value = false
  } catch (e) { if (e.name !== 'AbortError') defaultsError.value = true; defaultsRequest = undefined }
  finally { defaultsLoading.value = false }
})

function handleSubmit() {
  if (defaultsLoading.value || props.isSaving) return
  submitted.value = true
  if (!serviceDate.value || !workDone.value.trim() || !hasMileage.value || !hasCost.value) return

  const payload = {
    date_of_service: serviceDate.value,
    mileage: numberOrNull(mileage.value),
    cost: numberOrNull(cost.value),
    done_by: doneBy.value,
    category: category.value,
    interval_months: createReminder.value ? positiveNumberOrNull(intervalMonths.value) : null,
    interval_miles: createReminder.value ? positiveNumberOrNull(intervalMiles.value) : null,
    work_done: workDone.value.trim(),
    notes: notes.value.trim() || null
  }
  emit(isEditMode.value ? 'updated' : 'created', payload)
}

function isPositive(value) { return value !== null && value !== '' && Number(value) > 0 }
function numberOrNull(value) { return value === null || value === '' ? null : Number(value) }
function positiveNumberOrNull(value) { return isPositive(value) ? Number(value) : null }
function titleCase(value) { return value.charAt(0).toUpperCase() + value.slice(1) }
</script>

<style scoped>
.overlay { position: fixed; inset: 0; z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 24px; overflow-y: auto; background: rgba(8, 11, 15, .8); backdrop-filter: blur(7px); }
.panel { width: min(100%, 720px); max-height: calc(100vh - 48px); padding: 24px; overflow-y: auto; border: 1px solid rgba(179, 199, 255, .14); border-radius: 14px; background: #232930; box-shadow: 0 24px 70px rgba(0, 0, 0, .42); }
header, .actions, .reminder-toggle { display: flex; align-items: center; justify-content: space-between; gap: 14px; }
header > div > span { color: var(--gb-accent); font-size: .7rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; }
h2 { margin-top: 2px; color: var(--gb-heading); font-size: 1.4rem; font-weight: 680; letter-spacing: -.02em; }
.close-button, .secondary, .primary { border-radius: 8px; padding: 9px 14px; cursor: pointer; }
.close-button, .secondary { border: 1px solid var(--gb-border-strong); background: transparent; color: var(--gb-text-muted); }
.close-button:hover:not(:disabled), .secondary:hover:not(:disabled) { border-color: var(--gb-accent); color: var(--gb-heading); }
form { display: flex; flex-direction: column; gap: 24px; margin-top: 24px; }
.form-group { display: flex; flex-direction: column; gap: 14px; padding-bottom: 24px; border-bottom: 1px solid rgba(179, 199, 255, .1); }
.section-heading { display: flex; align-items: flex-start; gap: 10px; }
.section-heading > span { padding-top: 2px; color: var(--gb-accent); font-size: .68rem; font-weight: 700; }
.section-heading h3 { color: var(--gb-heading); font-size: .9rem; font-weight: 650; }
.section-heading p { margin-top: 1px; color: var(--gb-text-muted); font-size: .74rem; }
.field-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.three-columns { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.field { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
label { color: var(--gb-text); font-size: .8rem; font-weight: 600; }
label small { margin-left: 3px; color: var(--gb-text-muted); font-size: .68rem; font-weight: 400; }
input, select, textarea { box-sizing: border-box; width: 100%; min-width: 0; padding: 10px 11px; border: 1px solid rgba(179, 199, 255, .13); border-radius: 8px; outline: none; background: #171c22; color: var(--gb-heading); font: inherit; font-size: .84rem; }
textarea { resize: vertical; }
input:focus, select:focus, textarea:focus { border-color: var(--gb-accent); box-shadow: 0 0 0 3px rgba(179, 199, 255, .1); }
.input-suffix, .input-prefix { position: relative; }
.input-suffix input { padding-right: 42px; }
.input-prefix input { padding-left: 26px; }
.input-suffix span, .input-prefix span { position: absolute; top: 50%; color: var(--gb-text-muted); font-size: .72rem; pointer-events: none; }
.input-suffix span { right: 10px; transform: translateY(-50%); }
.input-prefix span { left: 11px; transform: translateY(-50%); }
.invalid { border-color: var(--gb-danger); }
.error { color: var(--gb-danger); font-size: .74rem; }
.reminder-group { padding: 14px; border: 1px solid rgba(179, 199, 255, .1); border-radius: 9px; background: #1c2128; }
.reminder-group.active { border-color: rgba(179, 199, 255, .22); }
.switch { display: flex; align-items: center; gap: 7px; color: var(--gb-text-muted); font-size: .72rem; cursor: pointer; }
.switch input { position: absolute; width: 1px; height: 1px; opacity: 0; }
.switch > span { position: relative; width: 34px; height: 19px; border-radius: 99px; background: #3a424d; transition: background 150ms; }
.switch > span::after { position: absolute; top: 3px; left: 3px; width: 13px; height: 13px; border-radius: 50%; background: #aeb7c5; content: ''; transition: transform 150ms, background 150ms; }
.switch input:checked + span { background: #647caf; }
.switch input:checked + span::after { transform: translateX(15px); background: #fff; }
.switch input:focus-visible + span { outline: 2px solid var(--gb-accent); outline-offset: 2px; }
.reminder-fields { padding-top: 4px; }
.interval-error { grid-column: 1 / -1; }
.actions { justify-content: flex-end; }
.primary { display: inline-flex; align-items: center; justify-content: center; gap: 8px; border: 0; background: var(--gb-accent); color: #141820; font-weight: 700; }
.primary:hover:not(:disabled) { background: var(--gb-accent-hover); }
button:disabled { opacity: .55; cursor: not-allowed; }
.button-spinner { width: 14px; height: 14px; border: 2px solid rgba(20, 24, 32, .3); border-top-color: #141820; border-radius: 50%; animation: spin 700ms linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 650px) {
  .overlay { align-items: flex-start; padding: 0; }
  .panel { max-height: none; min-height: 100vh; padding: 20px 16px; border: 0; border-radius: 0; }
  .field-grid, .three-columns { grid-template-columns: 1fr; }
  .reminder-toggle { align-items: flex-start; }
}
</style>
