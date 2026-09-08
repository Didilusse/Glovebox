<template>
  <header class="planner-header">
    <div class="title-row">
      <div>
        <span class="context">Modification plan</span>
        <h1>{{ title }}</h1>
        <p>Move each part from idea to installed.</p>
      </div>
      <button v-if="!readOnly" type="button" class="add-button" @click="$emit('add')">
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 4v12M4 10h12" /></svg>
        Add part
      </button>
    </div>

    <section class="overview" aria-label="Build overview">
      <div class="progress-block">
        <div class="progress-copy">
          <div>
            <span>Build progress</span>
            <strong>{{ installedCount }} of {{ mods.length }} installed</strong>
          </div>
          <b>{{ progress }}%</b>
        </div>
        <progress class="progress-track" aria-label="Build progress" max="100" :value="progress" :aria-valuenow="progress"></progress>
      </div>

      <dl>
        <div>
          <dt>Estimated total</dt>
          <dd>{{ money(totalCost) }}</dd>
        </div>
        <div>
          <dt>Still to purchase</dt>
          <dd>{{ money(plannedCost) }}</dd>
        </div>
        <div>
          <dt>Ready to install</dt>
          <dd>{{ purchasedCount }} <small>{{ money(purchasedCost) }}</small></dd>
        </div>
      </dl>
    </section>
  </header>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  readOnly: Boolean,
  carName: { type: String, default: '' },
  mods: { type: Array, default: () => [] }
})

defineEmits(['add'])

const title = computed(() => props.carName ? `${props.carName} build` : 'Build plan')
const installedCount = computed(() => props.mods.filter(mod => mod.status === 'installed').length)
const purchasedCount = computed(() => props.mods.filter(mod => mod.status === 'purchased').length)
const totalCost = computed(() => sumCost(props.mods))
const plannedCost = computed(() => sumCost(props.mods.filter(mod => mod.status === 'planned')))
const purchasedCost = computed(() => sumCost(props.mods.filter(mod => mod.status === 'purchased')))
const progress = computed(() => props.mods.length ? Math.round((installedCount.value / props.mods.length) * 100) : 0)

function sumCost(mods) {
  return mods.reduce((total, mod) => total + (Number(mod.cost) || 0), 0)
}

function money(value) {
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0
  }).format(value)
}
</script>

<style scoped>
.planner-header {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.title-row,
.progress-copy,
.add-button {
  display: flex;
  align-items: center;
}

.title-row {
  justify-content: space-between;
  gap: 24px;
}

.context {
  color: var(--gb-accent);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

h1 {
  margin-top: 4px;
  color: var(--gb-heading);
  font-size: clamp(1.5rem, 3vw, 1.75rem);
  font-weight: 720;
  letter-spacing: -0.025em;
  line-height: 1.15;
}

.title-row p {
  margin-top: 5px;
  color: var(--gb-text-muted);
  font-size: 0.9rem;
}

.add-button {
  gap: 8px;
  border: 0;
  border-radius: 9px;
  padding: 10px 16px;
  background: var(--gb-accent);
  color: #141820;
  font-weight: 700;
  cursor: pointer;
  transition: background 150ms, transform 100ms;
}

.add-button:hover { background: var(--gb-accent-hover); }
.add-button:active { transform: translateY(1px); }
.add-button:focus-visible { outline: 3px solid rgba(179, 199, 255, 0.25); outline-offset: 2px; }
.add-button svg { width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 1.8; }

.overview {
  display: grid;
  grid-template-columns: minmax(240px, 1.15fr) minmax(430px, 1.85fr);
  border: 1px solid rgba(179, 199, 255, 0.1);
  border-radius: 12px;
  background: #1c2128;
}

.progress-block {
  padding: 20px;
  border-right: 1px solid rgba(179, 199, 255, 0.1);
}

.progress-copy {
  justify-content: space-between;
  gap: 16px;
}

.progress-copy div {
  display: flex;
  flex-direction: column;
}

.progress-copy span,
dt {
  color: var(--gb-text-muted);
  font-size: 0.74rem;
}

.progress-copy strong {
  margin-top: 1px;
  color: var(--gb-heading);
  font-size: 0.9rem;
  font-weight: 600;
}

.progress-copy b {
  color: #8bd2ac;
  font-size: 1rem;
  font-weight: 700;
}

.progress-track {
  display: block;
  width: 100%;
  height: 6px;
  margin-top: 14px;
  overflow: hidden;
  border-radius: 99px;
  background: #30363f;
  border: 0;
  appearance: none;
}

.progress-track::-webkit-progress-bar { border-radius: inherit; background: #30363f; }
.progress-track::-webkit-progress-value,
.progress-track::-moz-progress-bar {
  border-radius: 99px;
  background: #6ec79e;
}

dl {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

dl div {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 16px 20px;
}

dl div + div { border-left: 1px solid rgba(179, 199, 255, 0.1); }

dd {
  margin-top: 2px;
  color: var(--gb-heading);
  font-size: 1.08rem;
  font-weight: 650;
}

dd small {
  margin-left: 4px;
  color: var(--gb-text-muted);
  font-size: 0.72rem;
}

@media (max-width: 820px) {
  .overview { grid-template-columns: 1fr; }
  .progress-block { border-right: 0; border-bottom: 1px solid rgba(179, 199, 255, 0.1); }
}

@media (max-width: 540px) {
  .title-row { align-items: flex-start; }
  .add-button { padding: 10px 12px; white-space: nowrap; }
  dl { grid-template-columns: 1fr 1fr; }
  dl div { padding: 14px 16px; }
  dl div + div { border-left: 0; }
  dl div:nth-child(2) { border-left: 1px solid rgba(179, 199, 255, 0.1); }
  dl div:last-child { grid-column: 1 / -1; border-top: 1px solid rgba(179, 199, 255, 0.1); }
}
</style>
