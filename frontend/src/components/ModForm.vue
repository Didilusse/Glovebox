<template>
  <div class="overlay" @click.self="$emit('close')">
    <section class="panel" role="dialog" aria-modal="true" :aria-labelledby="titleId">
      <header>
        <div>
          <span>{{ isEditMode ? 'Update card' : 'New card' }}</span>
          <h2 :id="titleId">{{ isEditMode ? 'Edit part' : 'Add a part' }}</h2>
        </div>
        <button type="button" class="close" @click="$emit('close')">Close</button>
      </header>

      <form @submit.prevent="handleSubmit">
        <section class="form-group">
          <div class="section-heading">
            <span>01</span>
            <div><h3>Part details</h3><p>What you are buying and what it costs.</p></div>
          </div>

          <div class="field full">
            <label for="mod-name">Part name</label>
            <input id="mod-name" v-model="name" maxlength="200" placeholder="e.g. Street coilover kit" :class="{ invalid: submitted && !name.trim() }" />
            <small v-if="submitted && !name.trim()" class="error">Part name is required.</small>
          </div>

          <div class="field-grid">
            <div class="field">
              <label for="mod-brand">Brand</label>
              <input id="mod-brand" v-model="brand" maxlength="100" placeholder="e.g. KW Suspension" />
            </div>
            <div class="field">
              <label for="mod-part-number">Part number</label>
              <input id="mod-part-number" v-model="partNumber" maxlength="100" placeholder="For fitment checks" />
            </div>
            <div class="field">
              <label for="mod-category">Category</label>
              <select id="mod-category" v-model="category">
                <option v-for="option in categories" :key="option" :value="option">{{ titleCase(option) }}</option>
              </select>
            </div>
            <div class="field">
              <label for="mod-cost">Part cost</label>
              <input id="mod-cost" v-model.number="cost" type="number" min="0" step="0.01" :class="{ invalid: submitted && !hasValidCost }" />
              <small v-if="submitted && !hasValidCost" class="error">Enter a cost of zero or more.</small>
            </div>
          </div>
        </section>

        <section class="form-group">
          <div class="section-heading">
            <span>02</span>
            <div><h3>Install plan</h3><p>Set the decision priority, owner, and target.</p></div>
          </div>

          <div class="field-grid">
            <div class="field">
              <label for="mod-status">Board status</label>
              <select id="mod-status" v-model="status">
                <option value="planned">Planned</option>
                <option value="purchased">Purchased</option>
                <option value="installed">Installed</option>
              </select>
            </div>
            <div class="field">
              <label for="mod-priority">Priority</label>
              <select id="mod-priority" v-model="priority">
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
            <div class="field">
              <label for="mod-install-method">Install method</label>
              <select id="mod-install-method" v-model="installMethod">
                <option value="undecided">Undecided</option>
                <option value="diy">DIY</option>
                <option value="shop">Shop</option>
              </select>
            </div>
            <div class="field">
              <label for="mod-target-date">Target date</label>
              <input id="mod-target-date" v-model="targetDate" type="date" />
            </div>
          </div>
        </section>

        <section class="form-group">
          <div class="section-heading">
            <span>03</span>
            <div><h3>Reference</h3><p>Keep the source and fitment notes with the card.</p></div>
          </div>

          <div class="field-grid reference-grid">
            <div class="field">
              <label for="mod-type">Record type</label>
              <select id="mod-type" v-model="type">
                <option value="modification">Modification</option>
                <option value="maintenance">Maintenance</option>
              </select>
            </div>
            <div class="field">
              <label for="mod-url">Product URL</label>
              <input id="mod-url" v-model="url" type="url" placeholder="https://" :class="{ invalid: submitted && !hasValidUrl }" />
              <small v-if="submitted && !hasValidUrl" class="error">Enter a valid http or https URL.</small>
            </div>
          </div>

          <div class="field full">
            <label for="mod-notes">Fitment and install notes</label>
            <textarea id="mod-notes" v-model="notes" rows="4" maxlength="5000" placeholder="Required hardware, fitment details, install sequence..." />
          </div>
        </section>

        <div class="actions">
          <button type="button" class="secondary" :disabled="isSaving" @click="$emit('close')">Cancel</button>
          <button type="submit" class="primary" :disabled="isSaving">
            <span v-if="isSaving" class="button-spinner"></span>
            {{ isSaving ? 'Saving...' : isEditMode ? 'Save changes' : 'Add to board' }}
          </button>
        </div>
      </form>
    </section>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  mode: {
    type: String,
    default: 'create'
  },
  mod: {
    type: Object,
    default: null
  },
  isSaving: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'created', 'updated'])
