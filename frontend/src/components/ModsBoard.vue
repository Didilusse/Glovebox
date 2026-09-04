<template>
  <section class="board" aria-label="Modification planner">
    <div v-for="column in columns" :key="column.status" class="column" :class="`column-${column.status}`">
      <header>
        <div>
          <span class="status-dot"></span>
          <div class="column-title">
            <h2>{{ column.label }}</h2>
            <p>{{ column.description }}</p>
          </div>
        </div>
        <div class="column-total">
          <strong>{{ money(columnCost(column.status)) }}</strong>
          <span>{{ itemsByStatus[column.status].length }} {{ itemsByStatus[column.status].length === 1 ? 'part' : 'parts' }}</span>
        </div>
      </header>

      <div class="drop-zone">
        <draggable
          v-model="itemsByStatus[column.status]"
          class="card-list"
          :class="{ disabled }"
          item-key="_id"
          group="mods-board"
          handle=".drag-handle"
          ghost-class="drag-ghost"
          chosen-class="drag-chosen"
          drag-class="drag-active"
          :animation="180"
          :disabled="disabled"
          @change="handleChange($event, column.status)"
        >
          <template #item="{ element }">
            <ModCard
              :mod="element"
              :is-saving="movingId === element._id"
              :is-saved="savedId === element._id"
              @edit="$emit('edit', $event)"
              @delete="$emit('delete', $event)"
            />
          </template>
        </draggable>
        <div v-if="itemsByStatus[column.status].length === 0" class="empty-column">
          <span>Drop a part here</span>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { reactive, watch } from 'vue'
import draggable from 'vuedraggable'
import ModCard from './ModCard.vue'

const props = defineProps({
  mods: {
    type: Array,
    default: () => []
  },
  disabled: {
    type: Boolean,
    default: false
  },
  movingId: {
    type: String,
    default: ''
  },
  savedId: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['move', 'edit', 'delete'])
const columns = [
  { status: 'planned', label: 'Planned', description: 'Research and budget' },
  { status: 'purchased', label: 'Purchased', description: 'Ready for install' },
  { status: 'installed', label: 'Installed', description: 'Completed work' }
]
const itemsByStatus = reactive({
  planned: [],
  purchased: [],
  installed: []
})

watch(
  () => props.mods,
  (mods) => {
    for (const column of columns) {
      itemsByStatus[column.status] = mods
        .filter(mod => mod.status === column.status)
        .sort((a, b) => a.position - b.position || a._id.localeCompare(b._id))
    }
  },
  { immediate: true }
)

function handleChange(event, status) {
  const change = event.added ?? event.moved
  if (!change) return

  emit('move', {
    modId: change.element._id,
    status,
    position: change.newIndex
  })
}

function columnCost(status) {
  return itemsByStatus[status].reduce((total, mod) => total + (Number(mod.cost) || 0), 0)
}

function money(value) {
  return new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)
}
</script>

<style scoped>
.board {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  align-items: start;
}

.column {
  min-width: 0;
  padding: 14px;
  border: 1px solid var(--gb-border);
  border-radius: 17px;
  background: color-mix(in srgb, var(--gb-background-deep) 82%, transparent);
}

.column > header,
.column > header > div {
  display: flex;
  align-items: center;
}

.column > header {
  justify-content: space-between;
  min-height: 48px;
  margin-bottom: 12px;
  padding: 0 2px;
}

.column > header > div {
  gap: 9px;
}

.column-title p {
  margin-top: 1px;
  color: var(--gb-text-muted);
  font-size: 0.7rem;
}

.column h2 {
  color: var(--gb-heading);
  font-size: 0.9rem;
  font-weight: 650;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #86a8ff;
  box-shadow: 0 0 0 4px rgba(134, 168, 255, 0.1);
}

.column-purchased .status-dot {
  background: #e0b86e;
  box-shadow: 0 0 0 4px rgba(224, 184, 110, 0.1);
}

.column-installed .status-dot {
  background: #6ec79e;
  box-shadow: 0 0 0 4px rgba(110, 199, 158, 0.1);
}

.column-total {
  text-align: center;
}

.column-total strong,
.column-total span { display: block; text-align: right; }
.column-total strong { color: var(--gb-heading); font-size: 0.8rem; font-weight: 650; }
.column-total span { color: var(--gb-text-muted); font-size: 0.68rem; }

.drop-zone {
  position: relative;
  min-height: 116px;
}

.card-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 116px;
}

.card-list.disabled {
  opacity: 0.75;
}

.empty-column {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  border: 1px dashed var(--gb-border);
  border-radius: 12px;
  color: var(--gb-text-muted);
  font-size: 0.82rem;
  pointer-events: none;
}

:deep(.drag-ghost) {
  opacity: 0.35;
  border-color: var(--gb-accent);
}

:deep(.drag-chosen) {
  border-color: var(--gb-accent);
}

:deep(.drag-active) {
  transform: rotate(1deg);
}

@media (max-width: 850px) {
  .board {
    display: flex;
    width: calc(100vw - 14px);
    margin-right: calc((100vw - 100%) / -2);
    margin-left: calc((100vw - 100%) / -2);
    padding: 0 14px 12px;
    overflow-x: auto;
    scroll-snap-type: x proximity;
  }

  .column {
    width: min(84vw, 340px);
    flex: 0 0 min(84vw, 340px);
    scroll-snap-align: start;
  }
}
</style>
