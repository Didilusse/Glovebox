<template>
  <div class="overlay" @click.self="close">
    <section class="panel" role="dialog" aria-modal="true" aria-labelledby="import-title">
      <header class="panel-header">
        <div>
          <p class="eyebrow">Service history importer</p>
          <h2 id="import-title">Import a CARFAX report</h2>
          <p class="intro">Review every service visit before anything is added to your glovebox.</p>
        </div>
        <button type="button" class="text-button" :disabled="busy" @click="close">Close</button>
      </header>

      <div v-if="!preview" class="upload-stage">
        <label class="drop-zone" :class="{ active: file }" for="carfax-file">
          <span class="drop-title">{{ file ? file.name : 'Choose a CARFAX PDF' }}</span>
          <span class="drop-copy">PDF only, up to 10 MB. The report is parsed but not stored.</span>
          <input id="carfax-file" type="file" accept="application/pdf,.pdf" @change="selectFile" />
        </label>
        <p v-if="error" class="error" role="alert">{{ error }}</p>
        <div class="footer-actions">
          <button type="button" class="secondary" :disabled="busy" @click="close">Cancel</button>
          <button type="button" class="primary" :disabled="!file || busy" @click="upload">
            {{ busy ? 'Reading report…' : 'Preview service history' }}
          </button>
        </div>
      </div>

      <div v-else class="review-stage">
        <section class="report-strip">
          <div>
            <span class="strip-label">Report vehicle</span>
            <strong>{{ preview.report.vehicle || 'Vehicle details unavailable' }}</strong>
            <span class="vin">VIN {{ preview.report.vin }}</span>
          </div>
          <div class="metrics">
            <span><strong>{{ preview.summary.found }}</strong> found</span>
            <span><strong>{{ selectedCount }}</strong> selected</span>
            <span><strong>{{ preview.summary.missing_mileage }}</strong> unknown mileage</span>
            <span v-if="preview.summary.duplicates"><strong>{{ preview.summary.duplicates }}</strong> duplicates</span>
          </div>
        </section>

        <div v-if="preview.warnings.length" class="report-warning">
          <p v-for="warning in preview.warnings" :key="warning">{{ warning }}</p>
        </div>
        <p v-if="error" class="error" role="alert">{{ error }}</p>

        <div class="selection-bar">
          <label><input type="checkbox" :checked="allSelected" @change="toggleAll" /> Select all new records</label>
          <button type="button" class="text-button" :disabled="busy" @click="reset">Choose another PDF</button>
        </div>

        <div class="records">
          <article v-for="(record, index) in records" :key="record.source_record_key" class="record" :class="{ muted: record.duplicate || !record.selected }">
            <div class="record-select">
              <input v-model="record.selected" type="checkbox" :disabled="record.duplicate || busy" :aria-label="`Include service on ${record.date_of_service}`" />
              <span class="record-number">{{ String(index + 1).padStart(2, '0') }}</span>
            </div>
            <div class="record-fields">
              <div class="field-row compact">
                <label>Date<input v-model="record.date_of_service" type="date" /></label>
                <label>Mileage<input v-model.number="record.mileage" type="number" min="0" placeholder="Unknown" /></label>
                <label>Category
                  <select v-model="record.category">
                    <option v-for="category in categories" :key="category" :value="category">{{ category }}</option>
                  </select>
                </label>
              </div>
              <label>Service provider<input v-model="record.service_provider" placeholder="Unknown provider" /></label>
              <label>Work performed<textarea v-model="record.work_done" rows="2" maxlength="500" /></label>
              <div class="record-meta">
                <span>Page {{ record.source_page }}</span>
                <span v-if="record.duplicate" class="duplicate">Already imported</span>
                <span v-for="warning in record.warnings" :key="warning" class="warning">{{ warning }}</span>
              </div>
            </div>
          </article>
        </div>

        <div class="footer-actions sticky">
          <span class="selection-copy">{{ selectedCount }} record{{ selectedCount === 1 ? '' : 's' }} ready</span>
          <button type="button" class="secondary" :disabled="busy" @click="close">Cancel</button>
          <button type="button" class="primary" :disabled="selectedCount === 0 || busy" @click="confirmImport">
            {{ busy ? 'Importing…' : `Import ${selectedCount} records` }}
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  carId: { type: String, required: true },
  apiBase: { type: String, required: true }
})
const emit = defineEmits(['close', 'imported'])

