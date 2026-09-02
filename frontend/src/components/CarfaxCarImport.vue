<template>
  <section class="import-flow">
    <div v-if="!preview" class="upload-step">
      <label class="drop-zone" :class="{ active: file }" for="new-car-carfax">
        <span class="drop-title">{{ file ? file.name : 'Choose a CARFAX PDF' }}</span>
        <span>Glovebox will identify the car and import every service visit.</span>
        <small>Text-based PDF only, up to 10 MB. Your report is not stored.</small>
        <input id="new-car-carfax" type="file" accept="application/pdf,.pdf" @change="selectFile" />
      </label>
      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <div class="actions">
        <button type="button" class="secondary" :disabled="busy" @click="$emit('cancel')">Back</button>
        <button type="button" class="primary" :disabled="!file || busy" @click="upload">
          {{ busy ? 'Reading report…' : 'Read CARFAX report' }}
        </button>
      </div>
    </div>

    <div v-else class="review-step">
      <div class="report-heading">
        <div>
          <span class="eyebrow">Report recognized</span>
          <strong>{{ preview.report.vehicle }}</strong>
          <small>VIN {{ preview.report.vin }}</small>
        </div>
        <button type="button" class="link-button" :disabled="busy" @click="reset">Use another PDF</button>
      </div>

      <div class="summary">
        <span><strong>{{ preview.summary.found }}</strong> service visits</span>
        <span><strong>{{ preview.summary.latest_mileage?.toLocaleString() || 'Unknown' }}</strong> latest miles</span>
        <span><strong>{{ preview.summary.missing_mileage }}</strong> without mileage</span>
      </div>

      <p v-for="warning in preview.warnings" :key="warning" class="warning">{{ warning }}</p>
      <p v-if="error" class="error" role="alert">{{ error }}</p>

      <div class="vehicle-fields">
        <label>Year<input v-model.number="vehicle.year" type="number" min="1886" :max="maxVehicleYear" /></label>
        <label>Make<input v-model.trim="vehicle.make" /></label>
        <label class="model-field">Model<input v-model.trim="vehicle.model" /></label>
        <label>Current mileage<input v-model.number="vehicle.mileage" type="number" min="0" placeholder="Unknown" /></label>
        <label>Fuel type
          <select v-model="vehicle.fuel_type">
            <option value="gas">Gasoline</option>
            <option value="diesel">Diesel</option>
            <option value="electric">Electric</option>
          </select>
        </label>
        <label>License plate<input v-model.trim="vehicle.license_plate" placeholder="Optional" /></label>
      </div>

      <details class="history-preview">
        <summary>Review all {{ preview.summary.found }} service visits</summary>
        <div class="history-list">
          <article v-for="record in preview.records" :key="record.source_record_key">
            <time>{{ record.date_of_service }}</time>
            <div><strong>{{ record.work_done }}</strong><small>{{ record.service_provider || 'Unknown provider' }} · {{ record.mileage?.toLocaleString() || 'Mileage unknown' }}</small></div>
          </article>
        </div>
      </details>

      <div class="actions">
        <button type="button" class="secondary" :disabled="busy" @click="reset">Back</button>
        <button type="button" class="primary" :disabled="!validVehicle || busy" @click="confirm">
          {{ busy ? 'Adding car…' : `Add car and ${preview.summary.found} records` }}
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({ apiBase: { type: String, required: true } })
const emit = defineEmits(['created', 'cancel'])
const maxVehicleYear = new Date().getFullYear() + 1
const file = ref(null)
const preview = ref(null)
const vehicle = ref({})
const busy = ref(false)
const error = ref('')

const validVehicle = computed(() => {
  const value = vehicle.value
  return Number.isInteger(value.year) && value.year >= 1886 && value.year <= maxVehicleYear &&
    Boolean(value.make?.trim()) && Boolean(value.model?.trim()) &&
    (value.mileage === null || value.mileage === '' || (Number.isFinite(Number(value.mileage)) && Number(value.mileage) >= 0))
})

function selectFile(event) {
  error.value = ''
  const selected = event.target.files?.[0] || null
  if (!selected) return
  if (!selected.name.toLowerCase().endsWith('.pdf') || !['application/pdf', 'application/x-pdf'].includes(selected.type)) {
    file.value = null
    error.value = 'Choose a PDF file.'
    return
  }
  if (selected.size > 10 * 1024 * 1024) {
    file.value = null
    error.value = 'The PDF must be 10 MB or smaller.'
    return
  }
  file.value = selected
}

async function upload() {
  busy.value = true
  error.value = ''
  const form = new FormData()
  form.append('file', file.value)
  try {
    const response = await fetch(`${props.apiBase}/cars/import/carfax/preview`, { method: 'POST', body: form })
    if (!response.ok) throw new Error(await responseMessage(response, 'Could not read this CARFAX report.'))
    preview.value = await response.json()
    vehicle.value = {
      year: preview.value.report.year,
      make: preview.value.report.make || '',
      model: preview.value.report.model || '',
      vin: preview.value.report.vin,
      mileage: preview.value.summary.latest_mileage,
      fuel_type: preview.value.report.fuel_type || 'gas',
      license_plate: ''
    }
  } catch (caught) {
    error.value = caught.message
  } finally {
    busy.value = false
  }
}

