<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import CarForm from '../components/CarForm.vue'
import AccountControls from '../components/AccountControls.vue'
import { API_BASE } from '../utils/auth'
const adding = ref(false)
const router = useRouter()
</script>
<template>
  <main class="auth-page">
    <AccountControls />
    <h1>Your garage is ready</h1>
    <p>Add your first car now, or come back to it later.</p>
    <div class="auth-actions">
      <button class="auth-button" @click="adding = true">Add a car</button>
      <router-link to="/">Skip for now</router-link>
    </div>
    <section v-if="adding" class="auth-section">
      <CarForm :api-base="API_BASE" @created="router.replace('/')" @close="adding = false" />
    </section>
  </main>
</template>
