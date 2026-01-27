<template>
  <div>
    <h2>Available Cars</h2>
    <button @click="fetchCars">Refresh</button>
    <ul>
      <li v-for="car in cars" :key="car.id">
        {{ car.brand }} {{ car.model }} ({{ car.plate }}) - {{ car.hourly_rate }} €/h
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';

const cars = ref([]);

async function fetchCars() {
  // Replace with your backend URL and tenant_id
  const res = await axios.get('/api/cars', { params: { tenant_id: 1 } });
  cars.value = res.data;
}

fetchCars();
</script>
