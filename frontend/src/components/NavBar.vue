<template>
  <nav class="navbar">
    <div class="navbar-container">
      <router-link to="/" class="navbar-brand">
        Glovebox
      </router-link>

      <button @click="isMobileMenuOpen = !isMobileMenuOpen" class="navbar-toggle">
        ☰
      </button>

      <ul :class="['navbar-menu', { open: isMobileMenuOpen }]">
        <li>
          <router-link :to="carDetailLink" @click="isMobileMenuOpen = false">
            Dashboard
          </router-link>
        </li>
        <li>
          <router-link :to="maintenanceLink" @click="isMobileMenuOpen = false">
            Maintenance
          </router-link>
        </li>
        <li>
          <router-link :to="modsLink" @click="isMobileMenuOpen = false">
            Mods
          </router-link>
        </li>
      </ul>
    </div>
  </nav>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

const isMobileMenuOpen = ref(false)
const route = useRoute()
const carDetailLink = computed(() => {
  const carId = route.params.carId
  return carId ? `/car/${carId}` : '/car'
})
const maintenanceLink = computed(() => {
  const carId = route.params.carId
  return carId ? `/maintenance/${carId}` : '/maintenance'
})
const modsLink = computed(() => {
  const carId = route.params.carId
  return carId ? `/mods/${carId}` : '/mods'
})
</script>

<style scoped>
.navbar {
  background: #333;
  color: white;
  padding: 1rem 0;
}

.navbar-container {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 1rem;
}

.navbar-brand {
  font-size: 1.5rem;
  font-weight: bold;
  color: white;
  text-decoration: none;
}

.navbar-toggle {
  display: none;
  background: none;
  border: none;
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
}

.navbar-menu {
  display: flex;
  list-style: none;
  margin: 0;
  padding: 0;
  gap: 2rem;
}

.navbar-menu a {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
}

.navbar-menu a.router-link-active {
  background: #555;
  border-radius: 4px;
}

@media (max-width: 768px) {
  .navbar-toggle {
    display: block;
  }

  .navbar-menu {
    display: none;
    flex-direction: column;
    position: absolute;
    top: 60px;
    left: 0;
    right: 0;
    background: #333;
    padding: 1rem;
  }

  .navbar-menu.open {
    display: flex;
  }
}
</style>