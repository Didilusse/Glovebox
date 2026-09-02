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
        <p v-if="log.service_provider" class="meta">Provider: {{ log.service_provider }}</p>
        <p v-if="log.source" class="meta source">Imported from {{ log.source.toUpperCase() }}</p>
        <p v-if="log.reminder_date || log.reminder_mileage" class="meta">Reminder: {{ log.reminder_date ? log.reminder_date : '' }} {{ log.reminder_mileage ? `(at ${log.reminder_mileage} miles)` : '' }}</p>
        <p v-if="log.notes" class="meta">Notes: {{ log.notes }}</p>
      </div>

      <div class="actions">
        <button class="delete" @click="$emit('delete', log._id)">Delete</button>
        <button class="secondary" @click="$emit('edit', log)">Edit</button>
      </div>
    </div>
  </article>
</template>

<script setup>
defineEmits(['delete', 'edit'])

defineProps({
  log: {
    type: Object,
    required: true
  }
})
</script>

<style scoped>
.card {
  border: 1px solid var(--gb-border);
  border-radius: 16px;
  padding: 20px;
  background: var(--gb-surface);
  transition: border-color 0.2s ease;
}

.card:hover {
  border-color: var(--gb-border-strong);
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
  gap: 8px;
  align-items: flex-end;
}

.title {
  margin: 0;
  color: var(--gb-heading);
  font-size: 1.1rem;
  font-weight: 600;
}

.done-by {
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(179, 199, 255, 0.08);
  color: var(--gb-accent);
  font-size: 0.72rem;
  text-transform: capitalize;
}

.meta {
  margin: 4px 0;
  color: var(--gb-text-muted);
  font-size: 0.9rem;
}

.source {
  color: var(--gb-accent);
  font-size: 0.76rem;
}

.delete {
  background-color: transparent;
  border: none;
  color: var(--gb-danger);
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
}

.delete:hover {
  background: rgba(231, 76, 60, 0.1);
}

.secondary {
  padding: 6px 12px;
  border: 1px solid var(--gb-border-strong);
  border-radius: 8px;
  background: transparent;
  color: var(--gb-accent);
  cursor: pointer;
}

.secondary:hover {
  border-color: var(--gb-accent);
}

@media (max-width: 600px) {
  .card-body {
    flex-direction: column;
  }

  .actions {
    align-items: center;
  }
}
</style>
