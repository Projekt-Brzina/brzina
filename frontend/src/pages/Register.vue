<template>
  <div>
    <h2>Register</h2>
    <form @submit.prevent="register">
      <label>Email: <input v-model="email" type="email" required /></label><br />
      <label>Password: <input v-model="password" type="password" required /></label><br />
      <label>Name: <input v-model="name" type="text" required /></label><br />
      <label>Payment Info: <input v-model="payment_info" type="text" /></label><br />
      <label>Tenant:
        <select v-model="tenant_id" required>
          <option disabled value="">Select tenant</option>
          <option v-for="t in tenants" :key="t.id" :value="t.id">{{ t.name }}</option>
        </select>
      </label><br />
      <button type="submit">Register</button>
    </form>
    <div v-if="error" style="color:red">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const email = ref('');
const password = ref('');
const name = ref('');
const payment_info = ref('');
const tenant_id = ref('');
const error = ref('');
const tenants = ref([]);

onMounted(async () => {
  try {
    const res = await axios.get('/api/tenants/');
    tenants.value = res.data;
  } catch (e) {
    tenants.value = [];
  }
});

async function register() {
  try {
    const res = await axios.post('/api/auth/register', {
      email: email.value,
      password: password.value,
      name: name.value,
      payment_info: payment_info.value,
      tenant_id: Number(tenant_id.value)
    });
    error.value = '';
    alert('Registration successful!');
  } catch (e) {
    error.value = 'Registration failed.';
  }
}
</script>
