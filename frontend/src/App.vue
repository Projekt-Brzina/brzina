<template>
  <div>
    <h1>Brzina Car Sharing</h1>
    <nav>
      <router-link to="/">Home</router-link> |
      <router-link to="/cars">Cars</router-link> |
      <router-link to="/bookings">Bookings</router-link> |
      <router-link to="/login">Login</router-link> |
      <router-link to="/register">Register</router-link>
      <router-link v-if="isLoggedIn" to="/profile" style="margin-left:10px">Profile</router-link>
      <router-link v-if="isLoggedIn && userInfo.is_admin" to="/admin" style="margin-left:10px; color:orange">Admin</router-link>
      <span v-if="isLoggedIn" style="margin-left:20px; color:green">
        Logged in as {{ userInfo.name || userInfo.email }} (tenant: {{ userInfo.tenant_id }})<span v-if="userInfo.payment_info"> | Payment: {{ userInfo.payment_info }}</span>
      </span>
      <button v-if="isLoggedIn" @click="logout" style="margin-left:10px">Logout</button>
    </nav>
    <router-view />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const isLoggedIn = ref(!!localStorage.getItem('jwt'));
const userInfo = ref({});

async function fetchUserInfo() {
  if (!isLoggedIn.value) {
    userInfo.value = {};
    return;
  }
  try {
    const res = await axios.get('/api/auth/me', {
      headers: { Authorization: `Bearer ${localStorage.getItem('jwt')}` }
    });
    userInfo.value = res.data;
  } catch (e) {
    userInfo.value = {};
  }
}

onMounted(fetchUserInfo);

function logout() {
  localStorage.removeItem('jwt');
  delete axios.defaults.headers.common['Authorization'];
  isLoggedIn.value = false;
  window.location.reload();
}
</script>
