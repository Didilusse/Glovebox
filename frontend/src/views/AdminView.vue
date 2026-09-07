<script setup>
import { nextTick, onMounted, ref, watch } from 'vue'
import NavBar from '../components/NavBar.vue'
import { auth, useApiRequest, normalizeUsername, validateCredentials } from '../utils/auth'
const request = useApiRequest()
const users = ref([])
const loading = ref(false)
const busy = ref(false)
const error = ref('')
const message = ref('')
const username = ref('')
const password = ref('')
const action = ref(null)
const replacement = ref('')
const confirmation = ref('')
const dialog = ref(null)
let previousFocus
watch(action, async value => {
  if (value) {
    previousFocus = document.activeElement
    await nextTick()
    dialog.value?.querySelector('input, button')?.focus()
  } else previousFocus?.focus()
})
function trapFocus(event) {
  const controls = [...dialog.value.querySelectorAll('input:not(:disabled), button:not(:disabled)')]
  const first = controls[0]
  const last = controls.at(-1)
  if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus() }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() }
}
const version = auth.version
async function load() {
  loading.value = true
  error.value = ''
  try { users.value = await request('/users/', undefined, 'GET') }
  catch (err) { error.value = err.message }
  finally { loading.value = false }
}
onMounted(load)
function select(type, user) {
  action.value = { type, user }
  replacement.value = ''
  confirmation.value = ''
  error.value = ''
  message.value = ''
}
function cancel() {
  action.value = null
  replacement.value = ''
  confirmation.value = ''
}
async function create() {
  if (busy.value || version !== auth.version) return
  error.value = validateCredentials(username.value, password.value)
  if (error.value) return
  busy.value = true
  message.value = ''
  try {
    await request('/users/', { username: normalizeUsername(username.value), password: password.value })
    username.value = ''
    message.value = 'User created.'
    await load()
  } catch (err) { error.value = err.message }
  finally { password.value = ''; busy.value = false }
}
async function confirmAction() {
  if (busy.value || !action.value || version !== auth.version) return
  const { type, user } = action.value
  error.value = type === 'reset' ? validateCredentials(null, replacement.value) : ''
  if (type === 'reset' && !error.value && replacement.value !== confirmation.value) error.value = 'Passwords do not match.'
  if (error.value) return
  busy.value = true
  try {
    await request(`/users/${encodeURIComponent(user._id)}${type === 'reset' ? '/password' : ''}`,
      type === 'reset' ? { new_password: replacement.value } : undefined, type === 'reset' ? 'PATCH' : 'DELETE')
    message.value = type === 'reset' ? `Password reset for ${user.username}.` : `Deleted ${user.username}.`
    cancel()
    await load()
  } catch (err) { error.value = err.message }
  finally { replacement.value = ''; confirmation.value = ''; busy.value = false }
}
</script>
<template>
  <NavBar />
  <main class="auth-page">
    <h1>Manage users</h1>
    <p>Create accounts and manage access to Glovebox.</p>
    <p v-if="error && !action" class="auth-error" role="alert">{{ error }}</p>
    <p v-if="message" role="status">{{ message }}</p>
    <section class="auth-section">
      <h2>Create user</h2>
      <form class="auth-form" @submit.prevent="create">
        <label>Username<input v-model="username" autocomplete="off" required :disabled="busy" /></label>
        <label>Initial password<input v-model="password" type="password" autocomplete="new-password" required :disabled="busy" /></label>
        <small>Username: 3-30 letters, numbers, dots, underscores or hyphens. Password: 8-128 characters; spaces are preserved.</small>
        <button class="auth-button" :disabled="busy">Create user</button>
      </form>
    </section>
    <section class="auth-section" aria-label="Users">
      <div class="auth-actions"><h2>Accounts</h2><button class="auth-button secondary" :disabled="loading || busy" @click="load">Refresh users</button></div>
      <p v-if="loading" role="status">Loading users...</p>
      <p v-else-if="!users.length">No users to display.</p>
      <ul class="user-list">
        <li v-for="user in users" :key="user._id">
          <div><strong>{{ user.username }}</strong><span> {{ user.is_admin ? 'Administrator' : 'User' }}{{ user._id === auth.user?._id ? ' (you)' : '' }}</span><small v-if="user.created_at">Created {{ new Date(user.created_at).toLocaleDateString() }}</small></div>
          <div class="auth-actions">
            <router-link v-if="user._id === auth.user?._id" to="/account">Change your password</router-link>
            <template v-else>
              <button class="auth-button secondary" :disabled="busy || loading" @click="select('reset', user)">Reset password</button>
              <button v-if="!user.is_admin" class="auth-button danger" :disabled="busy || loading" @click="select('delete', user)">Delete user</button>
            </template>
          </div>
        </li>
      </ul>
    </section>
    <div v-if="action" class="auth-dialog" @keydown.esc="!busy && cancel()">
      <section ref="dialog" class="auth-card" role="dialog" aria-modal="true" aria-labelledby="admin-dialog-title" @keydown.tab="trapFocus">
        <h2 id="admin-dialog-title">{{ action.type === 'reset' ? 'Reset password' : 'Delete user' }}: {{ action.user.username }}</h2>
        <p>{{ action.type === 'reset' ? 'This will replace their password and sign them out of existing sessions.' : 'This permanently deletes this account, its cars, maintenance history and planned mods. This cannot be undone.' }}</p>
        <form class="auth-form" @submit.prevent="confirmAction">
          <template v-if="action.type === 'reset'">
            <label>New password<input v-model="replacement" type="password" autocomplete="new-password" required :disabled="busy" /></label>
            <label>Confirm new password<input v-model="confirmation" type="password" autocomplete="new-password" required :disabled="busy" /></label>
          </template>
          <p v-if="error" class="auth-error" role="alert">{{ error }}</p>
          <div class="auth-actions">
            <button type="button" class="auth-button secondary" :disabled="busy" @click="cancel">Cancel</button>
            <button class="auth-button" :disabled="busy">{{ busy ? 'Saving...' : action.type === 'reset' ? 'Confirm password reset' : 'Confirm deletion' }}</button>
          </div>
        </form>
      </section>
    </div>
  </main>
</template>
<style scoped>
.user-list { list-style: none; padding: 0; }
.user-list li { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 16px; padding: 20px 0; border-top: 1px solid var(--gb-border); }
.user-list strong { color: var(--gb-heading); overflow-wrap: anywhere; }
.user-list small { display: block; color: var(--gb-text-muted); }
</style>
