<template>
  <div>
    <h2>Edit Profile</h2>
    <form @submit.prevent="saveProfile">
      <label>Name: <input v-model="name" type="text" /></label><br />
      <label>Payment Info: <input v-model="payment_info" type="text" /></label><br />
      <button type="submit">Save</button>
    </form>
    <div v-if="msg" style="color:green">{{ msg }}</div>
    <div v-if="error" style="color:red">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const name = ref('');
const payment_info = ref('');
const msg = ref('');
const error = ref('');

onMounted(async () => {
  try {
    const res = await axios.get('/api/auth/me', {
      headers: { Authorization: `Bearer ${localStorage.getItem('jwt')}` }
    });
    name.value = res.data.name || '';
    payment_info.value = res.data.payment_info || '';
  } catch (e) {
    error.value = 'Failed to load profile.';
  }
});

async function saveProfile() {
  if (name.value && name.value.length < 2) {
    error.value = 'Name must be at least 2 characters.';
    msg.value = '';
    return;
  }
  try {
    await axios.put('/api/auth/me', {
      name: name.value,
      payment_info: payment_info.value
    }, {
      headers: { Authorization: `Bearer ${localStorage.getItem('jwt')}` }
    });
    msg.value = 'Profile updated!';
    error.value = '';
  } catch (e) {
    error.value = 'Failed to update profile.';
    msg.value = '';
  }
}
</script>
