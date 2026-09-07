import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import CarDetailView from '../views/CarDetailView.vue'
import MaintenanceView from '../views/MaintenanceView.vue'
import ModsView from "../views/ModsView.vue"
import NhtsaView from "../views/NhtsaView.vue"
import AuthView from '../views/AuthView.vue'
import WelcomeView from '../views/WelcomeView.vue'
import AccountView from '../views/AccountView.vue'
import AdminView from '../views/AdminView.vue'
import { authGuard } from './authGuard'

const routes = [
  { path: '/auth', component: AuthView },
  { path: '/login', component: AuthView },
  { path: '/setup', component: AuthView },
  { path: '/welcome', component: WelcomeView },
  { path: '/account', component: AccountView },
  { path: '/admin', component: AdminView, meta: { admin: true } },
  { path: '/:pathMatch(.*)*', redirect: '/' },
  { path: '/', component: HomeView },
  { path: '/car/:carId', component: CarDetailView },
  { path: '/maintenance/:carId', component: MaintenanceView },
  { path: '/mods/:carId', component: ModsView },
  { path: '/nhtsa/:carId', component: NhtsaView }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})
router.beforeEach(authGuard)

export default router
