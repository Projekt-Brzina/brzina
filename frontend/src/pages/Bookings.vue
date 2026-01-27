<template>
  <div>
    <h2>My Bookings</h2>
    <button @click="fetchBookings">Refresh</button>
    <ul>
      <li v-for="booking in bookings" :key="booking.id">
        Car: {{ booking.car_id }} | From: {{ booking.start_time }} | To: {{ booking.end_time }}
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';

const bookings = ref([]);

async function fetchBookings() {
  // Replace with your backend URL and tenant_id
  const res = await axios.get('/api/bookings', { params: { tenant_id: 1 } });
  bookings.value = res.data;
}

fetchBookings();
</script>