const categories = ['engine', 'suspension', 'exterior', 'interior', 'wheels', 'brakes', 'exhaust', 'fluids', 'other']
const file = ref(null)
const preview = ref(null)
const records = ref([])
const busy = ref(false)
const error = ref('')

const selectedCount = computed(() => records.value.filter(record => record.selected && !record.duplicate).length)
const selectable = computed(() => records.value.filter(record => !record.duplicate))
const allSelected = computed(() => selectable.value.length > 0 && selectable.value.every(record => record.selected))

function close() {
  if (!busy.value) emit('close')
}

function selectFile(event) {
  error.value = ''
  const selected = event.target.files?.[0] || null
  if (!selected) {
    file.value = null
    return
  }
  if (!selected.name.toLowerCase().endsWith('.pdf') || !['application/pdf', 'application/x-pdf'].includes(selected.type)) {
    error.value = 'Choose a PDF file.'
    file.value = null
    return
  }
  if (selected.size > 10 * 1024 * 1024) {
    error.value = 'The PDF must be 10 MB or smaller.'
    file.value = null
    return
  }
  file.value = selected
}

async function upload() {
  if (!file.value) return
  busy.value = true
  error.value = ''
  const form = new FormData()
  form.append('file', file.value)
  try {
    const response = await fetch(`${props.apiBase}/cars/${props.carId}/logs/import/preview`, { method: 'POST', body: form })
    if (!response.ok) throw new Error(await responseMessage(response, 'Could not read this CARFAX report.'))
    preview.value = await response.json()
    records.value = preview.value.records.map(record => ({ ...record, selected: !record.duplicate }))
  } catch (caught) {
    error.value = caught.message
  } finally {
    busy.value = false
  }
}

function toggleAll(event) {
  for (const record of selectable.value) record.selected = event.target.checked
}

function reset() {
  preview.value = null
  records.value = []
  file.value = null
  error.value = ''
}

