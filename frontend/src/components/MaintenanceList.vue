<template>
  <section class="maintenance-list">
    <header v-if="maintenances.length" class="list-header">
      <div>
        <h2>Service timeline</h2>
        <p>Recorded work, newest first unless sorted otherwise.</p>
      </div>
      <span>{{ maintenances.length }} {{ maintenances.length === 1 ? 'record' : 'records' }}</span>
    </header>

    <div v-if="!maintenances.length" class="empty-state">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15.2 6.6 2.2-2.2a4.3 4.3 0 0 1-5.7 5.7l-6.4 6.4a1.5 1.5 0 0 0 2.2 2.2l6.4-6.4a4.3 4.3 0 0 0 5.7-5.7l-2.2 2.2-2.2-2.2Z" /></svg>
      <strong>{{ hasRecords ? 'No matching service records' : 'No service history yet' }}</strong>
      <p>{{ hasRecords ? 'Try a different search or category.' : 'Log completed work to build a useful history for this car.' }}</p>
    </div>

    <div v-else class="timeline">
      <div v-for="log in maintenances" :key="log._id" class="timeline-entry">
        <span class="timeline-node"></span>
        <MaintenanceLogCard :log="log" @delete="$emit('delete', $event)" @edit="$emit('edit', $event)" />
      </div>
    </div>
  </section>
</template>

<script setup>
import MaintenanceLogCard from './MaintenanceLogCard.vue'

defineEmits(['delete', 'edit'])

defineProps({
  maintenances: {
    type: Array,
    default: () => []
  },
  hasRecords: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.maintenance-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.list-header { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; }
.list-header h2 { color: var(--gb-heading); font-size: 1rem; font-weight: 680; }
.list-header p { margin-top: 2px; color: var(--gb-text-muted); font-size: .76rem; }
.list-header > span { color: var(--gb-text-muted); font-size: .74rem; }

.timeline { position: relative; display: flex; flex-direction: column; gap: 12px; padding-left: 18px; }
.timeline::before { position: absolute; top: 18px; bottom: 18px; left: 4px; width: 1px; background: rgba(179, 199, 255, .13); content: ''; }
.timeline-entry { position: relative; }
.timeline-node { position: absolute; z-index: 1; top: 23px; left: -18px; width: 9px; height: 9px; border: 2px solid var(--gb-background); border-radius: 50%; background: #718abe; }

.empty-state {
  display: flex;
  align-items: center;
  flex-direction: column;
  padding: 48px 24px;
  border: 1px dashed rgba(179, 199, 255, .18);
  border-radius: 10px;
  color: var(--gb-text-muted);
  text-align: center;
}
.empty-state svg { width: 25px; height: 25px; margin-bottom: 10px; fill: none; stroke: var(--gb-accent); stroke-linecap: round; stroke-linejoin: round; stroke-width: 1.4; }
.empty-state strong { color: var(--gb-heading); font-size: .9rem; font-weight: 650; }
.empty-state p { margin-top: 3px; font-size: .78rem; }
</style>
