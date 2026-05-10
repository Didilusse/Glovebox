import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import CarDetailView from '../views/CarDetailView.vue'

const routes = [
  { path: '/', component: HomeView },
  { path: '/car/:carId', component: CarDetailView }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router