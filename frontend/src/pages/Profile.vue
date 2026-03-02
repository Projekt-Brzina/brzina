<template>
  <div class="container py-4">
    <h2 class="mb-3">Edit Profile</h2>
    <form @submit.prevent="saveProfile" class="row g-3 mb-4">
      <div class="col-md-6">
        <label class="form-label">Name:</label>
        <input v-model="name" type="text" class="form-control" />
      </div>
      <div class="col-md-6">
        <label class="form-label">Payment Info:</label>
        <input v-model="payment_info" type="text" class="form-control" />
      </div>
      <div class="col-12">
        <button type="submit" class="btn btn-primary">Save</button>
      </div>
    </form>
    <div v-if="msg" class="alert alert-success">{{ msg }}</div>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>
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
