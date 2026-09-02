<template>
  <div class="app-container">
    <Toast />

    <header class="site-header">
      <div class="header-inner">
        <a class="site-title" href="/">
          <img class="logo-mark" src="/Glovebox.png" alt="" />
          <span>Glovebox</span>
        </a>

        <nav aria-label="Main navigation">
          <a class="active" href="/">Garage</a>
        </nav>

        <button type="button" class="header-add-button" @click="handleShowCarForm">
          Add car
        </button>
      </div>
    </header>

    <main class="main-container">
      <section class="page-intro">
        <span class="intro-label">Vehicle management</span>
        <h1>Your garage, made simple</h1>
        <p>Keep your cars and maintenance history organized in one place.</p>
      </section>

      <CarList
        :inventory="cars"
        class="car-list-section"
        @add="handleShowCarForm"
        @delete="handleDeleteCar"
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
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import CarForm from '../components/CarForm.vue'
import CarList from '../components/CarList.vue'
import Toast, { showToast } from '../components/Toast.vue'

const envApiBase = import.meta.env.VITE_API_BASE_URL?.trim()
const API_BASE = envApiBase || `${window.location.protocol}//${window.location.hostname}:8000`
const router = useRouter()
const cars = ref([])
const isCarFormVisible = ref(false)

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
}

function handleCarCreated(car) {
  cars.value = [...cars.value, car]
  handleCloseCarForm()
}

async function handleDeleteCar(carId) {
  const response = await fetch(`${API_BASE}/cars/${carId}`, {
    method: 'DELETE'
  })
  if (!response.ok) {
    showToast('Failed to delete car', 'error')
    return
  }

  cars.value = cars.value.filter(existingCar => existingCar._id !== carId)
  showToast('Car deleted successfully', 'success')
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  width: 100%;
  color: #c1c3c9;
  background: #161a20;
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

.site-title:hover,
.header-inner nav a:hover {
  background: transparent;
}

.logo-mark {
  width: 42px;
  height: 42px;
  object-fit: contain;
}

.header-inner nav {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-inner nav a {
  padding: 8px 10px;
  color: #a0aec0;
  font-size: 0.9rem;
}

.header-inner nav a.active {
  color: white;
}

.header-add-button {
  margin-left: auto;
  padding: 10px 18px;
  border: 0;
  border-radius: 999px;
  background: #b3c7ff;
  color: #141820;
  font-size: 0.86rem;
  font-weight: 700;
  cursor: pointer;
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
  }

  .header-inner nav {
    display: none;
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
