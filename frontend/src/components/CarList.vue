<template>
  <section class="garage-container">
    <div class="garage-header">
      <div>
        <h2>Garage</h2>
        <p>Your saved vehicles</p>
      </div>
      <span class="car-count">{{ inventory.length }} {{ inventory.length === 1 ? 'car' : 'cars' }}</span>
    </div>

    <div v-if="inventory.length" class="car-grid">
      <article v-for="car in inventory" :key="car._id" class="car-card">
        <div class="car-info-main">{{ car.make }} {{ car.model }}</div>
        <div class="car-tags">
          <span>{{ car.year || 'Year N/A' }}</span>
          <span v-if="car.fuel_type">{{ formatFuel(car.fuel_type) }}</span>
        </div>
        <div class="car-stats">
          <span>Odometer</span>
          <strong>{{ car.mileage !== null && car.mileage !== undefined ? formatMileage(car.mileage) : 'N/A' }}</strong>
        </div>

        <div class="card-actions">
          <button class="view" type="button" @click="emit('view', car._id)">View vehicle →</button>
          <button class="delete" type="button" @click="emit('delete', car._id)">Delete</button>
        </div>
      </article>

      <button type="button" class="add-car-card" @click="emit('add')">
        <span class="plus">+</span>
        <span>Add a new car</span>
      </button>
    </div>

    <div v-else class="empty-state">
      <p>Your garage is empty.</p>
      <button type="button" class="add-car-card" @click="emit('add')">
        <span class="plus">+</span>
        <span>Add your first car</span>
      </button>
    </div>
  </section>
</template>

<script setup>
const emit = defineEmits(['view', 'delete', 'add'])

defineProps({
  inventory: {
    type: Array,
    default: () => []
  }
})

const numberFormatter = new Intl.NumberFormat('en-US')

function formatMileage(mileage) {
  return `${numberFormatter.format(mileage)} miles`
}

function formatFuel(fuelType) {
  return fuelType.charAt(0).toUpperCase() + fuelType.slice(1)
}
</script>

<style scoped>
.garage-container {
  padding-top: 30px;
  border-top: 1px solid #2d3748;
}

.garage-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 28px;
}

.garage-header h2 {
  color: white;
  font-size: clamp(1.6rem, 3vw, 2rem);
  font-weight: 600;
  line-height: 1.2;
}

.garage-header p {
  margin-top: 4px;
  color: #a0aec0;
  font-size: 0.9rem;
}

.car-count {
  padding: 7px 12px;
  border: 1px solid #2d3748;
  border-radius: 999px;
  color: #a0aec0;
  font-size: 0.76rem;
}

.car-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 18px;
}

.car-card,
.add-car-card {
  min-height: 220px;
  border-radius: 16px;
}

.car-card {
  display: flex;
  flex-direction: column;
  padding: 24px;
  border: 1px solid #2d3748;
  background: #23272e;
  transition: transform 0.15s ease, border-color 0.15s ease;
}

.car-card:hover {
  transform: translateY(-2px);
  border-color: #b3c7ff;
}

.car-info-main {
  margin-bottom: 12px;
  color: white;
  font-size: 1.25rem;
  font-weight: 600;
}

.car-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.car-tags span {
  padding: 5px 10px;
  border: 1px solid #3a4557;
  border-radius: 999px;
  color: #b3c7ff;
  font-size: 0.7rem;
  font-weight: 600;
}

.car-stats {
  margin-top: 22px;
}

.car-stats span,
.car-stats strong {
  display: block;
}

.car-stats span {
  color: #7f8b9f;
  font-size: 0.72rem;
  text-transform: uppercase;
}

.car-stats strong {
  margin-top: 3px;
  color: #c1c3c9;
  font-size: 0.95rem;
  font-weight: 500;
}

.card-actions {
  display: flex;
  gap: 8px;
  margin-top: auto;
  padding-top: 20px;
}

.view,
.delete {
  border: 0;
  font-weight: 600;
  cursor: pointer;
}

.view {
  padding: 8px 0;
  background: transparent;
  color: #b3c7ff;
}

.view:hover {
  color: white;
}

.delete {
  margin-left: auto;
  padding: 8px 10px;
  border-radius: 6px;
  background: transparent;
  color: #7f8b9f;
}

.delete:hover {
  background: rgba(231, 76, 60, 0.1);
  color: #ef8b80;
}

.add-car-card {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 20px;
  border: 1px dashed #3a4557;
  background: rgba(35, 39, 46, 0.45);
  color: #a0aec0;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.add-car-card:hover {
  border-color: #b3c7ff;
  background: rgba(179, 199, 255, 0.05);
  color: #b3c7ff;
}

.plus {
  font-size: 1.4rem;
  font-weight: 400;
}

.empty-state {
  padding: 24px 0 4px;
  color: #a0aec0;
  text-align: center;
}

.empty-state .add-car-card {
  width: min(100%, 320px);
  min-height: 130px;
  margin: 20px auto 0;
}

@media (max-width: 520px) {
  .garage-header {
    align-items: flex-start;
    flex-direction: column;
  }

}
</style>
