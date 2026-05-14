<template>
  <article class="card">
    <div class="title-row">
      <h3 class="title">{{ log.work_done || 'Maintenance' }}</h3>
      <span class="done-by">{{ log.done_by || 'N/A' }}</span>
    </div>

    <div class="card-body">
      <div class="details">
        <p class="meta">Date: {{ log.date_of_service || 'N/A' }}</p>
        <p class="meta">Mileage: {{ log.mileage ?? 'N/A' }}</p>
        <p class="meta">Cost: {{ log.cost ?? 'N/A' }}</p>
        <p v-if="log.notes" class="meta">Notes: {{ log.notes }}</p>
      </div>

      <div class="actions">
        <button class="delete" @click="$emit('delete', log._id)">Delete</button>
      </div>
    </div>
  </article>
</template>

<script setup>
defineEmits(['delete'])

defineProps({
  log: {
    type: Object,
    required: true
  }
})
</script>

<style scoped>
.card {
  border: 1px solid #1e1e1e;
  border-radius: 12px;
  padding: 16px;
  background: #333;
}

.title-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: baseline;
  margin-bottom: 8px;
}

.card-body {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.details {
  flex: 1;
}

.actions {
  display: flex;
  align-items: flex-end;
}

.title {
  margin: 0;
  font-size: 1.05rem;
}

.done-by {
  color: #666;
  font-size: 0.9rem;
}

.meta {
  margin: 4px 0;
  color: #555;
}

.delete {
  background-color: #dc3545;
  border: none;
  color: white;
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
}
</style>