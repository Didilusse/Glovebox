<template>
  <VehicleDialog v-if="allowed" class="vehicle-edit-dialog" title="Edit vehicle" @close="$emit('close')">
    <div class="vehicle-edit">
      <p class="form-intro">Update the details and history for this vehicle.</p>
      <p v-if="error" class="form-error" role="alert">{{ error }}</p>
      <form novalidate @submit.prevent="save">
        <fieldset class="form-fields" :disabled="busy">
          <div class="form-layout">
            <div class="form-column">
              <div class="form-group"><label for="edit-make">Make</label><input id="edit-make" v-model.trim="draft.make" required maxlength="100" /></div>
              <div class="form-group"><label for="edit-model">Model</label><input id="edit-model" v-model.trim="draft.model" required maxlength="100" /></div>
              <div class="form-group"><label for="edit-year">Year</label><input id="edit-year" v-model="draft.year" inputmode="numeric" required /></div>
              <div class="form-group"><label for="edit-license">License Plate</label><input id="edit-license" v-model.trim="draft.license_plate" maxlength="20" placeholder="e.g. ABC-1234" /></div>
            </div>

            <div class="form-column">
              <div class="form-group"><label for="edit-mileage">Mileage</label><input id="edit-mileage" :value="draft.mileage" inputmode="numeric" @input="draft.mileage = sanitizeWholeNumberInput($event)" /></div>
              <div class="form-group"><label for="edit-initial-mileage">Initial Mileage</label><input id="edit-initial-mileage" :value="draft.initial_mileage" inputmode="numeric" @input="draft.initial_mileage = sanitizeWholeNumberInput($event)" /></div>
              <div class="fuel-type-picker">
                <span>Fuel Type</span>
                <div class="fuel-options">
                  <label v-for="option in fuelOptions" :key="option.value" class="fuel-option" :class="{ active: draft.fuel_type === option.value }">
                    <input v-model="draft.fuel_type" type="radio" name="edit-fuel-type" :value="option.value" />
                    <span>{{ option.label }}</span>
                  </label>
                </div>
              </div>
            </div>
          </div>

          <div class="advanced-section" :class="{ expanded: showAdvanced }">
            <button type="button" class="advanced-toggle" :aria-expanded="showAdvanced" aria-controls="advanced-vehicle-edit" @click="showAdvanced = !showAdvanced">
              <span>Advanced Options</span>
              <svg viewBox="0 0 20 20" aria-hidden="true"><path d="m6 8 4 4 4-4" /></svg>
            </button>
            <div v-show="showAdvanced" id="advanced-vehicle-edit" class="advanced-options">
              <div class="form-group"><label for="edit-purchase-date">Purchased Date</label><input id="edit-purchase-date" v-model="draft.purchased_date" type="date" :max="today" /></div>
              <div class="form-group"><label for="edit-purchase-price">Purchased Price</label><input id="edit-purchase-price" v-model="draft.purchased_price" inputmode="decimal" placeholder="e.g. 25000.00" data-currency @blur="formatPurchasedPrice" /></div>
              <div class="form-group wide"><label for="edit-vin">VIN</label><input id="edit-vin" v-model.trim="draft.vin" maxlength="17" placeholder="e.g. 1HGBH41JXMN109186" /></div>
            </div>
          </div>

          <div class="form-actions">
            <button type="button" class="cancel-button" @click="emit('close')">Cancel</button>
            <button type="submit" class="submit-button">{{ busy ? 'Saving...' : 'Save Vehicle' }}</button>
          </div>
        </fieldset>
      </form>
    </div>
  </VehicleDialog>
</template>

<script setup>
import { computed, ref } from 'vue'
import { auth, useApiRequest } from '../utils/auth'
import { canAccess } from '../utils/vehicleAccess'
import VehicleDialog from './VehicleDialog.vue'
import { sanitizeWholeNumberInput } from '../utils/numericInput'
const props = defineProps({ car: { type: Object, required: true } })
const emit = defineEmits(['close', 'updated'])
const version = auth.version
const allowed = computed(() => auth.version === version && canAccess(props.car, 'vehicle', true))
const request = useApiRequest()
const fuelOptions = [
  { value: 'electric', label: 'Electric' },
  { value: 'gas', label: 'Gasoline' },
  { value: 'diesel', label: 'Diesel' },
  { value: '', label: 'Not specified' }
]
const fields = ['make', 'model', 'year', 'mileage', 'initial_mileage', 'vin', 'license_plate', 'fuel_type', 'purchased_date', 'purchased_price']
const draft = ref(Object.fromEntries(fields.map(key => [
  key,
  key === 'purchased_price' ? priceForDisplay(props.car[key]) : (props.car[key] ?? '')
])))
const busy = ref(false)
const error = ref('')
const showAdvanced = ref(false)
const now = new Date()
const maxYear = now.getFullYear() + 1
const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
function priceForDisplay(value) {
  if (value === undefined || value === null || value === '') return ''
  const number = Number(value)
  return Number.isFinite(number) ? number.toFixed(2) : value
}
function formatPurchasedPrice() {
  draft.value.purchased_price = priceForDisplay(draft.value.purchased_price)
}
async function save() {
  if (!allowed.value || busy.value) return
  const payload = Object.fromEntries(Object.entries(draft.value).filter(([, value]) => value !== ''))
  for (const key of ['year', 'mileage', 'initial_mileage', 'purchased_price']) {
    if (key in payload) payload[key] = Number(payload[key])
  }
  if (!payload.make?.trim() || payload.make.length > 100 || !payload.model?.trim() || payload.model.length > 100 ||
      !Number.isInteger(payload.year) || payload.year < 1886 || payload.year > maxYear ||
      ['mileage', 'initial_mileage'].some(key => key in payload && (!Number.isInteger(payload[key]) || payload[key] < 0)) ||
      ('purchased_price' in payload && !Number.isFinite(payload.purchased_price)) ||
      (payload.vin && payload.vin.length > 17) || (payload.license_plate && payload.license_plate.length > 20) ||
      (payload.fuel_type && !['gas', 'diesel', 'electric'].includes(payload.fuel_type)) ||
      (payload.purchased_date && (!/^\d{4}-\d{2}-\d{2}$/.test(payload.purchased_date) || !Number.isFinite(Date.parse(payload.purchased_date)) || payload.purchased_date > today))) {
    error.value = 'Check the vehicle fields: use a valid year, non-negative whole-number mileage, a valid price, and a purchase date no later than today.'
    return
  }
  busy.value = true
  error.value = ''
  try { emit('updated', await request(`/cars/${props.car._id}`, payload, 'PATCH')) }
  catch (err) { if (err.name !== 'AbortError') error.value = err.message }
  finally { busy.value = false }
}
</script>

