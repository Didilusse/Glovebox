import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import CarDetailView from '../views/CarDetailView.vue'
import MaintenanceView from '../views/MaintenanceView.vue'
import ModsView from "../views/ModsView.vue"

const routes = [
  { path: '/', component: HomeView },
  { path: '/car/:carId', component: CarDetailView },
  { path: '/maintenance/:carId', component: MaintenanceView },
  { path: '/mods/:carId', component: ModsView }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router