<template>
  <div class="app-container">

    <header class="site-header">
      <div class="header-inner">
        <a class="site-title" href="/">
          <img class="logo-mark" src="/Glovebox.png" alt="" />
          <span>Glovebox</span>
        </a>

        <div class="header-actions">
          <button type="button" class="header-add-button" @click="handleShowCarForm">
            Add car
          </button>
          <AccountControls />
        </div>
      </div>
    </header>

    <main class="main-container">
      <section class="page-intro">
        <span class="intro-label">Vehicle management</span>
        <h1>Your garage, made simple</h1>
        <p>Keep your cars and maintenance history organized in one place.</p>
      </section>

      <DueAlerts />
      <CarList
        :inventory="cars"
        class="car-list-section"
        @add="handleShowCarForm"
        @delete="requestDeleteCar"
        @view="handleViewCar"
      />

      <transition name="fade">
        <div
          v-if="isCarFormVisible"
          class="popup-overlay"
          @click.self="handleCloseCarForm"
        >
          <CarForm
            :api-base="API_BASE"
            @created="handleCarCreated"
            @close="handleCloseCarForm"
          />
        </div>
      </transition>

      <VehicleDialog v-if="carPendingDelete" title="Delete vehicle" @close="cancelDeleteCar">
        <div class="delete-confirmation">
          <p>Delete <strong>{{ carPendingDelete.year }} {{ carPendingDelete.make }} {{ carPendingDelete.model }}</strong>?</p>
          <p>This permanently removes the vehicle, its maintenance history, reminders, and planned modifications. This cannot be undone.</p>
          <div class="dialog-actions">
            <button type="button" :disabled="isDeletingCar" @click="cancelDeleteCar">Cancel</button>
            <button type="button" class="confirm-delete" :disabled="isDeletingCar" @click="confirmDeleteCar">
              {{ isDeletingCar ? 'Deleting...' : 'Delete vehicle' }}
            </button>
          </div>
        </div>
      </VehicleDialog>
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import CarForm from '../components/CarForm.vue'
import CarList from '../components/CarList.vue'
import { showToast } from '../components/Toast.vue'
import AccountControls from '../components/AccountControls.vue'
import DueAlerts from '../components/DueAlerts.vue'
import VehicleDialog from '../components/VehicleDialog.vue'
import { API_BASE, useApiClient } from '../utils/auth'

const fetch = useApiClient()
const router = useRouter()
const cars = ref([])
const isCarFormVisible = ref(false)
const carPendingDelete = ref(null)
const isDeletingCar = ref(false)

onMounted(handleFetchCars)

function handleViewCar(carId) {
  router.push(`/car/${carId}`)
}

function handleShowCarForm() {
  isCarFormVisible.value = true
}

function handleCloseCarForm() {
  isCarFormVisible.value = false
}

async function handleFetchCars() {
  try {
    const fetchedCars = []
    const pageSize = 100

    while (true) {
      const response = await fetch(`${API_BASE}/cars/?skip=${fetchedCars.length}&limit=${pageSize}`)
      if (!response.ok) {
        showToast('Failed to fetch cars', 'error')
        return
      }

      const page = await response.json()
      fetchedCars.push(...page)
      if (page.length < pageSize) break
    }

    cars.value = fetchedCars
  } catch (error) {
    if (error.name !== 'AbortError') showToast('Unable to load your garage. Please reload to try again.', 'error')
  }
}

function handleCarCreated(car) {
  cars.value = [...cars.value, car]
  handleCloseCarForm()
}

function requestDeleteCar(carId) {
  const car = cars.value.find(existingCar => existingCar._id === carId)
  if (car?.access?.is_owner) carPendingDelete.value = car
}

function cancelDeleteCar() {
  if (!isDeletingCar.value) carPendingDelete.value = null
}

async function confirmDeleteCar() {
  if (!carPendingDelete.value || isDeletingCar.value) return
  const carId = carPendingDelete.value._id
  isDeletingCar.value = true
  try {
    const response = await fetch(`${API_BASE}/cars/${carId}`, {
      method: 'DELETE'
    })
    if (!response.ok) {
      showToast('Failed to delete car', 'error')
      return
    }

    cars.value = cars.value.filter(existingCar => existingCar._id !== carId)
    carPendingDelete.value = null
    showToast('Car deleted successfully', 'success')
  } catch (error) {
    if (error.name !== 'AbortError') showToast('Failed to delete car', 'error')
  } finally {
    isDeletingCar.value = false
  }
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  width: 100%;
  color: #c1c3c9;
  background: #161a20;
}

.delete-confirmation {
  display: grid;
  gap: 12px;
}

.delete-confirmation p {
  margin: 0;
  color: var(--gb-text-muted);
  line-height: 1.6;
}

.delete-confirmation strong {
  color: var(--gb-heading);
}

.delete-confirmation .dialog-actions {
  justify-content: flex-end;
  margin-top: 10px;
}

.delete-confirmation .confirm-delete {
  border-color: rgba(239, 139, 128, 0.45);
  background: rgba(239, 139, 128, 0.12);
  color: #ef8b80;
}

.delete-confirmation .confirm-delete:hover:not(:disabled) {
  border-color: #ef8b80;
  background: rgba(239, 139, 128, 0.2);
}

.site-header {
  border-bottom: 1px solid #2d3748;
  background: #11151b;
}

.header-inner {
  width: min(100% - 40px, 1200px);
  min-height: 70px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 36px;
}

.site-title {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 0;
  color: white;
  font-size: 1.15rem;
  font-weight: 700;
}

  .site-title:hover {
  background: transparent;
}

.logo-mark {
  width: 42px;
  height: 42px;
  object-fit: contain;
}

.header-add-button {
  padding: 10px 18px;
  border: 0;
  border-radius: 999px;
  background: #b3c7ff;
  color: #141820;
  font-size: 0.86rem;
  font-weight: 700;
  cursor: pointer;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.header-add-button:hover {
  background: #cad7ff;
}

.main-container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: clamp(40px, 7vw, 76px) 20px 80px;
}

.page-intro {
  max-width: 680px;
  margin-bottom: 52px;
}

.intro-label {
  display: inline-block;
  margin-bottom: 14px;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(179, 199, 255, 0.1);
  color: #b3c7ff;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.page-intro h1 {
  color: white;
  font-size: clamp(2.2rem, 5vw, 3.8rem);
  font-weight: 700;
  line-height: 1.08;
  letter-spacing: -0.035em;
}

.page-intro p {
  margin-top: 18px;
  color: #a0aec0;
  font-size: 1.05rem;
}

.car-list-section {
  width: 100%;
}

.popup-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  overflow-y: auto;
  padding: 72px 24px 24px;
  background: rgba(0, 0, 0, 0.65);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 600px) {
  .header-inner {
    width: min(100% - 28px, 1200px);
    gap: 16px;
    flex-wrap: wrap;
    padding: 12px 0;
  }

  .header-actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .header-actions :deep(.account-controls) {
    flex-basis: 100%;
  }

  .header-add-button {
    padding: 9px 14px;
  }

  .main-container {
    padding: 38px 14px 56px;
  }

  .page-intro {
    margin-bottom: 36px;
  }

  .popup-overlay {
    padding: 24px 12px;
  }
}
</style>
