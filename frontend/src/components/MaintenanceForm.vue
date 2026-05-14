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
          </div>

          <div class="field">
            <label for="mileage">Mileage</label>
            <input id="mileage" type="number" v-model.number="mileage" />
          </div>

          <div class="field">
            <label for="cost">Cost</label>
            <input id="cost" type="number" step="0.01" v-model.number="cost" />
          </div>

          <div class="field">
            <label for="done_by">Done by</label>
            <select id="done_by" v-model="done_by">
              <option value="self">Self</option>
              <option value="shop">Shop</option>
            </select>
          </div>
        </div>

        <div class="form-row">
          <div class="field" style="flex:1 1 100%">
            <label for="work_done">Work done</label>
            <input id="work_done" v-model="work_done" />
          </div>
        </div>

        <div class="form-row">
          <div class="field" style="flex:1 1 100%">
            <label for="notes">Notes</label>
            <textarea id="notes" rows="4" v-model="notes"></textarea>
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
const work_done = ref('')
const notes = ref('')

function handleCreateMaintenance() {
  if (mileage.value === null || mileage.value === '' || cost.value === null || cost.value === '' || !work_done.value.trim()) {
    return
  }

  const payload = {
    mileage: Number(mileage.value),
    cost: Number(cost.value),
    done_by: done_by.value,
    work_done: work_done.value.trim(),
    notes: notes.value.trim() || null
  }

  if (date.value) {
    payload.date_of_service = date.value
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
</style>