<style scoped>
.vehicle-edit-dialog {
  width: min(900px, calc(100% - 28px));
  padding: 30px;
  border-color: var(--gb-border);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.3);
}

.vehicle-edit-dialog :deep(header > button) {
  width: 32px;
  height: 32px;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--gb-text-muted);
  font-size: 0;
}

.vehicle-edit-dialog :deep(header > button::before) {
  content: "\00d7";
  font-size: 1.5rem;
  line-height: 1;
}

.vehicle-edit-dialog :deep(header > button:hover) {
  background: rgba(179, 199, 255, 0.08);
  color: var(--gb-heading);
}

.vehicle-edit {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-intro {
  margin-top: -12px;
  color: var(--gb-text-muted);
}

.form-error {
  margin: 0;
  padding: 10px 12px;
  border: 1px solid rgba(169, 88, 97, 0.45);
  border-radius: 8px;
  background: rgba(169, 88, 97, 0.1);
}

.vehicle-edit .form-fields,
.vehicle-edit form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-layout {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 30px;
}

.form-column {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-group,
.fuel-type-picker {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label,
.fuel-type-picker > span {
  color: var(--gb-text);
  font-size: 0.95rem;
  font-weight: 500;
}

.form-group input {
  padding: 10px 12px;
  border: 1px solid var(--gb-border);
  border-radius: 8px;
  background: var(--gb-background-deep);
  color: var(--gb-heading);
  font-size: 0.95rem;
}

.form-group input:focus {
  outline: none;
  border-color: var(--gb-accent);
  box-shadow: 0 0 0 3px rgba(179, 199, 255, 0.1);
}

.fuel-options {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.fuel-option {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
  padding: 10px 8px;
  border: 1px solid var(--gb-border);
  border-radius: 8px;
  background: var(--gb-background-deep);
  color: var(--gb-text-muted);
  font-size: 0.86rem;
  cursor: pointer;
}

.fuel-option.active {
  border-color: var(--gb-accent);
  background: rgba(179, 199, 255, 0.12);
  color: var(--gb-accent);
}

.fuel-option:focus-within {
  border-color: var(--gb-accent);
  box-shadow: 0 0 0 3px rgba(179, 199, 255, 0.1);
}

.fuel-option input {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
}

.advanced-section {
  overflow: hidden;
  border: 1px solid var(--gb-border-strong);
  border-radius: 10px;
}

.advanced-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 12px 14px;
  border: 0;
  background: transparent;
  color: var(--gb-text);
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.advanced-toggle:hover {
  background: rgba(179, 199, 255, 0.08);
  color: var(--gb-accent);
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

.advanced-section.expanded .advanced-toggle svg {
  transform: rotate(180deg);
}

.advanced-options {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 15px;
  padding: 15px;
  border-top: 1px solid var(--gb-border);
  background: rgba(179, 199, 255, 0.04);
}

.advanced-options .wide {
  grid-column: 1 / -1;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 10px;
  padding-top: 20px;
  border-top: 1px solid var(--gb-border);
}

.form-actions button {
  padding: 10px 24px;
  border-radius: 999px;
  font: inherit;
  font-weight: 500;
}

.submit-button {
  border-color: transparent;
  background: var(--gb-accent);
  color: #141820;
}

.submit-button:hover {
  background: var(--gb-accent-hover);
}

.cancel-button {
  border-color: var(--gb-border);
  background: transparent;
  color: var(--gb-text);
}

.cancel-button:hover {
  background: var(--gb-surface-hover);
}

@media (max-width: 640px) {
  .vehicle-edit-dialog {
    padding: 22px;
  }

  .form-layout,
  .advanced-options {
    grid-template-columns: 1fr;
  }

  .advanced-options .wide {
    grid-column: auto;
  }
}
</style>
