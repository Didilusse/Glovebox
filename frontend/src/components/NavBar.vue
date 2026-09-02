<template>
  <nav class="navbar">
    <div class="navbar-container">
      <router-link to="/" class="navbar-brand">
        <img src="/Glovebox.png" alt="" />
        <span>Glovebox</span>
      </router-link>

      <button
        type="button"
        class="navbar-toggle"
        :aria-expanded="isMobileMenuOpen"
        aria-label="Toggle navigation"
        @click="isMobileMenuOpen = !isMobileMenuOpen"
      >
        <span></span>
        <span></span>
        <span></span>
      </button>

      <ul :class="['navbar-menu', { open: isMobileMenuOpen }]">
        <li>
          <router-link :to="carDetailLink" @click="isMobileMenuOpen = false">Dashboard</router-link>
        </li>
        <li>
          <router-link :to="maintenanceLink" @click="isMobileMenuOpen = false">Maintenance</router-link>
        </li>
        <li>
          <router-link :to="modsLink" @click="isMobileMenuOpen = false">Mods</router-link>
        </li>
      </ul>
    </div>
  </nav>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'

const isMobileMenuOpen = ref(false)
const route = useRoute()
const carDetailLink = computed(() => route.params.carId ? `/car/${route.params.carId}` : '/car')
const maintenanceLink = computed(() => route.params.carId ? `/maintenance/${route.params.carId}` : '/maintenance')
const modsLink = computed(() => route.params.carId ? `/mods/${route.params.carId}` : '/mods')
</script>

<style scoped>
.navbar {
  position: relative;
  z-index: 20;
  border-bottom: 1px solid var(--gb-border);
  background: var(--gb-background-deep);
}

.navbar-container {
  width: min(100% - 40px, 1200px);
  min-height: 70px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 36px;
}

.navbar-brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 0;
  color: var(--gb-heading);
  font-size: 1.15rem;
  font-weight: 700;
}

.navbar-brand:hover {
  background: transparent;
}

.navbar-brand img {
  width: 42px;
  height: 42px;
  object-fit: contain;
}

.navbar-menu {
  display: flex;
  gap: 6px;
  margin: 0 0 0 auto;
  padding: 0;
  list-style: none;
}

.navbar-menu a {
  display: block;
  padding: 8px 12px;
  border-radius: 8px;
  color: var(--gb-text-muted);
  font-size: 0.9rem;
}

.navbar-menu a:hover {
  color: var(--gb-heading);
}

.navbar-menu a.router-link-active {
  background: rgba(179, 199, 255, 0.1);
  color: var(--gb-accent);
}

.navbar-toggle {
  display: none;
  width: 40px;
  height: 40px;
  margin-left: auto;
  border: 1px solid var(--gb-border);
  border-radius: 8px;
  background: var(--gb-surface);
  cursor: pointer;
}

.navbar-toggle span {
  width: 17px;
  height: 1px;
  display: block;
  margin: 4px auto;
  background: var(--gb-text);
}

@media (max-width: 700px) {
  .navbar-container {
    width: min(100% - 28px, 1200px);
  }

  .navbar-toggle {
    display: block;
  }

  .navbar-menu {
    display: none;
    position: absolute;
    top: 70px;
    left: 0;
    right: 0;
    flex-direction: column;
    padding: 12px 14px 16px;
    border-bottom: 1px solid var(--gb-border);
    background: var(--gb-background-deep);
  }

  .navbar-menu.open {
    display: flex;
  }
}
</style>
