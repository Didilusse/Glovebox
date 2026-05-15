<template>
  <NavBar />
  <Toast />
  <main class="maintenance-page">
    <MaintenanceHeader @add="isCreateOpen = true" />
    <MaintenanceList :maintenances="maintenances" @delete="handleDeleteMaintenance" />
  </main>

  <MaintenanceForm
    v-if="isCreateOpen"
    @close="isCreateOpen = false"
    @created="handleCreateMaintenance"
  />
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import Toast, { showToast } from '../components/Toast.vue'
import NavBar from '../components/NavBar.vue'
import MaintenanceForm from '../components/MaintenanceForm.vue'
import MaintenanceHeader from '../components/MaintenanceHeader.vue'
import MaintenanceList from '../components/MaintenanceList.vue'
const route = useRoute()
const maintenances = ref([])
const isCreateOpen = ref(false)
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

async function handleCreateMaintenance(payload) {
  try {
    const response = await fetch(`${API_BASE}/cars/${route.params.carId}/logs/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })

    if (!response.ok) {
      showToast('Failed to create maintenance log', 'error')
      return
    }

    const newMaintenance = await response.json()
    maintenances.value = [newMaintenance, ...maintenances.value]
    showToast('Maintenance log created successfully', 'success')
  } catch {
    showToast('Failed to create maintenance log', 'error')
  }
}

async function handleDeleteMaintenance(logId) {
  try {
    const response = await fetch(`${API_BASE}/cars/${route.params.carId}/logs/${logId}`, {
      method: 'DELETE'
    })

    if (!response.ok) {
      showToast('Failed to delete maintenance log', 'error')
      return
    }

    maintenances.value = maintenances.value.filter(log => log._id !== logId)
    showToast('Maintenance log deleted successfully', 'success')
  } catch {
    showToast('Failed to delete maintenance log', 'error')
  }
}

async function handleEditReminder(log) {
  try {
    const months = window.prompt('Enter interval months (leave blank to skip)', log.interval_months ?? '')
    const miles = window.prompt('Enter interval miles (leave blank to skip)', log.interval_miles ?? '')

    const body = {}
    if (months !== null && months !== '') body.interval_months = Number(months)
    if (miles !== null && miles !== '') body.interval_miles = Number(miles)

    if (!Object.keys(body).length) return

    const response = await fetch(`${API_BASE}/cars/${route.params.carId}/logs/${log._id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })

    if (!response.ok) {
      showToast('Failed to update reminder', 'error')
      return
    }

    const updated = await response.json()
    maintenances.value = maintenances.value.map(m => (m._id === updated._id ? updated : m))
    showToast('Reminder updated', 'success')
  } catch (err) {
    showToast('Failed to update reminder', 'error')
  }
}

function handleBack() {
  window.history.back()
}


</script>

<style scoped>
.maintenance-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 24px;
}

</style>