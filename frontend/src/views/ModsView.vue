<template>

  <NavBar />
  <main class="mods-page">
    <span class="page-label">Planned work</span>
    <h1>Mods</h1>
    <p>Planned modifications for {{ carMake }}.</p>
    <div class="coming-soon">
      <h2>Modification planner</h2>
      <p>Your planned upgrades will appear here.</p>
      <button type="button" @click="handleBack">Back</button>
    </div>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import Toast, { showToast } from '../components/Toast.vue'
import NavBar from '../components/NavBar.vue'
const route = useRoute()
const car = ref(null)
const envApiBase = import.meta.env.VITE_API_BASE_URL?.trim()
const API_BASE = envApiBase || `${window.location.protocol}//${window.location.hostname}:8000`

const carMake = computed(() => {
  if (!car.value) {
    return 'Loading car...'
  }
  
  return `${car.value.make ?? ''} ${car.value.model ?? ''}`.trim() || 'Car details'
})

onMounted(() => {
  handleFetchCar()
})

async function handleFetchCar() {
  const response = await fetch(`${API_BASE}/cars/${route.params.carId}`)
  if (!response.ok) {
    showToast('Failed to fetch car', 'error')
    throw new Error('Failed to fetch car')
  }
  const data = await response.json()
  car.value = data
  showToast('Car fetched successfully', 'success')
}

function handleBack() {
  window.history.back()
}


</script>

<style scoped>
.mods-page {
  width: min(100% - 40px, 1200px);
  min-height: calc(100vh - 70px);
  margin: 0 auto;
  padding: clamp(40px, 7vw, 72px) 0 80px;
}

.page-label {
  display: inline-block;
  padding: 6px 11px;
  border-radius: 999px;
  background: rgba(179, 199, 255, 0.1);
  color: var(--gb-accent);
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
}

.mods-page > h1 {
  margin-top: 12px;
  color: var(--gb-heading);
  font-size: clamp(2rem, 5vw, 3.5rem);
  font-weight: 700;
}

.mods-page > p {
  color: var(--gb-text-muted);
}

.coming-soon {
  margin-top: 34px;
  padding: clamp(24px, 5vw, 44px);
  border: 1px solid var(--gb-border);
  border-radius: 16px;
  background: var(--gb-surface);
}

.coming-soon h2 {
  color: var(--gb-heading);
  font-size: 1.4rem;
  font-weight: 600;
}

.coming-soon p {
  margin-top: 6px;
  color: var(--gb-text-muted);
}

.coming-soon button {
  margin-top: 20px;
  padding: 9px 15px;
  border: 1px solid var(--gb-border-strong);
  border-radius: 999px;
  background: transparent;
  color: var(--gb-accent);
  cursor: pointer;
}

@media (max-width: 600px) {
  .mods-page {
    width: min(100% - 28px, 1200px);
  }
}

</style>
