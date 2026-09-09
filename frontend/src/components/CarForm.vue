<template>
  <div class="car-form">
    <button type="button" class="close-button" aria-label="Close form" @click="emit('close')">
      &times;
    </button>

    <h2>Add a Car</h2>

    <div class="method-picker" role="tablist" aria-label="How to add a car">
      <button type="button" :class="{ active: method === 'manual' }" @click="method = 'manual'">Enter manually</button>
      <button type="button" :class="{ active: method === 'carfax' }" @click="method = 'carfax'">Import CARFAX</button>
    </div>

    <form v-if="method === 'manual'" class="form-section" novalidate @submit.prevent="handleCreateCar">
      <div class="form-layout">
        <div class="form-left">
          <div class="form-group">
            <label>Year</label>
            <input v-model="year" inputmode="numeric" placeholder="e.g. 2020" :aria-invalid="Boolean(visibleError('year'))" aria-describedby="year-error" @blur="markTouched('year')" @input="clearServerError('year')" />
            <small v-if="visibleError('year')" id="year-error" class="field-error">{{ visibleError('year') }}</small>
          </div>

          <div class="form-group">
            <label>Make</label>
            <input v-model.trim="make" maxlength="100" placeholder="e.g. Honda" :aria-invalid="Boolean(visibleError('make'))" aria-describedby="make-error" @blur="markTouched('make')" @input="clearServerError('make')" />
            <small v-if="visibleError('make')" id="make-error" class="field-error">{{ visibleError('make') }}</small>
          </div>

          <div class="form-group">
            <label>Model</label>
            <input v-model.trim="model" maxlength="100" placeholder="e.g. Civic" :aria-invalid="Boolean(visibleError('model'))" aria-describedby="model-error" @blur="markTouched('model')" @input="clearServerError('model')" />
            <small v-if="visibleError('model')" id="model-error" class="field-error">{{ visibleError('model') }}</small>
          </div>

          <div class="form-group">
            <label>License Plate</label>
            <input v-model="licensePlate" maxlength="20" placeholder="e.g. ABC-1234" :aria-invalid="Boolean(visibleError('licensePlate'))" aria-describedby="license-plate-error" @blur="markTouched('licensePlate')" @input="clearServerError('licensePlate')" />
            <small v-if="visibleError('licensePlate')" id="license-plate-error" class="field-error">{{ visibleError('licensePlate') }}</small>
          </div>
        </div>

        <div class="form-right">
          <fieldset class="fuel-type-picker">
            <legend>Fuel Type</legend>
            <div class="fuel-options">
              <label class="fuel-option" :class="{ active: fuelType === 'electric' }">
                <input v-model="fuelType" type="radio" name="fuel-type" value="electric" />
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="m13 2-8 12h7l-1 8 8-12h-7l1-8Z" />
                </svg>
                <span>Electric</span>
              </label>
              <label class="fuel-option" :class="{ active: fuelType === 'gas' }">
                <input v-model="fuelType" type="radio" name="fuel-type" value="gas" />
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M6 21V4a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v17M5 21h13M8 6h7v5H8V6Zm9 2h2l2 2v7a2 2 0 0 1-4 0v-3" />
                </svg>
                <span>Gasoline</span>
              </label>
              <label class="fuel-option" :class="{ active: fuelType === 'diesel' }">
                <input v-model="fuelType" type="radio" name="fuel-type" value="diesel" />
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M12 3s6 7 6 12a6 6 0 0 1-12 0c0-5 6-12 6-12Zm-3 12a3 3 0 0 0 3 3" />
                </svg>
                <span>Diesel</span>
              </label>
            </div>
          </fieldset>

        </div>
      </div>

      <div class="advanced-section" :class="{ expanded: showAdvanced, invalid: hasVisibleAdvancedErrors }">
        <button
          type="button"
          class="advanced-toggle"
          :aria-expanded="showAdvanced"
          aria-controls="advanced-car-options"
          @click="showAdvanced = !showAdvanced"
        >
          <span>Advanced Options</span>
          <span v-if="hasVisibleAdvancedErrors" class="advanced-error-summary">Needs attention</span>
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d="m6 8 4 4 4-4" /></svg>
        </button>

        <div v-show="showAdvanced" id="advanced-car-options" class="advanced-options">
          <div class="form-group">
            <label>Purchased Date</label>
            <input v-model="purchasedDate" type="date" :max="today" :aria-invalid="Boolean(visibleError('purchasedDate'))" aria-describedby="purchased-date-error" @blur="markTouched('purchasedDate')" @input="clearServerError('purchasedDate')" />
            <small v-if="visibleError('purchasedDate')" id="purchased-date-error" class="field-error">{{ visibleError('purchasedDate') }}</small>
          </div>

          <div class="form-group">
            <label>Purchased Price</label>
            <input
              v-model="purchasedPrice"
              inputmode="decimal"
              placeholder="e.g. 25000.00"
              :aria-invalid="Boolean(visibleError('purchasedPrice'))"
              aria-describedby="purchased-price-error"
              @blur="markTouched('purchasedPrice'); formatPurchasedPrice()"
              @input="clearServerError('purchasedPrice')"
            />
            <small v-if="visibleError('purchasedPrice')" id="purchased-price-error" class="field-error">{{ visibleError('purchasedPrice') }}</small>
          </div>

          <div class="form-group">
            <label>VIN</label>
            <input
              :value="vin"
              maxlength="17"
              placeholder="e.g. 1HGBH41JXMN109186"
              autocapitalize="characters"
              autocomplete="off"
              spellcheck="false"
              :aria-invalid="Boolean(visibleError('vin'))"
              aria-describedby="vin-validation"
              @input="handleVinInput"
              @blur="markTouched('vin')"
            />
            <small v-if="visibleError('vin')" id="vin-validation" class="field-error">{{ visibleError('vin') }}</small>
            <small v-else-if="vin && touched.vin" id="vin-validation" class="field-valid">Valid VIN</small>
            <div v-if="vinMismatch" class="vin-warning" role="alert">
              <strong>VIN details do not match this vehicle.</strong>
              <span>VIN decodes to {{ decodedVehicleName }}. Check the year, make, model, and VIN before creating the car.</span>
            </div>
          </div>

          <div class="form-group">
            <label>Mileage</label>
            <input :value="mileage" inputmode="numeric" placeholder="50000" :aria-invalid="Boolean(visibleError('mileage'))" aria-describedby="mileage-error" @blur="markTouched('mileage')" @input="handleMileageInput" />
            <small v-if="visibleError('mileage')" id="mileage-error" class="field-error">{{ visibleError('mileage') }}</small>
          </div>
        </div>
      </div>

      <div class="form-actions">
        <button type="button" class="cancel-button" @click="emit('close')">Cancel</button>
        <button type="submit" class="submit-button">Create Car</button>
      </div>
    </form>
    <CarfaxCarImport v-else :api-base="apiBase" @created="handleCarfaxCreated" @cancel="method = 'manual'" />
  </div>
