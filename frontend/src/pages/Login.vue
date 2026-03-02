<template>
  <div class="container py-4">
    <h2 class="mb-3">Login</h2>
    <form @submit.prevent="login" class="row g-3 mb-4">
      <div class="col-md-6">
        <label class="form-label">Email:</label>
        <input v-model="email" type="email" class="form-control" required />
      </div>
      <div class="col-md-6">
        <label class="form-label">Password:</label>
        <input v-model="password" type="password" class="form-control" required />
      </div>
      <div class="col-12">
        <button type="submit" class="btn btn-primary">Login</button>
      </div>
    </form>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';
import { useRouter } from 'vue-router';

const router = useRouter();

const email = ref('');
const password = ref('');
const error = ref('');

async function login() {
  if (!email.value || !password.value) {
    error.value = 'Email and password are required.';
    return;
  }
  try {
    const res = await axios.post('/api/auth/login', { email: email.value, password: password.value });
    // Store JWT in localStorage
    localStorage.setItem('jwt', res.data.access_token);
    // Set axios default Authorization header
    axios.defaults.headers.common['Authorization'] = `Bearer ${res.data.access_token}`;
    error.value = '';
    // Optionally, you can emit an event or use a global store, but for now reload app state:
    window.location.href = '/'; // Redirect to home and reloads state
  } catch (e) {
    error.value = 'Login failed.';
  }
}
</script>
