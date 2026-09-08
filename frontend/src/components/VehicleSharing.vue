<template>
  <VehicleDialog v-if="allowed" title="Manage sharing" @close="$emit('close')">
    <p>Share with an existing account using their exact username. Only the owner can manage sharing or delete the vehicle.</p>
    <p>View is read-only. Edit also allows adding, updating and deleting section records.</p>
    <p v-if="error" role="alert">{{ error }}</p>
    <p v-if="loading" role="status">Loading recipients...</p>
    <button v-else-if="!loaded" type="button" @click="loadShares">Retry loading recipients</button>
    <template v-else>
      <section aria-label="Shared with" class="recipients">
        <h3>Shared with</h3>
        <p v-if="!shares.length">No recipients yet.</p>
        <article v-for="share in shares" :key="share.user_id">
          <strong>{{ share.username }}</strong>
          <small>Vehicle: {{ share.permissions.vehicle }} / Maintenance: {{ share.permissions.maintenance }} / Mods: {{ share.permissions.mods }}</small>
          <div class="dialog-actions">
            <button type="button" :disabled="busy" @click="editShare(share)">Edit {{ share.username }}</button>
            <button type="button" :disabled="busy" @click="revoke(share)">Revoke {{ share.username }}</button>
          </div>
        </article>
      </section>
      <form @submit.prevent="save">
        <h3>{{ editing ? `Edit access for ${editing.username}` : 'Add recipient' }}</h3>
        <fieldset :disabled="busy">
          <label v-if="!editing">Username<input v-model="username" required maxlength="30" autocomplete="off" placeholder="Existing username" /></label>
          <label v-for="section in sections" :key="section.key">
            {{ section.label }}
            <select v-model="permissions[section.key]" :aria-label="`${section.label} permission`">
              <option v-if="section.key !== 'vehicle'" value="none">No access</option>
              <option value="view">View</option>
              <option value="edit">Edit</option>
            </select>
            <small>{{ section.description }}</small>
          </label>
          <div class="dialog-actions">
            <button type="submit">{{ busy ? 'Saving...' : editing ? 'Save permissions' : 'Share vehicle' }}</button>
            <button v-if="editing" type="button" @click="reset">Cancel edit</button>
          </div>
        </fieldset>
      </form>
    </template>
  </VehicleDialog>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { auth, normalizeUsername, useApiRequest } from '../utils/auth'
import VehicleDialog from './VehicleDialog.vue'
const props = defineProps({ car: { type: Object, required: true } })
defineEmits(['close'])
const version = auth.version
const allowed = computed(() => auth.version === version && props.car.access?.is_owner === true)
const request = useApiRequest()
const shares = ref([])
const loading = ref(false)
const loaded = ref(false)
const busy = ref(false)
const error = ref('')
const username = ref('')
const editing = ref(null)
const defaults = () => ({ vehicle: 'view', maintenance: 'view', mods: 'view' })
const permissions = ref(defaults())
const sections = [
  { key: 'vehicle', label: 'Vehicle', description: 'Vehicle details and safety are always visible. Edit allows changing vehicle details.' },
  { key: 'maintenance', label: 'Maintenance', description: 'Service logs, reminders and statistics. Edit also allows importing records.' },
  { key: 'mods', label: 'Mods', description: 'Independent access to the modification plan. Edit includes moving and deleting parts.' }
]
const path = `/cars/${props.car._id}/shares`
onMounted(loadShares)
async function loadShares() {
  if (!allowed.value) return
  loading.value = true
  loaded.value = false
  shares.value = []
  error.value = ''
  try {
    shares.value = await request(`${path}/`, undefined, 'GET')
    loaded.value = true
  } catch (err) {
    if (err.name !== 'AbortError') error.value = err.message
  } finally { loading.value = false }
}
function reset() {
  editing.value = null
  username.value = ''
  permissions.value = defaults()
}
function editShare(share) {
  editing.value = share
  permissions.value = { ...share.permissions }
  error.value = ''
}
async function save() {
  if (!allowed.value || busy.value || !loaded.value) return
  const normalized = normalizeUsername(username.value)
  if (!editing.value && !/^[a-z0-9][a-z0-9_.-]{2,29}$/.test(normalized)) {
    error.value = 'Enter a valid existing username (3-30 characters).'
    return
  }
  busy.value = true
  error.value = ''
  try {
    const grant = await request(editing.value ? `${path}/${editing.value.user_id}` : `${path}/`, {
      ...(!editing.value ? { username: normalized } : {}), permissions: { ...permissions.value }
    }, editing.value ? 'PUT' : 'POST')
    shares.value = [...shares.value.filter(share => share.user_id !== grant.user_id), grant]
    reset()
  } catch (err) {
    if (err.name !== 'AbortError') error.value = err.message
  } finally { busy.value = false }
}
async function revoke(share) {
  if (!allowed.value || busy.value) return
  busy.value = true
  error.value = ''
  try {
    await request(`${path}/${share.user_id}`, undefined, 'DELETE')
    shares.value = shares.value.filter(item => item.user_id !== share.user_id)
    if (editing.value?.user_id === share.user_id) reset()
  } catch (err) {
    if (err.name !== 'AbortError') error.value = err.message
  } finally { busy.value = false }
}
</script>

<style scoped>
.recipients { margin: 24px 0; }
.recipients article { display: grid; gap: 10px; padding: 14px 0; border-bottom: 1px solid var(--gb-border); overflow-wrap: anywhere; }
p + p { margin-top: 8px; }
</style>