</template>

<script setup>
import { useApiClient } from '../utils/auth'
const fetch = useApiClient()
import { computed, nextTick, reactive, ref } from 'vue'
import { showToast } from './Toast.vue'
import CarfaxCarImport from './CarfaxCarImport.vue'
import { sanitizeWholeNumberInput } from '../utils/numericInput'

const props = defineProps({
  apiBase: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['created', 'close'])

const make = ref('')
const model = ref('')
const year = ref('')
const mileage = ref('')
const method = ref('manual')

const showAdvanced = ref(false)

const vin = ref('')
const licensePlate = ref('')
const fuelType = ref('gas')
const purchasedDate = ref('')
const purchasedPrice = ref('')
const maxVehicleYear = new Date().getFullYear() + 1
const now = new Date()
const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
const touched = reactive({})
const submitted = ref(false)
const serverErrors = ref({})
const decodedVin = ref(null)
let vinLookupController = null

const yearNumber = computed(() => Number(year.value))
const mileageNumber = computed(() => Number(mileage.value))
const purchasedPriceNumber = computed(() => Number(purchasedPrice.value))
const validationErrors = computed(() => {
  const errors = {
    year: '', make: '', model: '', licensePlate: '', purchasedDate: '',
    purchasedPrice: '', vin: '', mileage: ''
  }
  if (!year.value) errors.year = 'Year is required'
  else if (!Number.isInteger(yearNumber.value) || yearNumber.value < 1886 || yearNumber.value > maxVehicleYear) errors.year = `Enter a year from 1886 to ${maxVehicleYear}`
  if (!make.value.trim()) errors.make = 'Make is required'
  if (!model.value.trim()) errors.model = 'Model is required'
  if (licensePlate.value.trim().length > 20) errors.licensePlate = 'License plate must be 20 characters or fewer'
  if (purchasedDate.value && purchasedDate.value > today) errors.purchasedDate = 'Purchase date cannot be in the future'
  if (purchasedPrice.value !== '' && !Number.isFinite(purchasedPriceNumber.value)) errors.purchasedPrice = 'Enter a valid price'
  if (mileage.value !== '' && (!Number.isInteger(mileageNumber.value) || mileageNumber.value < 0)) errors.mileage = 'Enter a non-negative whole number'
  if (!vin.value) return errors
  if (vin.value.length !== 17) errors.vin = `VIN must be 17 characters (${vin.value.length}/17)`
  else if (!isValidVinChecksum(vin.value)) errors.vin = 'VIN check digit does not match'
  return errors
})

const isFormValid = computed(() => {
  return Object.values(validationErrors.value).every(error => !error)
})
const advancedFields = ['purchasedDate', 'purchasedPrice', 'vin', 'mileage']
const hasVisibleAdvancedErrors = computed(() => advancedFields.some(field => visibleError(field)))
const decodedVehicleName = computed(() => {
  const fields = decodedVin.value?.fields ?? {}
  return [fields['Model Year'], fields.Make, fields.Model].filter(Boolean).join(' ')
})
const vinMismatch = computed(() => {
  if (!decodedVin.value || !decodedVehicleName.value) return false
  return String(decodedVin.value.year) !== String(yearNumber.value) ||
    normalizeVehicleName(decodedVin.value.make) !== normalizeVehicleName(make.value) ||
    normalizeVehicleName(decodedVin.value.model) !== normalizeVehicleName(model.value)
})

async function handleCreateCar() {
  submitted.value = true
  serverErrors.value = {}
  if (!isFormValid.value) {
    if (advancedFields.some(field => validationErrors.value[field])) showAdvanced.value = true
    await focusFirstInvalidField()
    showToast('Please fill in all required fields correctly', 'warning')
    return
  }

  const payload = {
    make: make.value.trim(),
    model: model.value.trim(),
    year: yearNumber.value,
    fuel_type: fuelType.value
  }

  if (mileage.value !== '') payload.mileage = mileageNumber.value
  if (vin.value) payload.vin = vin.value
  if (licensePlate.value.trim()) payload.license_plate = licensePlate.value.trim()
  if (purchasedDate.value) payload.purchased_date = purchasedDate.value
  if (purchasedPrice.value !== '') payload.purchased_price = Number(purchasedPrice.value)

  try {
    const response = await fetch(`${props.apiBase}/cars/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })

    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      if (response.status === 422 && Array.isArray(data.detail)) {
        applyServerErrors(data.detail)
        if (advancedFields.some(field => serverErrors.value[field])) showAdvanced.value = true
        await focusFirstInvalidField()
      }
      showToast(typeof data.detail === 'string' ? data.detail : 'Please correct the highlighted fields', 'error')
      return
    }

    const data = await response.json()
    emit('created', data)

    make.value = ''
    model.value = ''
    year.value = ''
    mileage.value = ''
    vin.value = ''
    licensePlate.value = ''
    fuelType.value = 'gas'
    purchasedDate.value = ''
    purchasedPrice.value = ''
    showToast('Car created successfully', 'success')
  } catch (error) {
    if (error.name !== 'AbortError') showToast('Failed to create car', 'error')
  }
}

function handleVinInput(event) {
  vin.value = event.target.value
    .toUpperCase()
    .replace(/[^A-HJ-NPR-Z0-9]/g, '')
    .slice(0, 17)
  event.target.value = vin.value
  decodedVin.value = null
  vinLookupController?.abort()
  clearServerError('vin')
}

function handleMileageInput(event) {
  mileage.value = sanitizeWholeNumberInput(event)
  clearServerError('mileage')
}

function formatPurchasedPrice() {
  if (purchasedPrice.value === '') return
  const value = Number(purchasedPrice.value)
  if (Number.isFinite(value)) purchasedPrice.value = value.toFixed(2)
}

async function markTouched(field) {
  touched[field] = true
  if (field === 'vin' && vin.value.length === 17 && isValidVinChecksum(vin.value)) await decodeEnteredVin()
}

async function decodeEnteredVin() {
  vinLookupController?.abort()
  const controller = new AbortController()
  vinLookupController = controller
  try {
    const response = await fetch(`${props.apiBase}/nhtsa/decode/${vin.value}`, { signal: controller.signal })
    if (!response.ok) return
    if (vinLookupController === controller) decodedVin.value = await response.json()
  } catch (error) {
    if (error.name !== 'AbortError') decodedVin.value = null
  }
}

function clearServerError(field) {
  if (!serverErrors.value[field]) return
  const errors = { ...serverErrors.value }
  delete errors[field]
  serverErrors.value = errors
}

function visibleError(field) {
  if (!submitted.value && !touched[field]) return ''
  return serverErrors.value[field] || validationErrors.value[field]
}

function normalizeVehicleName(value) {
  return String(value || '').trim().toLowerCase().replace(/[^a-z0-9]/g, '')
}

function applyServerErrors(details) {
  const fieldNames = {
    license_plate: 'licensePlate', purchased_date: 'purchasedDate',
    purchased_price: 'purchasedPrice'
  }
  serverErrors.value = Object.fromEntries(details.map(detail => {
    const serverField = detail.loc?.at(-1)
    return [fieldNames[serverField] || serverField, String(detail.msg || 'Invalid value').replace(/^Value error, /, '')]
  }).filter(([field]) => field in validationErrors.value))
}

async function focusFirstInvalidField() {
  await nextTick()
  document.querySelector('.car-form [aria-invalid="true"]')?.focus()
}

function isValidVinChecksum(value) {
  const letterValues = {
    A: 1, B: 2, C: 3, D: 4, E: 5, F: 6, G: 7, H: 8,
    J: 1, K: 2, L: 3, M: 4, N: 5, P: 7, R: 9,
    S: 2, T: 3, U: 4, V: 5, W: 6, X: 7, Y: 8, Z: 9
  }
  const weights = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]
  const total = [...value].reduce((sum, character, index) => {
    const characterValue = /\d/.test(character) ? Number(character) : letterValues[character]
    return sum + characterValue * weights[index]
  }, 0)
  const checkDigit = total % 11 === 10 ? 'X' : String(total % 11)
  return value[8] === checkDigit
}

function handleCarfaxCreated(result) {
  showToast(`Car added with ${result.created} CARFAX service records`, 'success')
  emit('created', result.car)
}
</script>

<style scoped>
.car-form {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 20px;
  border: 1px solid var(--gb-border);
  padding: 30px;
  border-radius: 16px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.3);
  width: 100%;
  max-width: 900px;
  background: var(--gb-surface);
}

.car-form h2 {
  margin: 0;
  margin-top: -10px;
  text-align: left;
  font-size: 1.5rem;
  color: var(--gb-heading);
}

.method-picker {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
  padding: 4px;
  border: 1px solid var(--gb-border);
  border-radius: 12px;
  background: var(--gb-background-deep);
}

.method-picker button {
  border: 0;
  border-radius: 8px;
  padding: 10px 14px;
  background: transparent;
  color: var(--gb-text-muted);
  font-weight: 700;
  cursor: pointer;
}

.method-picker button.active {
  background: rgba(179, 199, 255, 0.12);
  color: var(--gb-accent);
}

.close-button {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 4px;
  background: transparent;
  color: var(--gb-text-muted);
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-button:hover {
  color: var(--gb-heading);
  background-color: rgba(179, 199, 255, 0.08);
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
}

.form-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
  width: 100%;
}

.form-left {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-right {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--gb-text);
}

.fuel-type-picker {
  min-width: 0;
  margin: 0;
  padding: 0;
  border: 0;
}

.fuel-type-picker legend {
  margin-bottom: 8px;
  padding: 0;
  color: var(--gb-text);
  font-size: 0.95rem;
  font-weight: 500;
}

.fuel-options {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.fuel-option {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  min-width: 0;
  padding: 10px 8px;
  border: 1px solid var(--gb-border);
  border-radius: 8px;
  background: var(--gb-background-deep);
  color: var(--gb-text-muted);
  font-size: 0.86rem;
  cursor: pointer;
  transition: border-color 0.2s ease, background-color 0.2s ease, color 0.2s ease;
}

.fuel-option:hover {
  border-color: var(--gb-border-strong);
  color: var(--gb-heading);
}

.fuel-option.active {
  border-color: var(--gb-accent);
  background: rgba(179, 199, 255, 0.12);
  color: var(--gb-accent);
}

.fuel-option:focus-within {
  outline: none;
  border-color: var(--gb-accent);
  box-shadow: 0 0 0 3px rgba(179, 199, 255, 0.1);
}

.fuel-option input {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}

.fuel-option svg {
  width: 17px;
  height: 17px;
  flex: 0 0 auto;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.7;
}

.form-group input,
.form-group select {
  padding: 10px 12px;
  border: 1px solid var(--gb-border);
  border-radius: 8px;
  background-color: var(--gb-background-deep);
  color: var(--gb-heading);
  font-size: 0.95rem;
}

.form-group input::placeholder {
  color: #727d90;
}

.field-error,
.field-valid {
  font-size: 0.78rem;
}

.field-error {
  color: #e49a9f;
}

.field-valid {
  color: #79c69e;
}

.vin-warning {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 10px 12px;
  border: 1px solid rgba(240, 201, 131, 0.38);
  border-radius: 8px;
  background: rgba(240, 201, 131, 0.08);
  color: #f0c983;
  font-size: 0.78rem;
  line-height: 1.4;
}

.vin-warning strong { font-size: 0.8rem; }

.form-group input[aria-invalid="true"] {
  border-color: #a95861;
  box-shadow: 0 0 0 3px rgba(169, 88, 97, 0.14);
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--gb-accent);
  box-shadow: 0 0 0 3px rgba(179, 199, 255, 0.1);
}

.form-group input[aria-invalid="true"]:focus {
  border-color: #a95861;
  box-shadow: 0 0 0 3px rgba(169, 88, 97, 0.14);
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 10px;
  padding-top: 20px;
  border-top: 1px solid var(--gb-border);
}

.submit-button,
.cancel-button {
  padding: 10px 24px;
  border: none;
  border-radius: 999px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.submit-button {
  background-color: var(--gb-accent);
  color: #141820;
}

.submit-button:hover {
  background-color: var(--gb-accent-hover);
}

.cancel-button {
  border: 1px solid var(--gb-border);
  background-color: transparent;
  color: var(--gb-text);
}

.cancel-button:hover {
  background-color: var(--gb-surface-hover);
}

.advanced-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 12px 14px;
  border: 0;
  background-color: transparent;
  color: var(--gb-text);
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: color 0.2s ease, background-color 0.2s ease;
}

.advanced-toggle:hover {
  background-color: rgba(179, 199, 255, 0.08);
  color: var(--gb-accent);
}

.advanced-toggle:focus-visible {
  outline: 2px solid var(--gb-accent);
  outline-offset: -2px;
}

.advanced-toggle svg {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
  transition: transform 0.2s ease;
}

.advanced-section {
  overflow: hidden;
  border: 1px solid var(--gb-border-strong);
  border-radius: 10px;
}

.advanced-section.invalid {
  border-color: #a95861;
}

.advanced-error-summary {
  margin-left: auto;
  color: #e49a9f;
  font-size: 0.78rem;
  font-weight: 600;
}

.advanced-section.expanded .advanced-toggle svg {
  transform: rotate(180deg);
}

.advanced-options {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 15px;
  padding: 15px;
  border-top: 1px solid var(--gb-border);
  background-color: rgba(179, 199, 255, 0.04);
}

@media (max-width: 640px) {
  .form-layout {
    grid-template-columns: 1fr;
  }

  .fuel-option {
    padding-inline: 6px;
    font-size: 0.82rem;
  }

  .advanced-options {
    grid-template-columns: 1fr;
  }
}
</style>
