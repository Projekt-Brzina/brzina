<template>
  <div class="container-fluid p-0">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary mb-4">
      <div class="container-fluid">
        <a class="navbar-brand" href="#">Brzina Car Sharing</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav me-auto mb-2 mb-lg-0">
            <li class="nav-item"><router-link class="nav-link" to="/">Home</router-link></li>
            <li class="nav-item"><router-link class="nav-link" to="/cars">Cars</router-link></li>
            <li class="nav-item"><router-link class="nav-link" to="/bookings">Bookings</router-link></li>
            <li class="nav-item"><router-link class="nav-link" to="/login">Login</router-link></li>
            <li class="nav-item"><router-link class="nav-link" to="/register">Register</router-link></li>
            <li class="nav-item" v-if="isLoggedIn"><router-link class="nav-link" to="/profile">Profile</router-link></li>
            <li class="nav-item" v-if="isLoggedIn && userInfo.is_admin"><router-link class="nav-link text-warning" to="/admin">Admin</router-link></li>
          </ul>
          <span v-if="isLoggedIn" class="navbar-text text-light me-3">
            Logged in as {{ userInfo.name || userInfo.email }} (tenant: {{ tenantName }})<span v-if="userInfo.payment_info"> | Payment: {{ userInfo.payment_info }}</span>
          </span>
          <button v-if="isLoggedIn" class="btn btn-outline-light btn-sm" @click="logout">Logout</button>
        </div>
      </div>
    </nav>
    <main class="container">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const isLoggedIn = ref(!!localStorage.getItem('jwt'));
const userInfo = ref({});
const tenants = ref([]);
const tenantName = ref('');

async function fetchTenants() {
  try {
    const res = await axios.get('/api/tenants/');
    tenants.value = res.data;
    updateTenantName();
  } catch (e) {
    tenants.value = [];
    tenantName.value = '';
  }
}

function updateTenantName() {
  if (!userInfo.value.tenant_id || tenants.value.length === 0) {
    tenantName.value = userInfo.value.tenant_id || '';
    return;
  }
  const t = tenants.value.find(t => t.id === userInfo.value.tenant_id);
  tenantName.value = t ? t.name : userInfo.value.tenant_id;
}

async function fetchUserInfo() {
  if (!isLoggedIn.value) {
    userInfo.value = {};
    tenantName.value = '';
    return;
  }
  try {
    const res = await axios.get('/api/auth/me', {
      headers: { Authorization: `Bearer ${localStorage.getItem('jwt')}` }
    });
    userInfo.value = res.data;
    updateTenantName();
  } catch (e) {
    userInfo.value = {};
    tenantName.value = '';
  }
}

onMounted(async () => {
  await fetchUserInfo();
  await fetchTenants();
});

function logout() {
  localStorage.removeItem('jwt');
  delete axios.defaults.headers.common['Authorization'];
  isLoggedIn.value = false;
  window.location.reload();
}
</script>
