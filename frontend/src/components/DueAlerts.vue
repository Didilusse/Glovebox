<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue'
import { useApiRequest } from '../utils/auth'
const request = useApiRequest()
const reminders = ref([])
const loading = ref(true)
const error = ref(false)
let timer
async function load() {
  loading.value = true; error.value = false
  try { reminders.value = await request('/reminders/due', undefined, 'GET') }
  catch (e) { if (e.name !== 'AbortError') error.value = true }
  finally { loading.value = false }
}
onMounted(() => { load(); timer = setInterval(() => { if (!loading.value) load() }, 60000) })
onBeforeUnmount(() => clearInterval(timer))
</script>
<template>
  <section class="due-alerts" aria-labelledby="due-alerts-title">
    <h2 id="due-alerts-title">Service due</h2>
    <p v-if="loading" role="status">Checking reminders...</p>
    <p v-if="error" role="alert">Unable to check due reminders. <button @click="load" :disabled="loading">Retry</button></p>
    <p v-else-if="!loading && !reminders.length">No services currently due.</p>
    <div class="due-grid">
      <router-link v-for="r in reminders" :key="`${r.car_id}-${r.log_id}`" :to="`/car/${r.car_id}?tab=reminders`" class="due-card" :class="{ overdue: r.is_overdue }">
        <strong>{{ r.is_overdue ? 'Overdue' : 'Due' }}: {{ r.work_done }}</strong>
        <span>{{ r.car_name }}</span>
        <span v-if="r.reminder_mileage != null">Due at {{ r.reminder_mileage }} mi</span>
        <span v-if="r.reminder_date">Due {{ r.reminder_date }}</span>
        <span>View reminders &rarr;</span>
      </router-link>
    </div>
  </section>
</template>
<style scoped>
.due-alerts { margin-bottom: 36px; }
h2 { color: var(--gb-heading); margin-bottom: 12px; }
.due-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 260px), 1fr)); gap: 14px; }
.due-card { display: grid; gap: 6px; padding: 20px; background: var(--gb-surface); border: 1px solid var(--gb-accent); border-radius: 12px; overflow-wrap: anywhere; }
.overdue { border-color: var(--gb-danger); }
.overdue strong, [role=alert] { color: var(--gb-danger); }
</style>
