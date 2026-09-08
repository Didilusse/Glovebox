<template>
  <article class="mod-card" :class="[`priority-${mod.priority || 'medium'}`, { saving: isSaving, saved: isSaved }]">
    <div class="card-heading">
      <div class="identity">
        <span class="category">{{ categoryLabel }}</span>
        <h3>{{ mod.name }}</h3>
        <p v-if="identityLine">{{ identityLine }}</p>
      </div>
      <div class="cost">
        <span>Part cost</span>
        <strong>{{ formattedCost }}</strong>
      </div>
    </div>

    <div class="planning-meta">
      <span class="priority"><i></i>{{ priorityLabel }}</span>
      <span title="Install method">
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="m12.7 5.5 1.8-1.8a3.6 3.6 0 0 1-4.7 4.7l-5.4 5.4a1.3 1.3 0 0 0 1.8 1.8l5.4-5.4a3.6 3.6 0 0 0 4.7-4.7l-1.8 1.8-1.8-1.8Z" /></svg>
        {{ installLabel }}
      </span>
      <span v-if="mod.target_date" :class="{ overdue: isOverdue }" title="Target date">
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5 3v3m10-3v3M3.5 8.5h13M5 4.5h10a2 2 0 0 1 2 2V16H3V6.5a2 2 0 0 1 2-2Z" /></svg>
        {{ formattedDate }}
      </span>
    </div>

    <p v-if="mod.notes" class="notes">{{ mod.notes }}</p>

    <footer>
      <a v-if="mod.url" :href="mod.url" target="_blank" rel="noopener noreferrer">
        View part
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M7 13 13 7m-4 0h4v4M12 4h4v12H4V4h5" /></svg>
      </a>
      <span v-else class="no-link">No product link</span>
      <div v-if="!readOnly" class="actions">
        <button type="button" class="edit" aria-label="Edit part" title="Edit part" @click="$emit('edit', mod)">
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d="m12 4 4 4-8 8H4v-4l8-8Zm-2 2 4 4" /></svg>
        </button>
        <button type="button" class="delete" aria-label="Delete part" title="Delete part" @click="$emit('delete', mod._id)">
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 6h12M8 3h4l1 3H7l1-3Zm-2 3 1 11h6l1-11M9 9v5m2-5v5" /></svg>
        </button>
        <span class="drag-handle" title="Drag to move" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i></span>
      </div>
    </footer>

    <div v-if="isSaving || isSaved" class="state-feedback" aria-live="polite">
      <span v-if="isSaving" class="spinner"></span>
      <svg v-else viewBox="0 0 20 20" aria-hidden="true"><path d="m5 10 3 3 7-7" /></svg>
      {{ isSaving ? 'Saving move' : 'Move saved' }}
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  readOnly: Boolean,
  mod: { type: Object, required: true },
  isSaving: { type: Boolean, default: false },
  isSaved: { type: Boolean, default: false }
})

defineEmits(['edit', 'delete'])

