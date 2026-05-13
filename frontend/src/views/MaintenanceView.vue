<template>

  <NavBar />
  <Toast />
  <MaintenanceList :maintenances="maintenances" />
  <button @click="handleBack">Back</button>
  Maintenance
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import Toast, { showToast } from '../components/Toast.vue'
import NavBar from '../components/NavBar.vue'
import MaintenanceList from '../components/MaintenanceList.vue'
const route = useRoute()
const maintenances = ref([])
const envApiBase = import.meta.env.VITE_API_BASE_URL?.trim()
const API_BASE = envApiBase || `${window.location.protocol}//${window.location.hostname}:8000`



onMounted(() => {
  handleFetchMaintenances()
})

async function handleFetchMaintenances() {
  try {
    const response = await fetch(`${API_BASE}/cars/${route.params.carId}/logs/`)
    if (!response.ok) {
      showToast('Failed to fetch maintenance logs', 'error')
      return
    }

    const data = await response.json()
    maintenances.value = Array.isArray(data) ? data : []
  } catch {
    showToast('Failed to fetch maintenance logs', 'error')
  }
}

function handleBack() {
  window.history.back()
}


</script>

<style scoped>

</style>