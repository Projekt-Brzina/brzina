<template>
  <div>
    <h2>Available Cars</h2>
    <button @click="fetchCars">Refresh</button>
    <ul>
      <li v-for="car in cars" :key="car.id">
        <b>{{ car.brand }} {{ car.model }}</b> ({{ car.plate }})<br>
        Year: {{ car.year }} | Color: {{ car.color }}<br>
        Rate: <b>{{ car.hourly_rate }} €/h</b><br>
        <span v-if="car.description">Description: {{ car.description }}</span>
      </li>
    </ul>

    <div v-if="isLoggedIn">
      <h3>Your Cars</h3>
      <ul>
        <li v-for="car in myCars" :key="car.id">
          <span v-if="editCarId !== car.id">
            <b>{{ car.brand }} {{ car.model }}</b> ({{ car.plate }})<br>
            Year: {{ car.year }} | Color: {{ car.color }}<br>
            Rate: <b>{{ car.hourly_rate }} €/h</b><br>
            <span v-if="car.description">Description: {{ car.description }}</span><br>
            <button @click="startEditCar(car)">Edit</button>
            <button @click="deleteCar(car.id)">Delete</button>
          </span>
          <span v-else>
            <input v-model="editCar.brand" placeholder="Brand" />
            <input v-model="editCar.model" placeholder="Model" />
            <input v-model="editCar.plate" placeholder="Plate" />
            <input v-model="editCar.hourly_rate" placeholder="Hourly Rate" type="number" step="0.01" />
            <input v-model="editCar.year" placeholder="Year" type="number" />
            <input v-model="editCar.color" placeholder="Color" />
            <input v-model="editCar.description" placeholder="Description" />
            <button @click="saveEditCar(car.id)">Save</button>
            <button @click="cancelEditCar">Cancel</button>
          </span>
        </li>
      </ul>

      <h3>Add a Car</h3>
      <form @submit.prevent="addCar">
        <input v-model="brand" placeholder="Brand" required minlength="2" />
        <input v-model="model" placeholder="Model" required minlength="1" />
        <input v-model="plate" placeholder="Plate" required minlength="3" />
        <input v-model="hourly_rate" placeholder="Hourly Rate" type="number" step="0.01" required min="0.01" />
        <input v-model="year" placeholder="Year" type="number" min="1900" max="2100" />
        <input v-model="color" placeholder="Color" />
        <input v-model="description" placeholder="Description" />
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
const year = ref('');
const color = ref('');
const description = ref('');
const carError = ref('');
const editCarId = ref(null);
const editCar = ref({});
function startEditCar(car) {
  editCarId.value = car.id;
  editCar.value = { ...car };
}

function cancelEditCar() {
  editCarId.value = null;
  editCar.value = {};
}

async function saveEditCar(id) {
  try {
    await axios.put(`/api/cars/${id}`, {
      ...editCar.value
    }, {
      headers: { 'Content-Type': 'application/json' }
    });
    editCarId.value = null;
    editCar.value = {};
    fetchCars();
  } catch (e) {
    carError.value = 'Failed to update car.';
  }
}

async function deleteCar(id) {
  try {
    await axios.delete(`/api/cars/${id}`);
    fetchCars();
  } catch (e) {
    carError.value = 'Failed to delete car.';
  }
}
const isLoggedIn = ref(!!localStorage.getItem('jwt'));

async function fetchCars() {
  const res = await axios.get('/api/cars/', { params: { tenant_id: 1 } });
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
  if (!brand.value || !model.value || !plate.value || !hourly_rate.value) {
    carError.value = 'All required fields must be filled.';
    return;
  }
  if (brand.value.length < 2 || plate.value.length < 3 || hourly_rate.value <= 0) {
    carError.value = 'Please enter valid car details.';
    return;
  }
  try {
    await axios.post('/api/cars', {
      brand: brand.value,
      model: model.value,
      plate: plate.value,
      hourly_rate: hourly_rate.value,
      year: year.value ? Number(year.value) : undefined,
      color: color.value,
      description: description.value,
      tenant_id: 1
    }, {
      headers: { 'Content-Type': 'application/json' }
    });
    carError.value = '';
    brand.value = model.value = plate.value = color.value = description.value = '';
    hourly_rate.value = 0;
    year.value = '';
    fetchCars();
  } catch (e) {
    carError.value = 'Failed to add car.';
  }
}

fetchCars();
</script>
