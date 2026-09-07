<script setup>
import { ref } from 'vue'
import { auth, logout } from '../utils/auth'
const busy = ref(false)
async function signOut() {
  busy.value = true
  await logout()
  busy.value = false
}
</script>
<template>
  <div v-if="auth.user" class="account-controls">
    <router-link to="/account">{{ auth.user.username }}</router-link>
    <router-link v-if="auth.user.is_admin" to="/admin">Users</router-link>
    <button class="auth-button secondary" :disabled="busy" @click="signOut">{{ busy ? 'Signing out...' : 'Log out' }}</button>
  </div>
</template>
<style scoped>
.account-controls { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; font-size: .85rem; }
.account-controls a { overflow-wrap: anywhere; }
</style>