const categoryLabel = computed(() => titleCase(props.mod.category || 'other'))
const priorityLabel = computed(() => `${titleCase(props.mod.priority || 'medium')} priority`)
const installLabel = computed(() => ({ diy: 'DIY install', shop: 'Shop install', undecided: 'Install TBD' })[props.mod.install_method] || 'Install TBD')
const identityLine = computed(() => [props.mod.brand, props.mod.part_number].filter(Boolean).join(' / '))
const formattedCost = computed(() => new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(Number(props.mod.cost) || 0))
const formattedDate = computed(() => new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${props.mod.target_date}T00:00:00Z`)))
const isOverdue = computed(() => props.mod.status !== 'installed' && props.mod.target_date && props.mod.target_date < new Date().toISOString().slice(0, 10))

function titleCase(value) {
  return value.charAt(0).toUpperCase() + value.slice(1)
}
</script>

<style scoped>
.mod-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px;
  overflow: hidden;
  border: 1px solid rgba(179, 199, 255, 0.1);
  border-radius: 10px;
  background: #242a32;
  transition: border-color 150ms, background 150ms, transform 150ms;
}

.mod-card:hover { border-color: rgba(179, 199, 255, 0.22); background: #272e37; }
.mod-card.saved { border-color: rgba(110, 199, 158, 0.45); }
.mod-card.saving { pointer-events: none; }

.card-heading,
footer,
.actions,
.planning-meta,
.planning-meta span,
.state-feedback {
  display: flex;
  align-items: center;
}

.card-heading { align-items: flex-start; justify-content: space-between; gap: 12px; }
.identity { min-width: 0; }

.category {
  color: var(--gb-accent);
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

h3 {
  margin-top: 3px;
  color: var(--gb-heading);
  font-size: 1rem;
  font-weight: 680;
  letter-spacing: -0.015em;
  line-height: 1.25;
}

.identity p { margin-top: 4px; color: var(--gb-text-muted); font-size: 0.75rem; }

.cost { flex: 0 0 auto; text-align: right; }
.cost span { display: block; color: var(--gb-text-muted); font-size: 0.65rem; }
.cost strong { color: var(--gb-accent); font-size: 0.95rem; font-weight: 700; }

.planning-meta { flex-wrap: wrap; gap: 7px 12px; }
.planning-meta span { gap: 5px; color: #aeb7c5; font-size: 0.72rem; }
.planning-meta svg { width: 14px; height: 14px; fill: none; stroke: currentColor; stroke-linecap: round; stroke-linejoin: round; stroke-width: 1.5; }
.planning-meta .priority i { width: 6px; height: 6px; border-radius: 50%; background: #e0b86e; }
.priority-high .planning-meta .priority i { background: #ef8b80; }
.priority-low .planning-meta .priority i { background: #8995a5; }
.planning-meta .overdue { color: #ef9a91; }

.notes {
  display: -webkit-box;
  overflow: hidden;
  color: var(--gb-text-muted);
  font-size: 0.8rem;
  line-height: 1.5;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

footer { justify-content: space-between; gap: 12px; padding-top: 2px; }
footer > a, .no-link { color: var(--gb-text-muted); font-size: 0.72rem; }
footer > a { display: flex; align-items: center; gap: 4px; color: var(--gb-accent); text-decoration: none; }
footer > a:hover { color: var(--gb-accent-hover); }
footer > a svg { width: 13px; height: 13px; fill: none; stroke: currentColor; stroke-linecap: round; stroke-linejoin: round; stroke-width: 1.5; }

.actions { gap: 4px; }
.actions button { display: grid; width: 28px; height: 28px; padding: 0; place-items: center; border: 0; border-radius: 6px; background: transparent; color: var(--gb-text-muted); cursor: pointer; }
.actions button:hover { background: #343c47; color: var(--gb-heading); }
.actions button:active { transform: translateY(1px); }
.actions button:focus-visible { outline: 2px solid var(--gb-accent); outline-offset: 1px; }
.actions .delete:hover { color: var(--gb-danger); }
.actions svg { width: 15px; height: 15px; fill: none; stroke: currentColor; stroke-linecap: round; stroke-linejoin: round; stroke-width: 1.5; }

.drag-handle { display: grid; grid-template-columns: repeat(2, 3px); gap: 3px; padding: 7px; border-radius: 6px; cursor: grab; touch-action: none; }
.drag-handle:hover { background: #343c47; }
.drag-handle:active { cursor: grabbing; }
.drag-handle i { width: 3px; height: 3px; border-radius: 50%; background: var(--gb-text-muted); }

.state-feedback { position: absolute; inset: 0; justify-content: center; gap: 8px; background: rgba(36, 42, 50, 0.92); color: var(--gb-heading); font-size: 0.78rem; font-weight: 600; }
.state-feedback svg { width: 18px; height: 18px; fill: none; stroke: #6ec79e; stroke-linecap: round; stroke-linejoin: round; stroke-width: 2; }
.spinner { width: 15px; height: 15px; border: 2px solid #4a5564; border-top-color: var(--gb-accent); border-radius: 50%; animation: spin 700ms linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
