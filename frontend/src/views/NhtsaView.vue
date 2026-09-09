<template>
  <NavBar />

  <main class="nhtsa-page">
    <header class="page-header">
      <div class="title-row">
        <div>
          <span class="context">Safety center</span>
          <h1>{{ vehicleName }}</h1>
          <p>{{ vin ? `VIN ${vin}` : 'NHTSA vehicle information' }}</p>
        </div>
        <button type="button" class="refresh-button" :disabled="loading" @click="loadData">
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M16 10a6 6 0 1 1-1.76-4.24M16 4v4h-4" /></svg>
          {{ loading ? 'Updating' : 'Refresh data' }}
        </button>
      </div>

      <section v-if="!loadError && data" class="overview" aria-label="Safety overview">
        <div class="overview-lead">
          <span>Recall campaigns</span>
          <strong :class="{ 'has-recalls': recalls.length }">
            {{ recalls.length ? recalls.length : 'No' }}
            <small>{{ recalls.length === 1 ? 'campaign found' : 'campaigns found' }}</small>
          </strong>
          <p>Model-level campaigns from NHTSA. Repair status is specific to your VIN.</p>
        </div>
        <dl>
          <div>
            <dt>Safety rating</dt>
            <dd>{{ overallRating }}</dd>
          </div>
          <div>
            <dt>Vehicle year</dt>
            <dd>{{ vehicleYear }}</dd>
          </div>
          <div>
            <dt>Data source</dt>
            <dd>NHTSA <small>Live lookup</small></dd>
          </div>
        </dl>
      </section>
      <aside v-if="vinMismatch" class="vin-mismatch" role="alert">
        <strong>Check this vehicle's details</strong>
        <span>The saved vehicle is {{ savedVehicleName }}, but VIN {{ vin }} decodes to {{ vehicleName }}{{ vehicleYear !== 'N/A' ? ` (${vehicleYear})` : '' }}.</span>
      </aside>
    </header>

    <div v-if="loading" class="board-message">
      <span class="loader"></span>
      Loading safety information...
    </div>

    <div v-else-if="loadError" class="board-message error-message">
      <p>We couldn't load NHTSA information.</p>
      <span>{{ loadError }}</span>
      <button type="button" @click="loadData">Try again</button>
    </div>

    <div v-else-if="data" class="content">
      <section v-if="vehicleIdentity.length" class="section vehicle-profile">
        <div class="section-heading">
          <div>
            <span class="section-kicker">Decoded from VIN</span>
            <h2>Vehicle information</h2>
          </div>
          <span class="section-count">NHTSA vehicle profile</span>
        </div>
        <dl class="identity-strip">
          <div v-for="field in vehicleIdentity" :key="field.label">
            <dt>{{ field.label }}</dt>
            <dd>{{ field.value }}</dd>
          </div>
        </dl>
        <div v-if="vehicleSpecificationGroups.length" class="specification-groups">
          <section v-for="group in vehicleSpecificationGroups" :key="group.title" class="specification-group">
            <h3>{{ group.title }}</h3>
            <dl>
              <div v-for="field in group.fields" :key="field.label">
                <dt>{{ field.label }}</dt>
                <dd>{{ field.value }}</dd>
              </div>
            </dl>
          </section>
        </div>
      </section>

      <section v-if="selectedRating" class="section">
        <div class="section-heading">
          <div>
            <span class="section-kicker">Crash testing</span>
            <h2>Safety ratings</h2>
          </div>
          <span class="section-count">NHTSA results</span>
        </div>
        <div class="rating-grid">
          <div v-for="field in ratingFields" :key="field.label" class="rating-card">
            <span>{{ field.label }}</span>
            <strong :class="{ unrated: field.value === 'Not Rated' }">
              {{ field.value === 'Not Rated' ? '—' : field.value }}
            </strong>
          </div>
        </div>
      </section>

      <section class="section">
        <div class="section-heading">
          <div>
            <span class="section-kicker">Safety campaigns</span>
            <h2>Recalls</h2>
          </div>
          <a
            v-if="recallLookupUrl"
            class="lookup-link"
            :href="recallLookupUrl"
            target="_blank"
            rel="noreferrer"
          >
            Check VIN status <span aria-hidden="true">↗</span>
          </a>
        </div>

        <div v-if="recalls.length" class="recall-list">
          <article v-for="recall in recalls" :key="recall.recall_number" class="recall-item">
            <div class="recall-summary">
              <div class="recall-identity">
                <span class="campaign-label">NHTSA recall {{ recall.recall_number }}</span>
                <h3>{{ recall.manufacturer || 'Manufacturer recall' }}</h3>
              </div>
              <span v-if="recall.status" class="status-pill">{{ recall.status }}</span>
              <span v-else class="status-pill status-check">Check VIN</span>
            </div>

            <dl class="recall-meta">
              <div v-if="recall.manufacturer_recall_number">
                <dt>Manufacturer number</dt>
                <dd>{{ recall.manufacturer_recall_number }}</dd>
              </div>
              <div v-if="recall.component">
                <dt>Component</dt>
                <dd>{{ recall.component }}</dd>
              </div>
              <div v-if="recall.report_date">
                <dt>Reported</dt>
                <dd>{{ recall.report_date }}</dd>
              </div>
            </dl>

            <p v-if="recall.summary" class="recall-summary-text">{{ recall.summary }}</p>

            <details v-if="recall.consequence || recall.remedy || recall.notes" class="recall-details">
              <summary>View consequence, remedy and notes</summary>
              <div v-if="recall.consequence">
                <strong>Consequence</strong>
                <p>{{ recall.consequence }}</p>
              </div>
              <div v-if="recall.remedy">
                <strong>Remedy</strong>
                <p>{{ recall.remedy }}</p>
              </div>
              <div v-if="recall.notes">
                <strong>Notes</strong>
                <p>{{ recall.notes }}</p>
              </div>
            </details>
          </article>
        </div>

        <div v-else class="empty-state">
          <span class="empty-icon" aria-hidden="true">✓</span>
          <div>
            <h3>No NHTSA campaigns found</h3>
            <p>There are no model-level recall campaigns in this lookup.</p>
          </div>
        </div>
      </section>

      <p v-if="data.errors && Object.keys(data.errors).length" class="data-note">
        Some NHTSA data could not be loaded. Try refreshing to check again.
      </p>
    </div>
  </main>
