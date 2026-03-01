<template>
  <div>
    <h2>Admin Panel</h2>
    <div v-if="!isAdmin">
      <p style="color:red">You must be an admin to view this page.</p>
    </div>
    <div v-else>
      <h3>All Users</h3>
      <button @click="fetchUsers">Refresh Users</button>
      <ul>
        <li v-for="user in users" :key="user.id">
          {{ user.email }} | Name: {{ user.name }} | Tenant: {{ user.tenant_id }} | Admin: {{ user.is_admin }} | Active: {{ user.is_active }}
        </li>
      </ul>
      <h3>All Cars</h3>
      <button @click="fetchCars">Refresh Cars</button>
      <ul>
        <li v-for="car in cars" :key="car.id">
          {{ car.brand }} {{ car.model }} ({{ car.plate }}) | Owner: {{ car.owner_user_id }} | Tenant: {{ car.tenant_id }} | Status: {{ car.status }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const users = ref([]);
const cars = ref([]);
const userInfo = ref({});
const isAdmin = ref(false);

async function fetchUserInfo() {
  try {
    const res = await axios.get('/api/auth/me', {
      headers: { Authorization: `Bearer ${localStorage.getItem('jwt')}` }
    });
    userInfo.value = res.data;
    isAdmin.value = !!res.data.is_admin;
  } catch (e) {
    userInfo.value = {};
    isAdmin.value = false;
  }
}

async function fetchUsers() {
  try {
    const res = await axios.get('/api/auth/users', {
      headers: { Authorization: `Bearer ${localStorage.getItem('jwt')}` }
    });
    users.value = res.data;
  } catch (e) {
    users.value = [];
  }
}

async function fetchCars() {
  try {
    const res = await axios.get('/api/cars', {
      headers: { Authorization: `Bearer ${localStorage.getItem('jwt')}` }
    });
    cars.value = res.data;
  } catch (e) {
    cars.value = [];
  }
}

onMounted(() => {
  fetchUserInfo();
  fetchUsers();
  fetchCars();
});
</script>
