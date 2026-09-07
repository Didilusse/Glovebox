<template>
  <div id="app">
    <main v-if="!auth.ready" class="auth-page">
      <section class="auth-card">
        <h1>Glovebox</h1>
        <p v-if="auth.loading || !auth.error" role="status">Connecting to your garage...</p>
        <template v-else>
          <p class="auth-error" role="alert">Unable to initialize authentication: {{ auth.error }}</p>
          <button class="auth-button" @click="retry">Retry connection</button>
        </template>
      </section>
    </main>
    <router-view v-else v-slot="{ Component, route }">
      <component :is="Component" v-if="canDisplay(route)" :key="`${auth.version}:${route.fullPath}`" />
    </router-view>
    <Toast />
  </div>
</template>

<script setup>
import { watch } from 'vue'
import { useRouter } from 'vue-router'
import { auth, initializeAuth } from './utils/auth'
import Toast from './components/Toast.vue'
import './assets/auth.css'
const router = useRouter()
function canDisplay(route) {
  if (auth.setupRequired) return route.path === '/setup'
  if (!auth.user) return route.path === '/login'
  return !['/login', '/setup', '/auth'].includes(route.path) && (!route.meta.admin || auth.user.is_admin)
}
async function retry() {
  await initializeAuth()
  if (auth.ready) await router.replace(auth.setupRequired ? '/setup' : auth.user ? '/' : '/login')
}
watch(() => auth.version, () => {
  if (auth.ready && !auth.user) router.replace(auth.setupRequired ? '/setup' : '/login')
  else if (auth.ready && router.currentRoute.value.meta.admin && !auth.user?.is_admin) router.replace('/')
}, { flush: 'sync' })
</script>
