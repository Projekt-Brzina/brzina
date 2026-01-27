<template>
  <div>
    <h2>Register</h2>
    <form @submit.prevent="register">
      <label>Email: <input v-model="email" type="email" required /></label><br />
      <label>Password: <input v-model="password" type="password" required /></label><br />
      <button type="submit">Register</button>
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

async function register() {
  try {
    const res = await axios.post('/api/auth/register', { email: email.value, password: password.value });
    error.value = '';
    alert('Registration successful!');
  } catch (e) {
    error.value = 'Registration failed.';
  }
}
</script>
