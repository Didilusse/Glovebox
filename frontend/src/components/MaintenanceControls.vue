<template>
  <section class="controls" aria-label="Maintenance search and sorting">
    <label class="search-field">
      <span class="sr-only">Search maintenance</span>
      <input
        :value="search"
        type="search"
        placeholder="Search service, provider, notes, mileage..."
        @input="$emit('update:search', $event.target.value)"
      />
      <button v-if="search" type="button" class="clear" aria-label="Clear maintenance search" @click="$emit('update:search', '')">Clear</button>
    </label>

    <label class="sort-field">
      <span>Sort</span>
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
  sort: { type: String, default: 'recent' }
})
defineEmits(['update:search', 'update:sort'])
</script>

<style scoped>
.controls { display: flex; align-items: end; gap: 12px; }
.search-field { position: relative; flex: 1; }
.search-field input, .sort-field select { box-sizing: border-box; width: 100%; border: 1px solid var(--gb-border); border-radius: 10px; padding: 11px 12px; background: var(--gb-surface); color: var(--gb-heading); font: inherit; }
.search-field input { padding-right: 64px; }
.search-field input:focus, .sort-field select:focus { outline: none; border-color: var(--gb-accent); box-shadow: 0 0 0 3px rgba(179, 199, 255, .1); }
.clear { position: absolute; top: 50%; right: 8px; transform: translateY(-50%); border: 0; border-radius: 6px; padding: 5px 7px; background: transparent; color: var(--gb-accent); font-size: .78rem; font-weight: 700; cursor: pointer; }
.clear:hover { background: rgba(179, 199, 255, .1); }
.sort-field { display: grid; gap: 5px; min-width: 190px; color: var(--gb-text-muted); font-size: .76rem; font-weight: 700; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; }
@media (max-width: 600px) { .controls { align-items: stretch; flex-direction: column; } .sort-field { min-width: 0; } }
</style>
