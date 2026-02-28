<template>
  <div>
    <h2>Available Cars</h2>
    <button @click="fetchCars">Refresh</button>
    <ul>
      <li v-for="car in cars" :key="car.id">
        {{ car.brand }} {{ car.model }} ({{ car.plate }}) - {{ car.hourly_rate }} €/h
      </li>
    </ul>

    <div v-if="isLoggedIn">
      <h3>Your Cars</h3>
      <ul>
        <li v-for="car in myCars" :key="car.id">
          {{ car.brand }} {{ car.model }} ({{ car.plate }}) - {{ car.hourly_rate }} €/h
        </li>
      </ul>

      <h3>Add a Car</h3>
      <form @submit.prevent="addCar">
        <input v-model="brand" placeholder="Brand" required />
        <input v-model="model" placeholder="Model" required />
        <input v-model="plate" placeholder="Plate" required />
        <input v-model="hourly_rate" placeholder="Hourly Rate" type="number" required />
        <button type="submit">Add Car</button>
      </form>
      <div v-if="carError" style="color:red">{{ carError }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';

const cars = ref([]);
const myCars = ref([]);
const brand = ref('');
const model = ref('');
const plate = ref('');
const hourly_rate = ref(0);
const carError = ref('');
const isLoggedIn = ref(!!localStorage.getItem('jwt'));

async function fetchCars() {
  const res = await axios.get('/api/cars', { params: { tenant_id: 1 } });
  cars.value = res.data;
  // Fetch user's cars if logged in
  if (isLoggedIn.value) {
    try {
      const myRes = await axios.get('/api/cars/my', { params: { tenant_id: 1 } });
      myCars.value = myRes.data;
    } catch (e) {
      myCars.value = [];
    }
  }
}

async function addCar() {
  try {
    await axios.post('/api/cars', {
      brand: brand.value,
      model: model.value,
      plate: plate.value,
      hourly_rate: hourly_rate.value,
      tenant_id: 1
    });
    carError.value = '';
    brand.value = model.value = plate.value = '';
    hourly_rate.value = 0;
    fetchCars();
  } catch (e) {
    carError.value = 'Failed to add car.';
  }
}

fetchCars();
</script>
