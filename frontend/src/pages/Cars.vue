<template>
  <div>
    <h2>Available Cars</h2>
    <button @click="fetchCars">Refresh</button>
    <div v-if="loading">Loading...</div>
    <ul v-else>
      <li v-for="car in filteredCars" :key="car.id">
        <b>{{ car.brand }} {{ car.model }}</b> ({{ car.plate }})<br>
        Year: {{ car.year }} | Color: {{ car.color }}<br>
        Rate: <b>{{ car.hourly_rate }} €/h</b><br>
        <span v-if="car.description">Description: {{ car.description }}</span><br>
        <span v-if="ownerNames[car.owner_user_id]">Owner: {{ ownerNames[car.owner_user_id] }}</span><br>
        <span>Status: <b>{{ car.status === 'inactive' ? 'Unavailable' : 'Available' }}</b></span>
      </li>
    </ul>

    <div v-if="isLoggedIn">
      <h3>Your Cars</h3>
      <div v-if="myLoading">Loading...</div>
      <ul v-else>
        <li v-for="car in myCars" :key="car.id">
          <span v-if="editCarId !== car.id">
            <b>{{ car.brand }} {{ car.model }}</b> ({{ car.plate }})<br>
            Year: {{ car.year }} | Color: {{ car.color }}<br>
            Rate: <b>{{ car.hourly_rate }} €/h</b><br>
            <span v-if="car.description">Description: {{ car.description }}</span><br>
            <span>Status: <b>{{ car.status === 'inactive' ? 'Unavailable' : 'Available' }}</b></span><br>
            <button @click="toggleAvailability(car)">
              Mark as {{ car.status === 'inactive' ? 'Available' : 'Unavailable' }}
            </button>
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
            <label>
              <select v-model="editCar.status">
                <option value="active">Available</option>
                <option value="inactive">Unavailable</option>
              </select>
            </label>
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
        <label>
          <select v-model="status">
            <option value="active">Available</option>
            <option value="inactive">Unavailable</option>
          </select>
          Status
        </label>
        <button type="submit">Add Car</button>
      </form>
      <div v-if="carError" style="color:red">{{ carError }}</div>
    </div>
  </div>
</template>

<script setup>
const loading = ref(false);
const myLoading = ref(false);
import { ref } from 'vue';
import axios from 'axios';

const cars = ref([]);
const filteredCars = ref([]);
const myCars = ref([]);
const brand = ref('');
const model = ref('');
const plate = ref('');
const hourly_rate = ref(0);
const year = ref('');
const color = ref('');
const description = ref('');
const status = ref('active');
const carError = ref('');
const editCarId = ref(null);
const editCar = ref({});
const ownerNames = ref({});
const isLoggedIn = ref(!!localStorage.getItem('jwt'));
const userInfo = ref({});
async function toggleAvailability(car) {
  loading.value = true;
  try {
    const newStatus = car.status === 'inactive' ? 'active' : 'inactive';
    await axios.patch(`/api/cars/${car.id}`, { status: newStatus });
    await fetchCars();
  } catch (e) {
    carError.value = e.response?.data?.detail || e.message || 'Failed to update availability.';
  } finally {
    loading.value = false;
  }
}

function startEditCar(car) {
  editCarId.value = car.id;
  editCar.value = { ...car };
}

function cancelEditCar() {
  editCarId.value = null;
  editCar.value = {};
}

async function saveEditCar(id) {
  loading.value = true;
  try {
    await axios.put(`/api/cars/${id}`, {
      ...editCar.value,
      status: editCar.value.status || 'active'
    }, {
      headers: { 'Content-Type': 'application/json' }
    });
    editCarId.value = null;
    editCar.value = {};
    await fetchCars();
  } catch (e) {
    carError.value = e.response?.data?.detail || e.message || 'Failed to update car.';
  } finally {
    loading.value = false;
  }
}

async function deleteCar(id) {
  loading.value = true;
  try {
    await axios.delete(`/api/cars/${id}`);
    await fetchCars();
  } catch (e) {
    carError.value = e.response?.data?.detail || e.message || 'Failed to delete car.';
  } finally {
    loading.value = false;
  }
}

async function fetchWithRetry(fn, retries = 3, delay = 1000) {
  let lastError;
  for (let i = 0; i < retries; i++) {
    try {
      return await fn();
    } catch (e) {
      lastError = e;
      if (i < retries - 1) await new Promise(res => setTimeout(res, delay));
    }
  }
  throw lastError;
}

async function fetchCars() {
  // Fetch user info if logged in
  if (isLoggedIn.value) {
    try {
      const res = await fetchWithRetry(() => axios.get('/api/auth/me', {
        headers: { Authorization: `Bearer ${localStorage.getItem('jwt')}` }
      }));
      userInfo.value = res.data;
    } catch (e) {
      userInfo.value = {};
    }
  }
  // Fetch all users for tenant (for owner names)
  let users = [];
  try {
    const res = await fetchWithRetry(() => axios.get('/api/users', { params: { tenant_id: 1 } }));
    users = res.data;
    ownerNames.value = {};
    for (const u of users) {
      ownerNames.value[u.id] = u.name || u.email;
    }
  } catch (e) {
    ownerNames.value = {};
  }
  loading.value = true;
  try {
    // Fetch cars
    const res = await fetchWithRetry(() => axios.get('/api/cars/', { params: { tenant_id: 1 } }));
    cars.value = res.data;
    // Filter out cars owned by current user
    if (isLoggedIn.value && userInfo.value.id) {
      filteredCars.value = cars.value.filter(car => car.owner_user_id !== userInfo.value.id);
    } else {
      filteredCars.value = cars.value;
    }
  } finally {
    loading.value = false;
  }
  // Fetch user's cars if logged in
  if (isLoggedIn.value) {
    myLoading.value = true;
    try {
      const params = { tenant_id: 1 };
      if (userInfo.value && userInfo.value.id != null && !isNaN(userInfo.value.id)) {
        params.user_id = parseInt(userInfo.value.id, 10);
      } else {
        throw new Error('User ID is missing or invalid.');
      }
      // Debug: log params
      // eslint-disable-next-line no-console
      console.log('Requesting /api/cars/my with params:', params);
      const myRes = await fetchWithRetry(() => axios.get('/api/cars/my', { params }));
      myCars.value = myRes.data;
    } catch (e) {
      // Debug: log error
      // eslint-disable-next-line no-console
      console.error('Error fetching /api/cars/my:', e, e?.response?.data);
      carError.value = e.response?.data?.detail || e.message || 'Failed to fetch your cars.';
      myCars.value = [];
    } finally {
      myLoading.value = false;
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
  loading.value = true;
  try {
    await axios.post('/api/cars', {
      brand: brand.value,
      model: model.value,
      plate: plate.value,
      hourly_rate: hourly_rate.value,
      year: year.value ? Number(year.value) : undefined,
      color: color.value,
      description: description.value,
      status: status.value || 'active',
      tenant_id: 1
    }, {
      headers: { 'Content-Type': 'application/json' }
    });
    carError.value = '';
    brand.value = model.value = plate.value = color.value = description.value = '';
    hourly_rate.value = 0;
    year.value = '';
    status.value = 'active';
    await fetchCars();
  } catch (e) {
    carError.value = e.response?.data?.detail || e.message || 'Failed to add car.';
  } finally {
    loading.value = false;
  }
}

fetchCars();
</script>