</template>

<script setup>
import { API_BASE, useApiClient } from '../utils/auth'
import { provideVehicleAccess } from '../utils/vehicleAccess'
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { showToast } from '../components/Toast.vue'
import NavBar from '../components/NavBar.vue'
import { safeExternalUrl } from '../utils/url'

const route = useRoute()
const carId = route.params.carId
const fetch = useApiClient()
const car = ref(null)
const { canView } = provideVehicleAccess(car)

const data = ref(null)
const loading = ref(true)
const loadError = ref('')

const decode = computed(() => data.value?.decode ?? null)
const recalls = computed(() => data.value?.recalls ?? [])
const selectedRating = computed(() => data.value?.ratings?.selected ?? null)
const recallLookupUrl = computed(() => safeExternalUrl(data.value?.recall_lookup_url))
const vin = computed(() => data.value?.vin ?? '')
const decodedFields = computed(() => decode.value?.fields ?? {})
const vehicleName = computed(() => {
  const make = decodedFields.value.Make || ''
  const model = decodedFields.value.Model || ''
  return `${make} ${model}`.trim() || 'Vehicle safety'
})
const vehicleYear = computed(() => decodedFields.value['Model Year'] || 'N/A')
const overallRating = computed(() => selectedRating.value?.OverallRating || 'Not rated')
const savedVehicleName = computed(() => [car.value?.year, car.value?.make, car.value?.model].filter(Boolean).join(' '))
const vinMismatch = computed(() => {
  const decodedMake = decode.value?.make || decodedFields.value.Make
  const decodedModel = decode.value?.model || decodedFields.value.Model
  const decodedYear = decode.value?.year || decodedFields.value['Model Year']
  if (!car.value || !decodedMake || !decodedModel || !decodedYear) return false
  return String(car.value.year) !== String(decodedYear) ||
    normalizeVehicleName(car.value.make) !== normalizeVehicleName(decodedMake) ||
    normalizeVehicleName(car.value.model) !== normalizeVehicleName(decodedModel)
})

