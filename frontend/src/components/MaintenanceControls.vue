<template>
  <section class="controls" aria-label="Maintenance search and filters">
    <label class="search-field">
      <span class="sr-only">Search maintenance</span>
      <svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="8.5" cy="8.5" r="5" /><path d="m12.2 12.2 4 4" /></svg>
      <input :value="search" type="search" placeholder="Search work, provider, notes or mileage" @input="$emit('update:search', $event.target.value)" />
      <button v-if="search" type="button" class="clear" aria-label="Clear maintenance search" @click="$emit('update:search', '')">Clear</button>
    </label>

    <label class="select-field">
      <span>Category</span>
      <select :value="category" @change="$emit('update:category', $event.target.value)">
        <option value="all">All categories</option>
        <option v-for="option in categories" :key="option" :value="option">{{ titleCase(option) }}</option>
      </select>
    </label>

    <label class="select-field sort-field">
      <span>Sort by</span>
      <select :value="sort" @change="$emit('update:sort', $event.target.value)">
        <option v-for="option in maintenanceSortOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
      </select>
    </label>
  </section>
</template>

<script setup>
import { maintenanceSortOptions } from '../utils/maintenanceDisplay.js'

defineProps({
  search: { type: String, default: '' },
  sort: { type: String, default: 'recent' },
  category: { type: String, default: 'all' }
})
defineEmits(['update:search', 'update:sort', 'update:category'])

const categories = ['engine', 'suspension', 'exterior', 'interior', 'wheels', 'brakes', 'exhaust', 'fluids', 'other']
function titleCase(value) { return value.charAt(0).toUpperCase() + value.slice(1) }
</script>

<style scoped>
.controls { display: grid; grid-template-columns: minmax(280px, 1fr) 180px 200px; align-items: end; gap: 10px; padding-bottom: 16px; border-bottom: 1px solid rgba(179, 199, 255, .1); }
.search-field { position: relative; }
.search-field > svg { position: absolute; top: 50%; left: 12px; width: 17px; height: 17px; transform: translateY(-50%); fill: none; stroke: var(--gb-text-muted); stroke-linecap: round; stroke-width: 1.6; pointer-events: none; }
.search-field input, .select-field select { box-sizing: border-box; width: 100%; min-height: 42px; border: 1px solid rgba(179, 199, 255, .12); border-radius: 8px; padding: 10px 12px; background: #1c2128; color: var(--gb-heading); font: inherit; font-size: .84rem; }
.search-field input { padding-right: 58px; padding-left: 38px; }
.search-field input:focus, .select-field select:focus { outline: none; border-color: var(--gb-accent); box-shadow: 0 0 0 3px rgba(179, 199, 255, .1); }
.clear { position: absolute; top: 50%; right: 7px; transform: translateY(-50%); border: 0; border-radius: 5px; padding: 5px 7px; background: transparent; color: var(--gb-accent); font-size: .72rem; font-weight: 700; cursor: pointer; }
.clear:hover { background: rgba(179, 199, 255, .08); }
.select-field { display: grid; gap: 5px; color: var(--gb-text-muted); font-size: .72rem; font-weight: 600; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; }

@media (max-width: 760px) { .controls { grid-template-columns: 1fr 1fr; } .search-field { grid-column: 1 / -1; } }
@media (max-width: 480px) { .controls { grid-template-columns: 1fr; } .search-field { grid-column: auto; } }
</style>
