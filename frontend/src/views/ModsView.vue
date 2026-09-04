<template>
  <NavBar />
  <Toast />
  <main class="mods-page">
    <ModsHeader :car-name="carName" :mods="mods" @add="openCreateForm" />

    <div v-if="isLoading" class="board-message">
      <span class="loader"></span>
      Loading build plan...
    </div>
    <div v-else-if="loadFailed" class="board-message error-message">
      <p>We couldn't load this build plan.</p>
      <button type="button" @click="loadPage">Try again</button>
    </div>
    <ModsBoard
      v-else
      :mods="mods"
      :disabled="isMoving"
      :moving-id="movingModId"
      :saved-id="savedModId"
      @move="handleMoveMod"
      @edit="openEditForm"
      @delete="handleDeleteMod"
    />
  </main>

  <ModForm
    v-if="isFormOpen"
    :key="selectedMod?._id ?? 'new'"
    :mode="selectedMod ? 'edit' : 'create'"
    :mod="selectedMod"
    :is-saving="isFormSaving"
    @close="closeForm"
    @created="handleCreateMod"
    @updated="handleUpdateMod"
  />
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import ModForm from '../components/ModForm.vue'
import ModsBoard from '../components/ModsBoard.vue'
import ModsHeader from '../components/ModsHeader.vue'
import NavBar from '../components/NavBar.vue'
import Toast, { showToast } from '../components/Toast.vue'

const route = useRoute()
const car = ref(null)
const mods = ref([])
const isLoading = ref(true)
const loadFailed = ref(false)
const isMoving = ref(false)
const movingModId = ref('')
const savedModId = ref('')
const isFormOpen = ref(false)
const isFormSaving = ref(false)
const selectedMod = ref(null)
let savedStateTimer
const envApiBase = import.meta.env.VITE_API_BASE_URL?.trim()
const API_BASE = envApiBase || `${window.location.protocol}//${window.location.hostname}:8000`

const carName = computed(() => {
  if (!car.value) return ''
  return `${car.value.make ?? ''} ${car.value.model ?? ''}`.trim()
})

onMounted(loadPage)
onBeforeUnmount(() => window.clearTimeout(savedStateTimer))

async function loadPage() {
  isLoading.value = true
  loadFailed.value = false
  const [carLoaded, modsLoaded] = await Promise.all([fetchCar(), fetchMods()])
  loadFailed.value = !carLoaded || !modsLoaded
  isLoading.value = false
}

async function fetchCar() {
  try {
    const response = await fetch(`${API_BASE}/cars/${route.params.carId}`)
    if (!response.ok) return false
    car.value = await response.json()
    return true
  } catch {
    return false
  }
}

async function fetchMods() {
  try {
    const fetchedMods = []
    const pageSize = 100
    while (true) {
      const response = await fetch(`${API_BASE}/cars/${route.params.carId}/planned-mods/?skip=${fetchedMods.length}&limit=${pageSize}`)
      if (!response.ok) return false
      const page = await response.json()
      fetchedMods.push(...page)
      if (page.length < pageSize) break
    }
    mods.value = fetchedMods
    return true
  } catch {
    return false
  }
}

async function handleCreateMod(payload) {
  if (isFormSaving.value) return
  isFormSaving.value = true
  try {
    const response = await fetch(`${API_BASE}/cars/${route.params.carId}/planned-mods/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    if (!response.ok) throw new Error()
    const createdMod = await response.json()
    mods.value = [...mods.value, createdMod]
    isFormSaving.value = false
    closeForm()
    showToast('Part added to your build plan', 'success')
  } catch {
    showToast('Failed to add part', 'error')
  } finally {
    isFormSaving.value = false
  }
}

async function handleUpdateMod(payload) {
  if (!selectedMod.value || isFormSaving.value) return
  isFormSaving.value = true
  try {
    const response = await fetch(`${API_BASE}/cars/${route.params.carId}/planned-mods/${selectedMod.value._id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    if (!response.ok) throw new Error()
    const updatedMod = await response.json()
    mods.value = mods.value.map(mod => mod._id === updatedMod._id ? updatedMod : mod)
    isFormSaving.value = false
    closeForm()
    showToast('Part updated', 'success')
  } catch {
    showToast('Failed to update part', 'error')
  } finally {
    isFormSaving.value = false
  }
}

async function handleDeleteMod(modId) {
  try {
    const response = await fetch(`${API_BASE}/cars/${route.params.carId}/planned-mods/${modId}`, { method: 'DELETE' })
    if (!response.ok) throw new Error()
    mods.value = mods.value.filter(mod => mod._id !== modId)
    showToast('Part removed', 'success')
  } catch {
    showToast('Failed to remove part', 'error')
  }
}

async function handleMoveMod(move) {
  if (isMoving.value) return
  isMoving.value = true
  movingModId.value = move.modId
  savedModId.value = ''
  try {
    const response = await fetch(`${API_BASE}/cars/${route.params.carId}/planned-mods/${move.modId}/move`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: move.status, position: move.position })
    })
    if (!response.ok) throw new Error()
    await fetchMods()
    movingModId.value = ''
    savedModId.value = move.modId
    window.clearTimeout(savedStateTimer)
    savedStateTimer = window.setTimeout(() => {
      savedModId.value = ''
    }, 1100)
  } catch {
    movingModId.value = ''
    showToast('Move could not be saved', 'error')
    await fetchMods()
  } finally {
    isMoving.value = false
  }
}

function openCreateForm() {
  selectedMod.value = null
  isFormOpen.value = true
}

function openEditForm(mod) {
  selectedMod.value = mod
  isFormOpen.value = true
}

function closeForm() {
  if (isFormSaving.value) return
  isFormOpen.value = false
  selectedMod.value = null
}
</script>

<style scoped>
.mods-page {
  display: flex;
  flex-direction: column;
  gap: 34px;
  width: min(100% - 40px, 1200px);
  min-height: calc(100vh - 70px);
  margin: 0 auto;
  padding: clamp(40px, 7vw, 72px) 0 80px;
}

.board-message {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: 300px;
  border: 1px dashed var(--gb-border);
  border-radius: 17px;
  color: var(--gb-text-muted);
}

.loader {
  width: 18px;
  height: 18px;
  border: 2px solid var(--gb-border-strong);
  border-top-color: var(--gb-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.error-message {
  flex-direction: column;
}

.error-message button {
  padding: 8px 14px;
  border: 1px solid var(--gb-border-strong);
  border-radius: 999px;
  background: transparent;
  color: var(--gb-accent);
  cursor: pointer;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 600px) {
  .mods-page {
    width: min(100% - 28px, 1200px);
    gap: 28px;
    padding-top: 36px;
  }
}
</style>
