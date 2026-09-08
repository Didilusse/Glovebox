<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { auth, useApiRequest, setSession, normalizeUsername, validateCredentials } from '../utils/auth'
const request = useApiRequest()
const route = useRoute()
const router = useRouter()
const setup = computed(() => route.path === '/setup')
const username = ref('')
const password = ref('')
const confirmation = ref('')
const setupToken = ref('')
const busy = ref(false)
const error = ref('')
async function submit() {
  if (busy.value) return
  error.value = validateCredentials(username.value, password.value, setup.value ? 12 : 1)
  if (!error.value && setup.value && password.value !== confirmation.value) error.value = 'Passwords do not match.'
  if (!error.value && setup.value && auth.setupTokenRequired && !setupToken.value) error.value = 'Enter the setup token provided by your server administrator.'
  if (error.value) return
  busy.value = true
  const wasSetup = setup.value
  try {
    const credentials = { username: normalizeUsername(username.value), password: password.value }
    const result = await request(wasSetup ? '/auth/setup' : '/auth/login', credentials,
      'POST', wasSetup && auth.setupTokenRequired ? { 'X-Setup-Token': setupToken.value } : {})
    // Setup may return a user or 204 instead of creating a session.
    if (wasSetup) auth.setupRequired = false
    const session = result?.token ? result : await request('/auth/login', credentials)
    if (!session?.token || !session.user?._id) throw new Error('Invalid sign-in response from server.')
    setSession(session.token, session.user)
    auth.notice = ''
    await router.replace(wasSetup ? '/welcome' : '/')
  } catch (err) {
    error.value = err.message
    if (wasSetup && auth.setupRequired && err.name !== 'AbortError') {
      try {
        const status = await request('/auth/status', undefined, 'GET')
        if (status.setup_required === false) {
          auth.setupRequired = false
          auth.notice = 'Setup has completed. Please sign in.'
        }
      } catch { /* Keep the original setup error visible if status is unavailable. */ }
    }
    if (wasSetup && !auth.setupRequired) await router.replace('/login')
  } finally {
    password.value = ''
    confirmation.value = ''
    setupToken.value = ''
    busy.value = false
  }
}
</script>

<template>
  <main class="auth-page">
    <section class="auth-card">
      <img src="/Glovebox.png" alt="Glovebox" width="56" height="56" />
      <h1>{{ setup ? 'Set up your garage' : 'Welcome back' }}</h1>
      <p>{{ setup ? 'Create the administrator account to get started.' : 'Sign in to your Glovebox account.' }}</p>
      <p v-if="auth.notice" role="status">{{ auth.notice }}</p>
      <form class="auth-form" @submit.prevent="submit">
        <label>Username<input v-model="username" name="username" autocomplete="username" required :disabled="busy" /></label>
        <label>Password<input v-model="password" name="password" type="password" :autocomplete="setup ? 'new-password' : 'current-password'" required :disabled="busy" /></label>
        <template v-if="setup">
          <small>Username: 3-30 lowercase letters, numbers, dots, underscores or hyphens. Password: 12-128 characters, including spaces.</small>
          <label>Confirm password<input v-model="confirmation" type="password" autocomplete="new-password" required :disabled="busy" /></label>
          <label v-if="auth.setupTokenRequired">Setup token<input v-model="setupToken" type="password" autocomplete="off" required :disabled="busy" /></label>
        </template>
        <p v-if="error" class="auth-error" role="alert">{{ error }}</p>
        <button class="auth-button" :disabled="busy">{{ busy ? 'Please wait...' : setup ? 'Create administrator' : 'Sign in' }}</button>
      </form>
    </section>
  </main>
</template>
