<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
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
const search = ref('')
let previousFocus
const filteredUsers = computed(() => {
  const query = search.value.trim().toLowerCase()
  return query ? users.value.filter(user => user.username.toLowerCase().includes(query)) : users.value
})
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
  username.value = ''
  password.value = ''
  replacement.value = ''
  confirmation.value = ''
  error.value = ''
  message.value = ''
}
function cancel() {
  action.value = null
  username.value = ''
  password.value = ''
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
    message.value = 'User created.'
    cancel()
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
  <main class="auth-page users-page">
    <header class="users-header">
      <div>
        <span class="page-label">Administration</span>
        <h1>Users</h1>
        <p>Create accounts and manage access to Glovebox.</p>
      </div>
      <button class="auth-button add-user-button" @click="select('create')">Add new user</button>
    </header>
    <p v-if="error && !action" class="auth-error" role="alert">{{ error }}</p>
    <p v-if="message" class="success-message" role="status">{{ message }}</p>
    <section class="auth-section" aria-label="Users">
      <div class="accounts-heading">
        <div>
          <h2>Accounts</h2>
          <p>{{ users.length }} {{ users.length === 1 ? 'account' : 'accounts' }}</p>
        </div>
        <div class="table-tools">
          <label class="search-field">
            <span class="sr-only">Search by username</span>
            <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></svg>
            <input v-model="search" type="search" placeholder="Search by username..." />
          </label>
          <button class="refresh-button" :disabled="loading || busy" aria-label="Refresh users" @click="load">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 11a8.1 8.1 0 0 0-15.5-2M4 4v5h5M4 13a8.1 8.1 0 0 0 15.5 2M20 20v-5h-5" /></svg>
            Refresh
          </button>
        </div>
      </div>
      <p v-if="loading" role="status">Loading users...</p>
      <p v-else-if="!users.length">No users to display.</p>
      <p v-else-if="!filteredUsers.length" class="empty-search">No usernames match “{{ search }}”.</p>
      <div v-else class="users-table-wrap">
        <table class="users-table">
          <thead><tr><th>Username</th><th>Role</th><th>Created at</th><th><span class="sr-only">Actions</span></th></tr></thead>
          <tbody>
            <tr v-for="user in filteredUsers" :key="user._id" :class="{ 'admin-row': user.is_admin }">
              <td>
                <div class="user-profile">
                  <span class="user-avatar" :class="{ admin: user.is_admin }" aria-hidden="true">{{ user.username.charAt(0).toUpperCase() }}</span>
                  <div class="user-name-row"><strong>{{ user.username }}</strong><span v-if="user._id === auth.user?._id" class="you-badge">You</span></div>
                </div>
              </td>
              <td><span class="role-badge" :class="{ admin: user.is_admin }">{{ user.is_admin ? 'Administrator' : 'User' }}</span></td>
              <td><span class="created-date">{{ user.created_at ? new Date(user.created_at).toLocaleDateString() : 'Unknown' }}</span></td>
              <td>
                <div class="auth-actions user-actions">
                  <router-link v-if="user._id === auth.user?._id" to="/account">Edit account</router-link>
                  <template v-else>
                    <button class="text-action" :disabled="busy || loading" @click="select('reset', user)">Reset password</button>
                    <button v-if="!user.is_admin" class="text-action danger" :disabled="busy || loading" @click="select('delete', user)">Delete</button>
                  </template>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
    <div v-if="action" class="auth-dialog" @keydown.esc="!busy && cancel()">
      <section ref="dialog" class="auth-card" role="dialog" aria-modal="true" aria-labelledby="admin-dialog-title" @keydown.tab="trapFocus">
        <h2 id="admin-dialog-title">{{ action.type === 'create' ? 'Create a new user' : `${action.type === 'reset' ? 'Reset password' : 'Delete user'}: ${action.user.username}` }}</h2>
        <p>{{ action.type === 'create' ? 'Give someone their own username and private garage.' : action.type === 'reset' ? 'This will replace their password and sign them out of existing sessions.' : 'This permanently deletes this account, its cars, maintenance history and planned mods. This cannot be undone.' }}</p>
        <form class="auth-form" @submit.prevent="action.type === 'create' ? create() : confirmAction()">
          <template v-if="action.type === 'create'">
            <label>Username<input v-model="username" autocomplete="off" required :disabled="busy" /></label>
            <label>Password<input v-model="password" type="password" autocomplete="new-password" required :disabled="busy" /></label>
            <small>Username: 3-30 letters, numbers, dots, underscores or hyphens. Password: 4-128 characters.</small>
          </template>
          <template v-else-if="action.type === 'reset'">
            <label>New password<input v-model="replacement" type="password" autocomplete="new-password" required :disabled="busy" /></label>
            <label>Confirm new password<input v-model="confirmation" type="password" autocomplete="new-password" required :disabled="busy" /></label>
          </template>
          <p v-if="error" class="auth-error" role="alert">{{ error }}</p>
          <div class="auth-actions">
            <button type="button" class="auth-button secondary" :disabled="busy" @click="cancel">Cancel</button>
            <button class="auth-button" :disabled="busy">{{ busy ? 'Saving...' : action.type === 'create' ? 'Create user' : action.type === 'reset' ? 'Confirm password reset' : 'Confirm deletion' }}</button>
          </div>
        </form>
      </section>
    </div>
  </main>
</template>
<style scoped>
.users-page { margin-top: 56px; margin-bottom: 80px; }
.users-header { display: flex; align-items: flex-end; justify-content: space-between; gap: 24px; margin-bottom: 34px; }
.users-header h1 { margin: 4px 0 2px; font-size: clamp(2.2rem, 5vw, 3.25rem); letter-spacing: -.035em; }
.users-header p, .accounts-heading p { margin: 0; color: var(--gb-text-muted); }
.page-label { color: var(--gb-accent); font-size: .72rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; }
.add-user-button { flex: 0 0 auto; font-weight: 700; }
.success-message { padding: 11px 14px; border: 1px solid rgba(179, 199, 255, .22); border-radius: 10px; background: rgba(179, 199, 255, .08); color: var(--gb-accent); }
.accounts-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 18px; }
.accounts-heading h2 { margin: 0; }
.accounts-heading p { font-size: .82rem; }
.table-tools { display: flex; align-items: center; gap: 10px; }
.search-field { width: min(280px, 34vw); display: flex; align-items: center; gap: 8px; padding: 0 11px; border: 1px solid var(--gb-border); border-radius: 9px; background: var(--gb-background-deep); }
.search-field:focus-within { border-color: var(--gb-accent); box-shadow: 0 0 0 2px rgba(179, 199, 255, .12); }
.search-field svg { width: 16px; flex: 0 0 auto; fill: none; stroke: var(--gb-text-muted); stroke-width: 1.8; stroke-linecap: round; }
.search-field input { width: 100%; padding: 9px 0; border: 0; outline: 0; background: transparent; color: var(--gb-heading); font: inherit; }
.search-field input::placeholder { color: var(--gb-text-muted); }
.refresh-button { display: inline-flex; align-items: center; gap: 7px; padding: 8px 11px; border: 1px solid var(--gb-border); border-radius: 9px; background: transparent; color: var(--gb-text-muted); font: inherit; cursor: pointer; }
.refresh-button:hover { border-color: var(--gb-border-strong); color: var(--gb-heading); }
.refresh-button svg { width: 15px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.users-table-wrap { overflow-x: auto; }
.users-table { width: 100%; min-width: 700px; border-collapse: collapse; text-align: left; }
.users-table th { padding: 12px 14px; border-bottom: 1px solid var(--gb-border); color: var(--gb-text-muted); font-size: .7rem; font-weight: 700; letter-spacing: .055em; text-transform: uppercase; }
.users-table td { padding: 16px 14px; border-bottom: 1px solid var(--gb-border); vertical-align: middle; }
.users-table tbody tr { transition: background-color .18s ease; }
.users-table tbody tr:hover { background: rgba(255, 255, 255, .018); }
.users-table .admin-row { background: rgba(179, 199, 255, .025); }
.users-table th:last-child, .users-table td:last-child { text-align: right; }
.user-profile { min-width: 0; display: flex; align-items: center; gap: 13px; }
.user-avatar { width: 36px; height: 36px; flex: 0 0 auto; display: grid; place-items: center; border: 1px solid var(--gb-border-strong); border-radius: 10px; background: var(--gb-background-deep); color: var(--gb-text); font-weight: 750; }
.user-avatar.admin { border-color: rgba(179, 199, 255, .28); background: rgba(179, 199, 255, .1); color: var(--gb-accent); }
.user-name-row { display: flex; align-items: center; flex-wrap: wrap; gap: 7px; }
.users-table strong { color: var(--gb-heading); font-weight: 650; overflow-wrap: anywhere; }
.role-badge, .you-badge { padding: 3px 7px; border: 1px solid var(--gb-border); border-radius: 999px; color: var(--gb-text-muted); font-size: .65rem; font-weight: 700; line-height: 1.2; text-transform: uppercase; }
.role-badge.admin { border-color: rgba(179, 199, 255, .28); background: rgba(179, 199, 255, .09); color: var(--gb-accent); }
.you-badge { border-color: transparent; background: var(--gb-surface-hover); color: var(--gb-heading); }
.created-date { color: var(--gb-text-muted); white-space: nowrap; }
.user-actions { justify-content: flex-end; }
.user-actions a, .text-action { font-size: .82rem; font-weight: 650; }
.text-action { padding: 4px; border: 0; background: transparent; color: var(--gb-accent); cursor: pointer; }
.text-action:hover { color: var(--gb-accent-hover); }
.text-action.danger { color: var(--gb-danger); }
.text-action:disabled { cursor: wait; opacity: .5; }
.empty-search { padding: 28px 0 8px; color: var(--gb-text-muted); text-align: center; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
@media (max-width: 720px) {
  .users-header { align-items: flex-start; }
  .accounts-heading { align-items: flex-start; flex-direction: column; }
  .table-tools { width: 100%; }
  .search-field { width: 100%; }
}
@media (max-width: 480px) {
  .users-page { width: min(100% - 24px, 1000px); margin-top: 32px; }
  .users-header { align-items: stretch; flex-direction: column; }
  .auth-section { padding: 18px; }
  .table-tools { align-items: stretch; flex-direction: column; }
  .refresh-button { justify-content: center; }
}
</style>
