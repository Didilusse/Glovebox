<script setup>
import { onMounted, reactive, ref } from 'vue'
import NavBar from '../components/NavBar.vue'
import { useApiRequest } from '../utils/auth'
import { sanitizeWholeNumberInput } from '../utils/numericInput'

const request = useApiRequest()
const form = reactive({ oil_interval_miles: 5000, oil_interval_months: 6, webhook_url: '', discord_webhook_url: '', email: '' })
const loading = ref(true)
const loaded = ref(false)
const saving = ref(false)
const error = ref('')
const message = ref('')
const emailAvailable = ref(false)
function populate(data) {
  for (const key of Object.keys(form)) form[key] = data[key] ?? ''
  emailAvailable.value = data.email_available
}
async function load() {
  loading.value = true
  error.value = ''
  try { populate(await request('/settings', undefined, 'GET')); loaded.value = true }
  catch (e) { if (e.name !== 'AbortError') error.value = 'Unable to load settings. Please retry.' }
  finally { loading.value = false }
}
async function save() {
  if (saving.value || !loaded.value) return
  error.value = ''; message.value = ''
  const body = Object.fromEntries(Object.entries(form).map(([key, value]) => [key, typeof value === 'string' ? value.trim() || null : value]))
  if (body.oil_interval_miles !== null) body.oil_interval_miles = Number(body.oil_interval_miles)
  for (const key of ['webhook_url', 'discord_webhook_url']) {
    if (!body[key]) continue
    try { if (new URL(body[key]).protocol !== 'https:') throw new Error() }
    catch { error.value = 'Webhook URLs must be valid HTTPS URLs.'; return }
  }
  saving.value = true
  try { populate(await request('/settings', body, 'PUT')); message.value = 'Settings saved.' }
  catch (e) { if (e.name !== 'AbortError') error.value = 'Unable to save settings. Please retry.' }
  finally { saving.value = false }
}
onMounted(load)
</script>

<template>
  <NavBar />
  <main class="settings">
    <h1>Settings</h1>
    <p>Your oil service defaults and notification destinations.</p>
    <p v-if="loading" role="status">Loading settings...</p>
    <p v-if="error" role="alert">{{ error }} <button v-if="!loaded" @click="load">Retry</button></p>
    <p v-if="message" role="status">{{ message }}</p>
    <form v-if="loaded" @submit.prevent="save">
      <fieldset :disabled="saving">
        <legend>Oil change defaults</legend>
        <p>Used for new oil changes only. Clear either interval to disable it.</p>
        <label for="oil-miles">Mileage interval (miles)</label>
        <input id="oil-miles" :value="form.oil_interval_miles" inputmode="numeric" @input="form.oil_interval_miles = sanitizeWholeNumberInput($event)" />
        <label for="oil-months">Time interval (months)</label>
        <input id="oil-months" v-model.number="form.oil_interval_months" type="number" min="1" max="1200" step="1" />
      </fieldset>
      <fieldset :disabled="saving">
        <legend>Notification destinations</legend>
        <p>Optional. Clear a destination to remove it. Notifications are sent for vehicles you own; shared vehicle alerts appear on Home.</p>
        <p>Destinations must use public HTTPS on port 443. New due alerts use the destinations enabled when the alert is created.</p>
        <label for="webhook">Custom HTTPS webhook</label>
        <input id="webhook" v-model="form.webhook_url" type="url" autocomplete="off" />
        <label for="discord">Discord webhook</label>
        <input id="discord" v-model="form.discord_webhook_url" type="url" autocomplete="off" />
        <label for="email">Email</label>
        <input id="email" v-model="form.email" type="email" :disabled="!emailAvailable" aria-describedby="email-help" />
        <p id="email-help">{{ emailAvailable ? 'Email delivery is available.' : 'Email delivery is not configured on this server.' }}</p>
      </fieldset>
      <button :disabled="saving" type="submit">{{ saving ? 'Saving...' : 'Save settings' }}</button>
    </form>
    <router-link to="/account">Account and password</router-link>
  </main>
</template>

<style scoped>
.settings { width: min(100% - 32px, 720px); margin: 40px auto; }
h1, legend { color: var(--gb-heading); font-weight: 650; }
h1 { font-size: 2.4rem; letter-spacing: -.03em; margin-bottom: 10px; }
p { color: var(--gb-text-muted); line-height: 1.7; }
fieldset { margin: 32px 0; padding: 24px; border: 1px solid var(--gb-border); border-radius: 12px; background: var(--gb-surface); }
fieldset p { margin: 8px 0; font-size: .85rem; }
legend { padding: 0 8px; }
label { display: block; margin-top: 16px; }
input { width: 100%; min-width: 0; padding: 10px; color: var(--gb-heading); background: var(--gb-surface); border: 1px solid var(--gb-border-strong); border-radius: 6px; }
button { padding: 10px 18px; margin-bottom: 20px; border: 1px solid var(--gb-border); background: var(--gb-accent); color: var(--gb-background-deep); font: inherit; font-weight: 650; border-radius: 8px; cursor: pointer; }
button:disabled { opacity: .6; cursor: wait; }
input:focus-visible, button:focus-visible { outline: 2px solid var(--gb-accent); outline-offset: 3px; }
[role=alert] { color: var(--gb-danger); }
</style>