const vehicleIdentity = computed(() => vehicleFields(['Model Year', 'Make', 'Model', 'Body Class', 'Vehicle Type']))
const vehicleSpecificationGroups = computed(() => [
  { title: 'Powertrain', fields: vehicleFields(['Engine Model', 'Engine Configuration', 'Displacement (L)', 'Fuel Type - Primary', 'Drive Type', 'Transmission Style', 'Transmission Speeds']) },
  { title: 'Built by', fields: vehicleFields(['Manufacturer Name', 'Plant Country', 'Doors']) }
].filter(group => group.fields.length))

const RATING_LABELS = [
  'OverallRating',
  'OverallFrontCrashRating',
  'FrontCrashDriversideRating',
  'FrontCrashPassengersideRating',
  'OverallSideCrashRating',
  'SideCrashDriversideRating',
  'SideCrashPassengersideRating',
  'RolloverRating',
]

const ratingFields = computed(() => RATING_LABELS
  .filter(label => selectedRating.value?.[label] !== undefined && selectedRating.value?.[label] !== null && selectedRating.value?.[label] !== '')
  .map(label => ({ label: formatRatingLabel(label), value: selectedRating.value[label] })))

function formatRatingLabel(label) {
  return label.replace(/([A-Z])/g, ' $1').trim()
}

function vehicleFields(labels) {
  return labels
    .filter(label => decodedFields.value[label])
    .map(label => ({ label, value: decodedFields.value[label] }))
}

function normalizeVehicleName(value) {
  return String(value || '').trim().toLowerCase().replace(/[^a-z0-9]/g, '')
}

onMounted(loadData)

