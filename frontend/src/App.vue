<template>
  <div>
    <h1>Brzina Car Sharing</h1>
    <nav>
      <router-link to="/">Home</router-link> |
      <router-link to="/cars">Cars</router-link> |
      <router-link to="/bookings">Bookings</router-link> |
      <router-link to="/login">Login</router-link> |
      <router-link to="/register">Register</router-link>
      <span v-if="isLoggedIn" style="margin-left:20px; color:green">
        Logged in as {{ userInfo.email }} (tenant: {{ userInfo.tenant_id }})
      </span>
      <button v-if="isLoggedIn" @click="logout" style="margin-left:10px">Logout</button>
    </nav>
    <router-view />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import axios from 'axios';

const isLoggedIn = ref(!!localStorage.getItem('jwt'));

function parseJwt(token) {
  try {
    return JSON.parse(atob(token.split('.')[1]));
  } catch (e) {
    return {};
  }
}

const userInfo = computed(() => {
  if (!isLoggedIn.value) return {};
  const token = localStorage.getItem('jwt');
  if (!token) return {};
  const payload = parseJwt(token);
  return {
    email: payload.email || payload.sub || 'unknown',
    tenant_id: payload.tenant_id || 'unknown',
  };
});

function logout() {
  localStorage.removeItem('jwt');
  delete axios.defaults.headers.common['Authorization'];
  isLoggedIn.value = false;
  window.location.reload();
}
</script>
