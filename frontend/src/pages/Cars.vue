<template>
  <div class="container py-4">
    <h2 class="mb-3">Available Cars</h2>
    <button class="btn btn-primary mb-3" @click="fetchCars">Refresh</button>
    <div v-if="loading" class="mb-3">Loading...</div>
    <ul v-else class="list-group mb-4">
      <li v-for="car in filteredCars" :key="car.id" class="list-group-item">
        <b>{{ car.brand }} {{ car.model }}</b> ({{ car.plate }})<br>
        Year: {{ car.year }} | Color: {{ car.color }}<br>
        Rate: <b>{{ car.hourly_rate }} €/h</b><br>
        <span v-if="car.description">Description: {{ car.description }}</span><br>
        <span v-if="ownerNames[car.owner_user_id]">Owner: {{ ownerNames[car.owner_user_id] }}</span><br>
        <span>Status: <b :class="car.status === 'inactive' ? 'text-danger' : 'text-success'">{{ car.status === 'inactive' ? 'Unavailable' : 'Available' }}</b></span>
      </li>
    </ul>

    <div v-if="isLoggedIn">
      <h3>Your Cars</h3>
      <div v-if="myLoading">Loading...</div>
      <ul v-else class="list-group mb-4">
        <li v-for="car in myCars" :key="car.id" class="list-group-item">
          <span v-if="editCarId !== car.id">
            <b>{{ car.brand }} {{ car.model }}</b> ({{ car.plate }})<br>
            Year: {{ car.year }} | Color: {{ car.color }}<br>
            Rate: <b>{{ car.hourly_rate }} €/h</b><br>
            <span v-if="car.description">Description: {{ car.description }}</span><br>
            <span>Status: <b :class="car.status === 'inactive' ? 'text-danger' : 'text-success'">{{ car.status === 'inactive' ? 'Unavailable' : 'Available' }}</b></span><br>
            <button class="btn btn-outline-secondary btn-sm me-2" @click="toggleAvailability(car)">
              Mark as {{ car.status === 'inactive' ? 'Available' : 'Unavailable' }}
            </button>
            <button class="btn btn-secondary btn-sm me-2" @click="startEditCar(car)">Edit</button>
            <button class="btn btn-danger btn-sm" @click="deleteCar(car.id)">Delete</button>
          </span>
          <span v-else class="d-flex flex-wrap gap-2 align-items-center">
            <input v-model="editCar.brand" placeholder="Brand" class="form-control form-control-sm w-auto" />
            <input v-model="editCar.model" placeholder="Model" class="form-control form-control-sm w-auto" />
            <input v-model="editCar.plate" placeholder="Plate" class="form-control form-control-sm w-auto" />
            <input v-model="editCar.hourly_rate" placeholder="Hourly Rate" type="number" step="0.01" class="form-control form-control-sm w-auto" />
            <input v-model="editCar.year" placeholder="Year" type="number" class="form-control form-control-sm w-auto" />
            <input v-model="editCar.color" placeholder="Color" class="form-control form-control-sm w-auto" />
            <input v-model="editCar.description" placeholder="Description" class="form-control form-control-sm w-auto" />
            <label class="form-label mb-0">
              <select v-model="editCar.status" class="form-select form-select-sm w-auto">
                <option value="active">Available</option>
                <option value="inactive">Unavailable</option>
              </select>
            </label>
            <button class="btn btn-success btn-sm me-2" @click="saveEditCar(car.id)">Save</button>
            <button class="btn btn-secondary btn-sm" @click="cancelEditCar">Cancel</button>
          </span>
        </li>
      </ul>

      <h3>Add a Car</h3>
      <form @submit.prevent="addCar" class="row g-3 mb-4">
        <div class="col-md-3"><input v-model="brand" class="form-control" placeholder="Brand" required minlength="2" /></div>
        <div class="col-md-3"><input v-model="model" class="form-control" placeholder="Model" required minlength="1" /></div>
        <div class="col-md-3"><input v-model="plate" class="form-control" placeholder="Plate" required minlength="3" /></div>
        <div class="col-md-3"><input v-model="hourly_rate" class="form-control" placeholder="Hourly Rate" type="number" step="0.01" required min="0.01" /></div>
        <div class="col-md-3"><input v-model="year" class="form-control" placeholder="Year" type="number" min="1900" max="2100" /></div>
        <div class="col-md-3"><input v-model="color" class="form-control" placeholder="Color" /></div>
        <div class="col-md-3"><input v-model="description" class="form-control" placeholder="Description" /></div>
        <div class="col-md-3">
          <select v-model="status" class="form-select">
            <option value="active">Available</option>
            <option value="inactive">Unavailable</option>
          </select>
        </div>
        <div class="col-12">
          <button type="submit" class="btn btn-primary">Add Car</button>
        </div>
      </form>
      <div v-if="carError" class="alert alert-danger">{{ carError }}</div>
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