async function loadData() {
  loading.value = true
  loadError.value = ''
  car.value = null
  data.value = null
  try {
    const vehicleResponse = await fetch(`${API_BASE}/cars/${carId}`)
    if (!vehicleResponse.ok) throw new Error('Unable to load vehicle access.')
    car.value = await vehicleResponse.json()
    if (!canView('vehicle')) throw new Error('Vehicle access is unavailable.')
    const response = await fetch(`${API_BASE}/cars/${carId}/nhtsa/`)
    if (!response.ok) {
      const body = await response.json().catch(() => ({}))
      throw new Error(body.detail || 'Failed to fetch NHTSA data')
    }
    data.value = await response.json()
  } catch (err) {
    loadError.value = err.message || 'Failed to fetch NHTSA data'
    showToast('Failed to fetch NHTSA data', 'error')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.nhtsa-page {
  display: flex;
  flex-direction: column;
  gap: 34px;
  width: min(100% - 40px, 1200px);
  min-height: calc(100vh - 70px);
  margin: 0 auto;
  padding: clamp(40px, 7vw, 72px) 0 80px;
}

.page-header,
.content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.title-row,
.section-heading,
.recall-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.context,
.section-kicker,
.campaign-label {
  color: var(--gb-accent);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.page-header h1 {
  margin-top: 4px;
  color: var(--gb-heading);
  font-size: clamp(1.5rem, 3vw, 1.75rem);
  font-weight: 720;
  letter-spacing: -0.025em;
  line-height: 1.15;
}

.page-header p {
  margin-top: 5px;
  color: var(--gb-text-muted);
  font-size: 0.9rem;
}

.refresh-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--gb-border-strong);
  border-radius: 9px;
  padding: 10px 14px;
  background: transparent;
  color: var(--gb-accent);
  font-weight: 700;
  cursor: pointer;
  transition: background 150ms, border-color 150ms, transform 100ms;
}

.refresh-button:hover:not(:disabled) {
  border-color: var(--gb-accent);
  background: rgba(179, 199, 255, 0.08);
}

.refresh-button:active:not(:disabled) { transform: translateY(1px); }
.refresh-button:disabled { cursor: wait; opacity: 0.6; }
.refresh-button:focus-visible,
.lookup-link:focus-visible,
summary:focus-visible { outline: 3px solid rgba(179, 199, 255, 0.25); outline-offset: 3px; }

.refresh-button svg {
  width: 17px;
  height: 17px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.7;
}

.overview {
  display: grid;
  grid-template-columns: minmax(250px, 1.15fr) minmax(430px, 1.85fr);
  overflow: hidden;
  border: 1px solid rgba(179, 199, 255, 0.1);
  border-radius: 12px;
  background: #1c2128;
}

.overview-lead {
  padding: 20px;
  border-right: 1px solid rgba(179, 199, 255, 0.1);
}

.overview-lead > span,
dt,
.rating-card > span {
  color: var(--gb-text-muted);
  font-size: 0.74rem;
}

.overview-lead strong {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-top: 2px;
  color: var(--gb-heading);
  font-size: 1.55rem;
  font-weight: 700;
}

.overview-lead strong.has-recalls { color: #f0c983; }

.overview-lead strong small {
  color: var(--gb-text-muted);
  font-size: 0.82rem;
  font-weight: 500;
}

.overview-lead p {
  margin-top: 5px;
  color: var(--gb-text-muted);
  font-size: 0.78rem;
  line-height: 1.45;
}

.overview dl {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.overview dl div {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 16px 20px;
}

.overview dl div + div { border-left: 1px solid rgba(179, 199, 255, 0.1); }

.vin-mismatch {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 14px 18px;
  border: 1px solid rgba(240, 201, 131, 0.35);
  border-radius: 12px;
  background: rgba(240, 201, 131, 0.08);
  color: #f0c983;
  font-size: 0.84rem;
  line-height: 1.45;
}

.vin-mismatch strong { color: #f7d89d; font-size: 0.9rem; }

dd {
  margin-top: 2px;
  color: var(--gb-heading);
  font-size: 1.08rem;
  font-weight: 650;
}

dd small {
  display: block;
  margin-top: 1px;
  color: var(--gb-text-muted);
  font-size: 0.7rem;
  font-weight: 500;
}

.board-message {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: 300px;
  border: 1px dashed var(--gb-border);
  border-radius: 17px;
  color: var(--gb-text-muted);
}

.loader {
  width: 18px;
  height: 18px;
  border: 2px solid var(--gb-border-strong);
  border-top-color: var(--gb-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.error-message { flex-direction: column; }
.error-message span { max-width: 620px; color: #c78d91; font-size: 0.82rem; text-align: center; }

.error-message button {
  border: 1px solid var(--gb-border-strong);
  border-radius: 999px;
  padding: 8px 14px;
  background: transparent;
  color: var(--gb-accent);
  cursor: pointer;
}

.section-heading { align-items: end; }
.section-heading h2 { margin-top: 3px; color: var(--gb-heading); font-size: 1.35rem; font-weight: 650; letter-spacing: -0.02em; }
.section-count { color: var(--gb-text-muted); font-size: 0.78rem; }

.lookup-link {
  padding: 7px 10px;
  border: 1px solid var(--gb-border-strong);
  border-radius: 8px;
  color: var(--gb-accent);
  font-size: 0.8rem;
  font-weight: 650;
}

.identity-strip {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 1px;
  overflow: hidden;
  border: 1px solid var(--gb-border);
  border-radius: 12px;
  background: var(--gb-border);
}

.identity-strip div { min-width: 0; padding: 17px 18px; background: var(--gb-surface); }
.identity-strip dd { overflow: hidden; margin-top: 4px; text-overflow: ellipsis; white-space: nowrap; }

.specification-groups {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 14px;
}

.specification-group {
  padding: 18px;
  border: 1px solid var(--gb-border);
  border-radius: 12px;
  background: var(--gb-surface);
}

.specification-group h3 { color: var(--gb-heading); font-size: 0.9rem; font-weight: 650; }
.specification-group dl { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px 12px; margin-top: 16px; }
.specification-group dd { overflow-wrap: anywhere; margin-top: 3px; font-size: 0.9rem; }

.rating-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
}

.rating-card {
  display: flex;
  flex-direction: column;
  gap: 7px;
  padding: 17px;
  border: 1px solid var(--gb-border);
  border-radius: 12px;
  background: var(--gb-surface);
}

.rating-card strong { color: var(--gb-heading); font-size: 1.65rem; font-weight: 700; line-height: 1; }
.rating-card strong.unrated { color: var(--gb-text-muted); }

.recall-list { display: flex; flex-direction: column; gap: 12px; }

.recall-item {
  padding: 20px;
  border: 1px solid var(--gb-border);
  border-radius: 12px;
  background: var(--gb-surface);
}

.recall-summary { align-items: start; }
.recall-identity { min-width: 0; }
.recall-identity h3 { margin-top: 5px; color: var(--gb-heading); font-size: 1rem; font-weight: 650; }

.status-pill {
  flex-shrink: 0;
  padding: 5px 9px;
  border: 1px solid rgba(240, 201, 131, 0.28);
  border-radius: 999px;
  background: rgba(240, 201, 131, 0.08);
  color: #f0c983;
  font-size: 0.7rem;
  font-weight: 700;
}

.status-check { border-color: rgba(179, 199, 255, 0.22); background: rgba(179, 199, 255, 0.07); color: var(--gb-accent); }

.recall-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid rgba(179, 199, 255, 0.08);
}

.recall-meta div { min-width: 120px; }
.recall-meta dd { margin-top: 2px; color: var(--gb-text); font-size: 0.82rem; font-weight: 500; }

.recall-summary-text,
.recall-details p { color: var(--gb-text-muted); font-size: 0.88rem; line-height: 1.55; }
.recall-summary-text { margin-top: 16px; }

.recall-details { margin-top: 16px; border-top: 1px solid rgba(179, 199, 255, 0.08); padding-top: 13px; }
.recall-details summary { color: var(--gb-accent); font-size: 0.8rem; font-weight: 650; cursor: pointer; }
.recall-details > div { margin-top: 14px; }
.recall-details strong { color: var(--gb-heading); font-size: 0.78rem; font-weight: 650; }
.recall-details p { margin-top: 3px; }

.empty-state {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 22px 20px;
  border: 1px dashed var(--gb-border-strong);
  border-radius: 12px;
}

.empty-icon {
  display: grid;
  width: 30px;
  height: 30px;
  flex-shrink: 0;
  place-items: center;
  border-radius: 50%;
  background: rgba(110, 199, 158, 0.12);
  color: #8bd2ac;
  font-weight: 700;
}

.empty-state h3 { color: var(--gb-heading); font-size: 0.95rem; font-weight: 650; }
.empty-state p { margin-top: 2px; color: var(--gb-text-muted); font-size: 0.82rem; }
.data-note { color: var(--gb-text-muted); font-size: 0.8rem; }

@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 820px) {
  .overview { grid-template-columns: 1fr; }
  .overview-lead { border-right: 0; border-bottom: 1px solid rgba(179, 199, 255, 0.1); }
}

@media (max-width: 700px) {
  .nhtsa-page { width: min(100% - 28px, 1200px); padding-top: 36px; }
  .identity-strip { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}

@media (max-width: 540px) {
  .title-row { align-items: flex-start; }
  .refresh-button { padding: 10px 12px; white-space: nowrap; }
  .overview dl { grid-template-columns: 1fr 1fr; }
  .overview dl div { padding: 14px 16px; }
  .overview dl div + div { border-left: 0; }
  .overview dl div:nth-child(2) { border-left: 1px solid rgba(179, 199, 255, 0.1); }
  .overview dl div:last-child { grid-column: 1 / -1; border-top: 1px solid rgba(179, 199, 255, 0.1); }
  .section-heading { align-items: flex-start; flex-direction: column; gap: 8px; }
  .lookup-link { align-self: flex-start; }
  .recall-summary { gap: 12px; }
  .recall-item { padding: 16px; }
  .identity-strip { grid-template-columns: 1fr 1fr; }
  .specification-groups { grid-template-columns: 1fr; }
}
</style>
