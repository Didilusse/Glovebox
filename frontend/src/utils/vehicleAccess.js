import { computed, onBeforeUnmount, provide, ref } from 'vue'
import { auth } from './auth'

export const vehicleAccessKey = Symbol('vehicleAccess')

export function canAccess(car, section, edit = false) {
  if (car?.access?.is_owner) return true
  const level = car?.access?.permissions?.[section]
  return edit ? level === 'edit' : level === 'view' || level === 'edit'
}

export function provideVehicleAccess(car) {
  const version = auth.version
  const active = ref(true)
  onBeforeUnmount(() => { active.value = false })
  const currentCar = computed(() => active.value && auth.version === version ? car.value : null)
  provide(vehicleAccessKey, currentCar)
  return {
    isOwner: computed(() => currentCar.value?.access?.is_owner === true),
    canView: section => canAccess(currentCar.value, section),
    canEdit: section => canAccess(currentCar.value, section, true)
  }
}
