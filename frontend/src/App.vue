<template>
  <div>
    <h1>Brzina Car Sharing</h1>
    <nav>
      <router-link to="/">Home</router-link> |
      <router-link to="/cars">Cars</router-link> |
      <router-link to="/bookings">Bookings</router-link> |
      <router-link to="/login">Login</router-link> |
      <router-link to="/register">Register</router-link>
      <span v-if="isLoggedIn" style="margin-left:20px; color:green">Logged in</span>
      <button v-if="isLoggedIn" @click="logout" style="margin-left:10px">Logout</button>
    </nav>
    <router-view />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';

const isLoggedIn = ref(!!localStorage.getItem('jwt'));

function logout() {
  localStorage.removeItem('jwt');
  delete axios.defaults.headers.common['Authorization'];
  isLoggedIn.value = false;
  window.location.reload();
}
</script>
