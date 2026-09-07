<script setup>
import { ref } from 'vue'
import NavBar from '../components/NavBar.vue'
import { useApiRequest, validateCredentials } from '../utils/auth'
const request = useApiRequest()
const current = ref('')
const password = ref('')
const confirm = ref('')
const busy = ref(false)
const error = ref('')
const success = ref('')
async function submit() {
  if (busy.value) return
  success.value = ''
  error.value = validateCredentials(null, password.value)
  if (!error.value && password.value !== confirm.value) error.value = 'Passwords do not match.'
  if (error.value) return
  busy.value = true
  try {
    await request('/auth/password', { current_password: current.value, new_password: password.value })
    success.value = 'Password changed. This session remains signed in.'
  } catch (err) { error.value = err.message }
  finally { current.value = ''; password.value = ''; confirm.value = ''; busy.value = false }
}
</script>
<template>
  <NavBar />
  <main class="auth-page">
    <section class="auth-card">
      <h1>Account security</h1>
      <p>Choose a password of 4-128 characters. Spaces are preserved.</p>
      <form class="auth-form" @submit.prevent="submit">
        <label>Current password<input v-model="current" type="password" autocomplete="current-password" required :disabled="busy" /></label>
        <label>New password<input v-model="password" type="password" autocomplete="new-password" required :disabled="busy" /></label>
        <label>Confirm new password<input v-model="confirm" type="password" autocomplete="new-password" required :disabled="busy" /></label>
        <p v-if="error" class="auth-error" role="alert">{{ error }}</p>
        <p v-if="success" role="status">{{ success }}</p>
        <button class="auth-button" :disabled="busy">{{ busy ? 'Saving...' : 'Change password' }}</button>
      </form>
    </section>
  </main>
</template>
