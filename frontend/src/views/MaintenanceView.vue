<template>
  <NavBar />
  <main class="maintenance-page">
    <MaintenanceHeader :car="car" :maintenances="maintenances" :reminders="reminders" @add="openCreateMaintenance" @import="isImportOpen = true" />
    <MaintenanceControls v-model:search="search" v-model:sort="sort" v-model:category="category" />
    <MaintenanceList :maintenances="displayedMaintenances" :has-records="maintenances.length > 0" @delete="handleDeleteMaintenance" @edit="openEditMaintenance" />
  </main>

  <MaintenanceForm
    v-if="isFormOpen"
    :key="formKey"
    :mode="formMode"
    :maintenance="selectedMaintenance"
    :is-saving="isFormSaving"
    @close="closeMaintenanceForm"
    @created="handleCreateMaintenance"
    @updated="handleUpdateMaintenance"
  />
  <MaintenanceImport
    v-if="isImportOpen"
    :car-id="route.params.carId"
    :api-base="API_BASE"
    @close="isImportOpen = false"
    @imported="handleImported"
  />
</template>

<script setup>
import { API_BASE, useApiClient } from '../utils/auth'
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { showToast } from '../components/Toast.vue'
import NavBar from '../components/NavBar.vue'
import MaintenanceForm from '../components/MaintenanceForm.vue'
import MaintenanceHeader from '../components/MaintenanceHeader.vue'
import MaintenanceList from '../components/MaintenanceList.vue'
import MaintenanceImport from '../components/MaintenanceImport.vue'
import MaintenanceControls from '../components/MaintenanceControls.vue'
import { filterAndSortMaintenances } from '../utils/maintenanceDisplay.js'
const route = useRoute()
const car = ref(null)
const maintenances = ref([])
const reminders = ref([])
const isFormOpen = ref(false)
const isFormSaving = ref(false)
const isImportOpen = ref(false)
const selectedMaintenance = ref(null)
const search = ref('')
const sort = ref('recent')
const category = ref('all')
const fetch = useApiClient()

const formMode = computed(() => (selectedMaintenance.value ? 'edit' : 'create'))
const formKey = computed(() => selectedMaintenance.value?._id ?? 'new')
const displayedMaintenances = computed(() => filterAndSortMaintenances(maintenances.value, search.value, sort.value, category.value))



onMounted(() => Promise.all([handleFetchCar(), handleFetchMaintenances(), handleFetchReminders()]))

async function handleFetchCar() {
  try {
    const response = await fetch(`${API_BASE}/cars/${route.params.carId}`)
    if (!response.ok) return
    car.value = await response.json()
  } catch {
    showToast('Failed to fetch car details', 'error')
  }
}

async function handleFetchReminders() {
  try {
    const fetchedReminders = []
    const pageSize = 100
    while (true) {
      const response = await fetch(`${API_BASE}/cars/${route.params.carId}/reminders/?skip=${fetchedReminders.length}&limit=${pageSize}`)
      if (!response.ok) return
      const page = await response.json()
      fetchedReminders.push(...page)
      if (page.length < pageSize) break
    }
    reminders.value = fetchedReminders
  } catch {
    showToast('Failed to fetch service reminders', 'error')
  }
}

async function handleFetchMaintenances() {
  try {
    const fetchedMaintenances = []
    const pageSize = 100

    while (true) {
      const response = await fetch(`${API_BASE}/cars/${route.params.carId}/logs/?skip=${fetchedMaintenances.length}&limit=${pageSize}`)
      if (!response.ok) {
        showToast('Failed to fetch maintenance logs', 'error')
        return
      }
      const page = await response.json()
      fetchedMaintenances.push(...page)
      if (page.length < pageSize) break
    }

    maintenances.value = fetchedMaintenances
  } catch {
    showToast('Failed to fetch maintenance logs', 'error')
  }
}

async function handleCreateMaintenance(payload) {
  if (isFormSaving.value) return
  isFormSaving.value = true
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
    await Promise.all([handleFetchCar(), handleFetchReminders()])
    isFormSaving.value = false
    showToast('Maintenance log created successfully', 'success')
    closeMaintenanceForm()
  } catch {
    showToast('Failed to create maintenance log', 'error')
  } finally {
    isFormSaving.value = false
  }
}

async function handleUpdateMaintenance(payload) {
  if (!selectedMaintenance.value || isFormSaving.value) {
    return
  }

  isFormSaving.value = true
  try {
    const response = await fetch(`${API_BASE}/cars/${route.params.carId}/logs/${selectedMaintenance.value._id}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })

    if (!response.ok) {
      showToast('Failed to update maintenance log', 'error')
      return
    }

    const updatedMaintenance = await response.json()
    maintenances.value = maintenances.value.map(log => (log._id === updatedMaintenance._id ? updatedMaintenance : log))
    await Promise.all([handleFetchCar(), handleFetchReminders()])
    isFormSaving.value = false
    showToast('Maintenance log updated successfully', 'success')
    closeMaintenanceForm()
  } catch {
    showToast('Failed to update maintenance log', 'error')
  } finally {
    isFormSaving.value = false
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
    await handleFetchReminders()
    showToast('Maintenance log deleted successfully', 'success')
  } catch {
    showToast('Failed to delete maintenance log', 'error')
  }
}

function openCreateMaintenance() {
  selectedMaintenance.value = null
  isFormOpen.value = true
}

function openEditMaintenance(log) {
  selectedMaintenance.value = log
  isFormOpen.value = true
}

function closeMaintenanceForm() {
  if (isFormSaving.value) return
  isFormOpen.value = false
  selectedMaintenance.value = null
}

async function handleImported(result) {
  isImportOpen.value = false
  await Promise.all([handleFetchCar(), handleFetchMaintenances(), handleFetchReminders()])
  showToast(`Imported ${result.created} maintenance records${result.skipped_duplicates ? `; skipped ${result.skipped_duplicates} duplicates` : ''}`, 'success')
}

function handleBack() {
  window.history.back()
}


</script>

<style scoped>
.maintenance-page {
  width: min(100% - 40px, 1200px);
  min-height: calc(100vh - 70px);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 28px;
  padding: clamp(40px, 7vw, 72px) 0 80px;
}

@media (max-width: 600px) {
  .maintenance-page {
    width: min(100% - 28px, 1200px);
    padding-top: 36px;
  }
}
</style>