async function confirmImport() {
  busy.value = true
  error.value = ''
  const allowedFields = ['date_of_service', 'mileage', 'cost', 'done_by', 'work_done', 'category', 'notes', 'service_provider', 'source_record_key']
  const selectedRecords = records.value.filter(record => record.selected && !record.duplicate).map(record => {
    const payload = {}
    for (const field of allowedFields) payload[field] = record[field] === '' ? null : record[field]
    return payload
  })
  try {
    const response = await fetch(`${props.apiBase}/cars/${props.carId}/logs/import/confirm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ report_vin: preview.value.report.vin, records: selectedRecords })
    })
    if (!response.ok) throw new Error(await responseMessage(response, 'The service history could not be imported.'))
    emit('imported', await response.json())
  } catch (caught) {
    error.value = caught.message
  } finally {
    busy.value = false
  }
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
.overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(7, 10, 17, 0.82);
  backdrop-filter: blur(8px);
}

.panel {
  width: min(1080px, 100%);
  max-height: calc(100vh - 48px);
  overflow: auto;
  border: 1px solid rgba(179, 199, 255, .14);
  border-radius: 14px;
  background: #232930;
  box-shadow: 0 24px 70px rgba(0, 0, 0, .42);
}

.panel-header,
.footer-actions,
.selection-bar,
.report-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.panel-header { padding: 28px 30px 22px; border-bottom: 1px solid var(--gb-border); }
.panel-header h2 { margin: 2px 0 5px; color: var(--gb-heading); font-size: clamp(1.3rem, 3vw, 1.5rem); font-weight: 680; letter-spacing: -.02em; }
.eyebrow, .strip-label { margin: 0; color: var(--gb-accent); font-size: .72rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }
.intro { margin: 0; color: var(--gb-text-muted); }
.upload-stage, .review-stage { padding: 26px 30px 30px; }

.drop-zone {
  min-height: 220px;
  display: grid;
  place-content: center;
  gap: 8px;
  padding: 30px;
  border: 1px dashed rgba(179, 199, 255, .2);
  border-radius: 10px;
  text-align: center;
  cursor: pointer;
  background: rgba(179, 199, 255, .025);
}
.drop-zone:hover, .drop-zone.active { border-color: var(--gb-accent); background: rgba(179, 199, 255, .06); }
.drop-zone input { position: absolute; width: 1px; height: 1px; opacity: 0; }
.drop-title { color: var(--gb-heading); font-size: 1.15rem; font-weight: 700; }
.drop-copy, .vin, .selection-copy { color: var(--gb-text-muted); font-size: .86rem; }

.report-strip { padding: 18px; border: 1px solid rgba(179, 199, 255, .1); border-radius: 10px; background: #1c2128; }
.report-strip > div:first-child { display: grid; gap: 4px; }
.metrics { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; }
.metrics span { padding: 2px 10px; border-left: 1px solid rgba(179, 199, 255, .12); color: var(--gb-text-muted); font-size: .76rem; }
.metrics strong { color: var(--gb-heading); }
.report-warning, .error { margin: 14px 0 0; padding: 12px 14px; border-radius: 10px; }
.report-warning { border: 1px solid rgba(218, 166, 65, .35); color: #e3c27f; background: rgba(218, 166, 65, .08); }
.report-warning p { margin: 3px 0; }
.error { color: #ffb0b0; background: rgba(231, 76, 60, .1); }
.selection-bar { padding: 20px 2px 12px; color: var(--gb-text-muted); }

.records { display: grid; gap: 10px; }
.record { display: grid; grid-template-columns: 52px 1fr; border: 1px solid rgba(179, 199, 255, .1); border-radius: 9px; padding: 16px; background: #242a32; transition: opacity .2s, border-color .2s, background .2s; }
.record:focus-within { border-color: var(--gb-border-strong); }
.record.muted { opacity: .55; }
.record-select { display: flex; flex-direction: column; align-items: flex-start; gap: 12px; }
.record-number { color: var(--gb-text-muted); font-size: .72rem; font-variant-numeric: tabular-nums; }
.record-fields { display: grid; gap: 10px; }
.field-row { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
label { display: grid; gap: 5px; color: var(--gb-text-muted); font-size: .76rem; font-weight: 600; }
input, select, textarea { width: 100%; box-sizing: border-box; border: 1px solid var(--gb-border); border-radius: 9px; padding: 9px 10px; background: rgba(7, 10, 17, .35); color: var(--gb-heading); font: inherit; }
textarea { resize: vertical; }
.record-meta { display: flex; flex-wrap: wrap; gap: 8px; color: var(--gb-text-muted); font-size: .72rem; }
.warning { color: #e3c27f; }
.duplicate { color: var(--gb-accent); }

.footer-actions { margin-top: 22px; }
.footer-actions.sticky { position: sticky; bottom: -30px; z-index: 2; margin: 20px -30px -30px; padding: 16px 30px; border-top: 1px solid var(--gb-border); background: color-mix(in srgb, var(--gb-surface) 94%, transparent); backdrop-filter: blur(8px); }
.selection-copy { margin-right: auto; }
button { cursor: pointer; }
button:disabled { cursor: not-allowed; opacity: .5; }
.primary, .secondary, .text-button { border-radius: 8px; padding: 10px 16px; font-weight: 700; }
.primary { border: 0; background: var(--gb-accent); color: #141820; }
.primary:hover:not(:disabled) { background: var(--gb-accent-hover); }
.secondary { border: 1px solid var(--gb-border-strong); background: transparent; color: var(--gb-heading); }
.text-button { border: 0; padding-inline: 4px; background: transparent; color: var(--gb-accent); }
button:active:not(:disabled) { transform: translateY(1px); }
button:focus-visible { outline: 2px solid var(--gb-accent); outline-offset: 2px; }

@media (max-width: 700px) {
  .overlay { padding: 0; place-items: stretch; }
  .panel { max-height: 100vh; border-radius: 0; }
  .panel-header, .upload-stage, .review-stage { padding-left: 18px; padding-right: 18px; }
  .report-strip, .panel-header { align-items: flex-start; }
  .report-strip { flex-direction: column; }
  .metrics { justify-content: flex-start; }
  .record { grid-template-columns: 34px 1fr; padding: 13px 10px; }
  .field-row { grid-template-columns: 1fr 1fr; }
  .field-row label:last-child { grid-column: 1 / -1; }
  .footer-actions.sticky { bottom: -30px; margin-left: -18px; margin-right: -18px; padding-left: 18px; padding-right: 18px; flex-wrap: wrap; }
}
</style>
