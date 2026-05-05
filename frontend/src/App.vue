<template>
  <p>Enter Car Make: {{ make }}</p>
<input v-model="make" placeholder="Toyota" />

<div>Enter Car Model: {{ model }}</div>
<input v-model="model" placeholder="Camry" />

<div>Enter Car Year: {{ year }}</div>
<input v-model="year" placeholder="2020" />

<div> {{ selected }}</div>

<button @click="handleCreateCar">Create Car</button>

</template>


<script setup>
import { ref } from 'vue'

const make = ref('')
const model = ref('')
const year = ref('')
const selected = ref('')

const handleCreateCar = () => {
  
}
</script>