const categories = ['engine', 'suspension', 'exterior', 'interior', 'wheels', 'brakes', 'exhaust', 'fluids']
const titleId = 'mod-form-title'
const name = ref('')
const type = ref('modification')
const category = ref('engine')
const status = ref('planned')
const cost = ref(0)
const brand = ref('')
const partNumber = ref('')
const priority = ref('medium')
const installMethod = ref('undecided')
const targetDate = ref('')
const url = ref('')
const notes = ref('')
const submitted = ref(false)

const isEditMode = computed(() => props.mode === 'edit')
const hasValidCost = computed(() => cost.value !== '' && cost.value !== null && Number.isFinite(Number(cost.value)) && Number(cost.value) >= 0)
const hasValidUrl = computed(() => {
  if (!url.value.trim()) return true
  try {
    const parsed = new URL(url.value.trim())
    return parsed.protocol === 'http:' || parsed.protocol === 'https:'
  } catch {
    return false
  }
})

watch(
  () => props.mod,
  (mod) => {
    name.value = mod?.name ?? ''
    type.value = mod?.type ?? 'modification'
    category.value = mod?.category ?? 'engine'
    status.value = mod?.status ?? 'planned'
    cost.value = mod?.cost ?? 0
    brand.value = mod?.brand ?? ''
    partNumber.value = mod?.part_number ?? ''
    priority.value = mod?.priority ?? 'medium'
    installMethod.value = mod?.install_method ?? 'undecided'
    targetDate.value = mod?.target_date ?? ''
    url.value = mod?.url ?? ''
    notes.value = mod?.notes ?? ''
    submitted.value = false
  },
  { immediate: true }
)

function handleSubmit() {
  submitted.value = true
  if (!name.value.trim() || !hasValidCost.value || !hasValidUrl.value) return

  const payload = {
    name: name.value.trim(),
    type: type.value,
    category: category.value,
    status: status.value,
    cost: Number(cost.value),
    priority: priority.value,
    install_method: installMethod.value,
    part_number: partNumber.value.trim() || null,
    target_date: targetDate.value || null,
    brand: brand.value.trim() || null,
    url: url.value.trim() || null,
    notes: notes.value.trim() || null
  }
  emit(isEditMode.value ? 'updated' : 'created', payload)
}

function titleCase(value) {
  return value.charAt(0).toUpperCase() + value.slice(1)
}
</script>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  overflow-y: auto;
  background: rgba(8, 11, 15, 0.8);
  backdrop-filter: blur(7px);
}

.panel {
  width: min(100%, 680px);
  max-height: calc(100vh - 48px);
  padding: 24px;
  overflow-y: auto;
  border: 1px solid var(--gb-border);
  border-radius: 18px;
  background: var(--gb-surface);
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.45);
}

header,
.actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

header span {
  color: var(--gb-accent);
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

h2 {
  margin-top: 2px;
  color: var(--gb-heading);
  font-size: 1.45rem;
  font-weight: 650;
}

.close,
.secondary,
.primary {
  border-radius: 999px;
  padding: 9px 14px;
  cursor: pointer;
}

.close,
.secondary {
  border: 1px solid var(--gb-border-strong);
  background: transparent;
  color: var(--gb-text-muted);
}

form {
  display: flex;
  flex-direction: column;
  gap: 24px;
  margin-top: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-bottom: 24px;
  border-bottom: 1px solid rgba(179, 199, 255, 0.1);
}

.section-heading {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.section-heading > span {
  padding-top: 2px;
  color: var(--gb-accent);
  font-size: 0.68rem;
  font-weight: 700;
}

.section-heading h3 {
  color: var(--gb-heading);
  font-size: 0.9rem;
  font-weight: 650;
}

.section-heading p {
  margin-top: 1px;
  color: var(--gb-text-muted);
  font-size: 0.74rem;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

label {
  color: var(--gb-text);
  font-size: 0.82rem;
  font-weight: 600;
}

input,
select,
textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--gb-border);
  border-radius: 9px;
  outline: none;
  background: var(--gb-background-deep);
  color: var(--gb-heading);
  font: inherit;
}

textarea {
  resize: vertical;
}

input:focus,
select:focus,
textarea:focus {
  border-color: var(--gb-accent);
  box-shadow: 0 0 0 3px rgba(179, 199, 255, 0.1);
}

.invalid {
  border-color: var(--gb-danger);
}

.error {
  color: var(--gb-danger);
  font-size: 0.76rem;
}

.actions {
  justify-content: flex-end;
  margin-top: 4px;
}

.primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 0;
  background: var(--gb-accent);
  color: #141820;
  font-weight: 750;
}

.primary:hover:not(:disabled) {
  background: var(--gb-accent-hover);
}

button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.button-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(20, 24, 32, 0.3);
  border-top-color: #141820;
  border-radius: 50%;
  animation: spin 700ms linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 600px) {
  .overlay {
    align-items: flex-start;
    padding: 14px;
  }

  .panel {
    max-height: none;
    padding: 20px;
  }

  .field-grid {
    grid-template-columns: 1fr;
  }
}
</style>
