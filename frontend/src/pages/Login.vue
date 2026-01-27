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

const email = ref('');
const password = ref('');
const error = ref('');

async function login() {
  try {
    const res = await axios.post('/api/auth/login', { email: email.value, password: password.value });
    // Store JWT, redirect, etc.
    error.value = '';
    alert('Login successful!');
  } catch (e) {
    error.value = 'Login failed.';
  }
}
</script>
