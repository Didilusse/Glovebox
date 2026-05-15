<template>
  <div class="overlay" @click.self="$emit('close')">
    <section class="panel">
      <div class="panel-header">
        <h2>Add maintenance</h2>

        <button type="button" class="close-button" @click="$emit('close')">Close</button>
      </div>

      <form class="form-section" @submit.prevent="handleCreateMaintenance">
        <div class="form-row">
          <div class="field">
            <label for="date">Date</label>
            <input id="date" type="date" v-model="date" />
            <span v-if="isSubmitted && !date" class="error-text">Date is required.</span>
          </div>

          <div class="field">
            <label for="mileage">Mileage</label>
            <input id="mileage" type="number" v-model.number="mileage" :class="{'input-error': isSubmitted && (mileage === null || mileage === '')}" />
            <span v-if="isSubmitted && (mileage === null || mileage === '')" class="error-text">Mileage is required.</span>
          </div>

          <div class="field">
            <label for="cost">Cost</label>
            <input id="cost" type="number" step="0.01" v-model.number="cost" :class="{'input-error': isSubmitted && (cost === null || cost === '')}" />
            <span v-if="isSubmitted && (cost === null || cost === '')" class="error-text">Cost is required.</span>
          </div>

          <div class="field">
            <label for="done_by">Done by</label>
            <select id="done_by" v-model="done_by" :class="{'input-error': isSubmitted && !done_by}">
              <option value="self">Self</option>
              <option value="shop">Shop</option>
            </select>
            <span v-if="isSubmitted && !done_by" class="error-text">Who performed the work is required.</span>
          </div>

          <div class="field">
            <label for="category">Category</label>
            <select id="category" v-model="category" :class="{'input-error': isSubmitted && !category}">
              <option value="engine">Engine</option>
              <option value="suspension">Suspension</option>
              <option value="exterior">Exterior</option>
              <option value="interior">Interior</option>
              <option value="wheels">Wheels</option>
              <option value="brakes">Brakes</option>
              <option value="exhaust">Exhaust</option>
              <option value="fluids">Fluids</option>
              <option value="other">Other</option>
            </select>
            <span v-if="isSubmitted && !category" class="error-text">Category is required.</span>
          </div>
        </div>

        <div class="form-row">
          <div class="field" style="flex:1 1 100%">
            <label for="work_done">Work done</label>
            <input id="work_done" v-model="work_done" :class="{'input-error': isSubmitted && !work_done.trim()}" />
            <span v-if="isSubmitted && !work_done.trim()" class="error-text">Work done is required.</span>
          </div>
        </div>

        <div class="form-row">
          <div class="field" style="flex:1 1 100%">
            <label for="notes">Notes</label>
            <textarea id="notes" rows="4" v-model="notes" :class="{'input-error': isSubmitted && !notes.trim()}"></textarea>
            <span v-if="isSubmitted && !notes.trim()" class="error-text">Notes are required.</span>
          </div>
        </div>

        <div class="form-row">
          <div class="field">
            <label>
              <input type="checkbox" v-model="createReminder" /> Add reminder
            </label>
          </div>
        </div>

        <div class="form-row" v-if="createReminder">
          <div class="field">
            <label for="interval_months">Interval (months)</label>
            <input id="interval_months" type="number" v-model.number="interval_months" min="0" />
            <span v-if="isSubmitted && createReminder && (interval_months === null || interval_months === '')" class="error-text">Provide months or miles.</span>
          </div>

          <div class="field">
            <label for="interval_miles">Interval (miles)</label>
            <input id="interval_miles" type="number" v-model.number="interval_miles" min="0" />
            <span v-if="isSubmitted && createReminder && (interval_miles === null || interval_miles === '')" class="error-text">Provide months or miles.</span>
          </div>
        </div>

        <div class="actions">
          <button type="button" class="secondary" @click="$emit('close')">Cancel</button>
          <button type="submit" class="primary">Save</button>
        </div>
      </form>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['close', 'created'])

const date = ref('')
const mileage = ref(null)
const cost = ref(null)
const done_by = ref('self')
const category = ref('other')
const work_done = ref('')
const notes = ref('')

const createReminder = ref(false)
const interval_months = ref(null)
const interval_miles = ref(null)

const isSubmitted = ref(false);


function handleCreateMaintenance() {
  isSubmitted.value = true;

  const hasMileage = !(mileage.value === null || mileage.value === '')
  const hasCost = !(cost.value === null || cost.value === '')
  const hasWork = Boolean(work_done.value && work_done.value.trim())
  const hasDoneBy = Boolean(done_by.value)
  const hasCategory = Boolean(category.value)
  const hasDate = Boolean(date.value)
  const hasNotes = Boolean(notes.value && notes.value.trim())

  // If createReminder true, require at least one interval value
  const hasInterval = !createReminder.value || ( (interval_months.value !== null && interval_months.value !== '') || (interval_miles.value !== null && interval_miles.value !== '') )

  if (!hasMileage || !hasCost || !hasWork || !hasDoneBy || !hasCategory || !hasDate || !hasNotes || !hasInterval) {
    return
  }

  const payload = {
    date_of_service: date.value,
    mileage: Number(mileage.value),
    cost: Number(cost.value),
    done_by: done_by.value,
    category: category.value,
    interval_months: createReminder.value ? (interval_months.value !== null && interval_months.value !== '' ? Number(interval_months.value) : null) : null,
    interval_miles: createReminder.value ? (interval_miles.value !== null && interval_miles.value !== '' ? Number(interval_miles.value) : null) : null,
    work_done: work_done.value.trim(),
    notes: notes.value.trim()
  }

  emit('created', payload)
  emit('close')
}

</script>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(10, 12, 15, 0.55);
  backdrop-filter: blur(4px);
  padding: 24px;
  z-index: 1000;
}

.panel {
  width: min(100%, 640px);
  background: #333;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 12px 30px rgba(16, 24, 40, 0.4);
  display: flex;
  flex-direction: column;
  gap: 12px;
  color: #e6edf3;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.close-button {
  border: 1px solid #1e1e1e;
  background: #1e1e1e;
  border-radius: 8px;
  padding: 8px 12px;
  cursor: pointer;
  color: #cbd5e1;
}

.note {
  color: #94a3b8;
  margin-top: 8px;
}

.form-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1 1 220px;
}

.field label {
  font-size: 0.85rem;
  color: #cbd5e1;
}

.field input,
.field textarea,
.field select {
  padding: 10px 12px;
  border: 1px solid #212020;
  border-radius: 8px;
  background: #1e1e1e;
  color: #e6edf3;
  outline: none;
}

.actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 8px;
}

.primary {
  background: linear-gradient(180deg,#0ea5a7,#0284c7);
  color: #0b1220;
  border: none;
  padding: 10px 14px;
  border-radius: 8px;
  cursor: pointer;
}

.secondary {
  background: transparent;
  border: 1px solid #263343;
  padding: 10px 14px;
  border-radius: 8px;
  cursor: pointer;
  color: #cbd5e1;
}

.error-text {
  color: red;
  font-size: 0.875rem;
  display: block;
  margin-top: 4px;
}
.input-error {
  border-color: red;
}
</style>