async function confirm() {
  if (!validVehicle.value) return
  busy.value = true
  error.value = ''
  const allowedFields = ['date_of_service', 'mileage', 'cost', 'done_by', 'work_done', 'category', 'notes', 'service_provider', 'source_record_key']
  const records = preview.value.records.map(record => Object.fromEntries(allowedFields.map(field => [field, record[field]])))
  const vehiclePayload = {
    year: Number(vehicle.value.year),
    make: vehicle.value.make.trim(),
    model: vehicle.value.model.trim(),
    vin: preview.value.report.vin,
    mileage: vehicle.value.mileage === '' ? null : vehicle.value.mileage,
    fuel_type: vehicle.value.fuel_type
  }
  if (vehicle.value.license_plate) vehiclePayload.license_plate = vehicle.value.license_plate
  try {
    const response = await fetch(`${props.apiBase}/cars/import/carfax/confirm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ report_vin: preview.value.report.vin, vehicle: vehiclePayload, records })
    })
    if (!response.ok) throw new Error(await responseMessage(response, 'The car could not be imported.'))
    emit('created', await response.json())
  } catch (caught) {
    error.value = caught.message
  } finally {
    busy.value = false
  }
}

function reset() {
  preview.value = null
  vehicle.value = {}
  file.value = null
  error.value = ''
}

async function responseMessage(response, fallback) {
  try {
    const body = await response.json()
    return typeof body.detail === 'string' ? body.detail : fallback
  } catch {
    return fallback
  }
}
</script>

<style scoped>
.import-flow { display: grid; gap: 18px; }
.upload-step, .review-step { display: grid; gap: 18px; }
.drop-zone { min-height: 220px; display: grid; place-content: center; gap: 8px; padding: 24px; border: 1px dashed var(--gb-border-strong); border-radius: 14px; background: rgba(179, 199, 255, .03); text-align: center; color: var(--gb-text-muted); cursor: pointer; }
.drop-zone:hover, .drop-zone.active { border-color: var(--gb-accent); background: rgba(179, 199, 255, .07); }
.drop-zone input { position: absolute; width: 1px; height: 1px; opacity: 0; }
.drop-title { color: var(--gb-heading); font-size: 1.15rem; font-weight: 700; }
.drop-zone small, .report-heading small, .history-list small { color: var(--gb-text-muted); }
.report-heading { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; padding: 16px; border: 1px solid var(--gb-border); border-radius: 12px; background: rgba(179, 199, 255, .04); }
.report-heading > div { display: grid; gap: 4px; }
.report-heading strong { color: var(--gb-heading); font-size: 1.05rem; }
.eyebrow { color: var(--gb-accent); font-size: .68rem; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; }
.summary { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.summary span { display: grid; gap: 2px; padding: 12px; border-radius: 10px; background: var(--gb-background-deep); color: var(--gb-text-muted); font-size: .78rem; }
.summary strong { color: var(--gb-heading); font-size: 1rem; }
.vehicle-fields { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.vehicle-fields label { display: grid; gap: 6px; color: var(--gb-text-muted); font-size: .8rem; font-weight: 600; }
.vehicle-fields input, .vehicle-fields select { min-width: 0; padding: 10px; border: 1px solid var(--gb-border); border-radius: 8px; background: var(--gb-background-deep); color: var(--gb-heading); }
.history-preview { border: 1px solid var(--gb-border); border-radius: 12px; overflow: hidden; }
.history-preview summary { padding: 13px 15px; color: var(--gb-accent); font-weight: 700; cursor: pointer; }
.history-list { max-height: 250px; overflow: auto; border-top: 1px solid var(--gb-border); }
.history-list article { display: grid; grid-template-columns: 100px 1fr; gap: 12px; padding: 12px 15px; border-bottom: 1px solid var(--gb-border); }
.history-list article:last-child { border-bottom: 0; }
.history-list time { color: var(--gb-text-muted); font-size: .8rem; }
.history-list div { display: grid; gap: 4px; }
.history-list strong { color: var(--gb-heading); font-size: .84rem; font-weight: 600; }
.actions { display: flex; justify-content: flex-end; gap: 10px; padding-top: 16px; border-top: 1px solid var(--gb-border); }
.primary, .secondary { padding: 10px 18px; border-radius: 999px; font-weight: 700; cursor: pointer; }
.primary { border: 0; background: var(--gb-accent); color: #141820; }
.secondary { border: 1px solid var(--gb-border); background: transparent; color: var(--gb-text); }
.link-button { border: 0; background: transparent; color: var(--gb-accent); cursor: pointer; }
button:disabled { opacity: .5; cursor: not-allowed; }
.warning, .error { margin: 0; padding: 10px 12px; border-radius: 8px; }
.warning { color: #e3c27f; background: rgba(218, 166, 65, .08); }
.error { color: #ffb0b0; background: rgba(231, 76, 60, .1); }
@media (max-width: 650px) {
  .summary, .vehicle-fields { grid-template-columns: 1fr 1fr; }
  .model-field { grid-column: 1 / -1; }
  .history-list article { grid-template-columns: 1fr; gap: 4px; }
  .report-heading { flex-direction: column; }
}
</style>
