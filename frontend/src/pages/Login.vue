<template>
  <div>
    <h2>Login</h2>
    <form @submit.prevent="login">
      <label>Email: <input v-model="email" type="email" required /></label><br />
      <label>Password: <input v-model="password" type="password" required /></label><br />
      <button type="submit">Login</button>
    </form>
    <div v-if="error" style="color:red">{{ error }}</div>
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
