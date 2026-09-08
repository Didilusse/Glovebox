<template>
  <VehicleDialog v-if="allowed" title="Edit vehicle" @close="$emit('close')">
    <p>Update vehicle details. Optional fields left blank remain unchanged.</p>
    <p v-if="error" role="alert">{{ error }}</p>
    <form @submit.prevent="save">
      <fieldset :disabled="busy">
        <label>Make<input v-model.trim="draft.make" required maxlength="100" /></label>
        <label>Model<input v-model.trim="draft.model" required maxlength="100" /></label>
        <label>Year<input v-model="draft.year" type="number" required min="1886" :max="maxYear" step="1" /></label>
        <label>Mileage<input v-model="draft.mileage" type="number" min="0" step="1" /></label>
        <label>Initial mileage<input v-model="draft.initial_mileage" type="number" min="0" step="1" /></label>
        <label>VIN<input v-model.trim="draft.vin" maxlength="17" /></label>
        <label>License plate<input v-model.trim="draft.license_plate" maxlength="20" /></label>
        <label>Fuel type<select v-model="draft.fuel_type"><option value="">Not specified</option><option value="gas">Gasoline</option><option value="diesel">Diesel</option><option value="electric">Electric</option></select></label>
        <label>Purchase date<input v-model="draft.purchased_date" type="date" :max="today" /></label>
        <label>Purchase price<input v-model="draft.purchased_price" type="number" min="0" step="any" /></label>
        <button type="submit">{{ busy ? 'Saving...' : 'Save vehicle' }}</button>
      </fieldset>
    </form>
  </VehicleDialog>
</template>

<script setup>
import { computed, ref } from 'vue'
import { auth, useApiRequest } from '../utils/auth'
import { canAccess } from '../utils/vehicleAccess'
import VehicleDialog from './VehicleDialog.vue'
const props = defineProps({ car: { type: Object, required: true } })
const emit = defineEmits(['close', 'updated'])
const version = auth.version
const allowed = computed(() => auth.version === version && canAccess(props.car, 'vehicle', true))
const request = useApiRequest()
const fields = ['make', 'model', 'year', 'mileage', 'initial_mileage', 'vin', 'license_plate', 'fuel_type', 'purchased_date', 'purchased_price']
const draft = ref(Object.fromEntries(fields.map(key => [key, props.car[key] ?? ''])))
const busy = ref(false)
const error = ref('')
const now = new Date()
const maxYear = now.getFullYear() + 1
const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
async function save() {
  if (!allowed.value || busy.value) return
  const payload = Object.fromEntries(Object.entries(draft.value).filter(([, value]) => value !== ''))
  for (const key of ['year', 'mileage', 'initial_mileage', 'purchased_price']) {
    if (key in payload) payload[key] = Number(payload[key])
  }
  if (!payload.make?.trim() || payload.make.length > 100 || !payload.model?.trim() || payload.model.length > 100 ||
      !Number.isInteger(payload.year) || payload.year < 1886 || payload.year > maxYear ||
      ['mileage', 'initial_mileage'].some(key => key in payload && (!Number.isInteger(payload[key]) || payload[key] < 0)) ||
      ('purchased_price' in payload && (!Number.isFinite(payload.purchased_price) || payload.purchased_price < 0)) ||
      (payload.vin && payload.vin.length > 17) || (payload.license_plate && payload.license_plate.length > 20) ||
      (payload.fuel_type && !['gas', 'diesel', 'electric'].includes(payload.fuel_type)) ||
      (payload.purchased_date && (!/^\d{4}-\d{2}-\d{2}$/.test(payload.purchased_date) || !Number.isFinite(Date.parse(payload.purchased_date)) || payload.purchased_date > today))) {
    error.value = 'Check the vehicle fields: use a valid year, non-negative mileage and price, and a purchase date no later than today.'
    return
  }
  busy.value = true
  error.value = ''
  try { emit('updated', await request(`/cars/${props.car._id}`, payload, 'PATCH')) }
  catch (err) { if (err.name !== 'AbortError') error.value = err.message }
  finally { busy.value = false }
}
</script>
