<template>
  <div>
    <h2>Pending Bookings for My Cars</h2>
    <button @click="fetchOwnerBookings">Refresh</button>
    <ul>
      <li v-for="booking in ownerBookings" :key="booking.id">
        <span>
          <b>Booking #{{ booking.id }}</b> | Car ID: {{ booking.car_id }} | User: {{ booking.borrower_user_id }}<br>
          From: {{ booking.start_time }}<br>
          To: {{ booking.end_time }}<br>
          Status: <b>{{ booking.status }}</b> | Cost: <b>{{ booking.total_cost }} €</b><br>
          <span v-if="booking.status === 'requested'">
            <button @click="confirmBooking(booking.id)">Confirm</button>
            <button @click="denyBooking(booking.id)">Deny</button>
          </span>
          <span v-else-if="booking.status === 'confirmed'" style="color:green">Confirmed</span>
          <span v-else-if="booking.status === 'denied'" style="color:red">Denied</span>
          <span v-else-if="booking.status === 'cancelled'" style="color:red">Cancelled</span>
        </span>
      </li>
    </ul>
    <div v-if="ownerBookingError" style="color:red">{{ ownerBookingError }}</div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';

const ownerBookings = ref([]);
const ownerBookingError = ref('');
const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || '{}'));

async function fetchOwnerBookings() {
  const jwt = localStorage.getItem('jwt');
  if (!jwt || !userInfo.value.id || !userInfo.value.tenant_id) {
    ownerBookings.value = [];
    return;
  }
  try {
    const res = await axios.get('/api/bookings/owner', {
      params: {
        tenant_id: userInfo.value.tenant_id,
        owner_user_id: userInfo.value.id
      },
      headers: {
        'Authorization': `Bearer ${jwt}`
      }
    });
    ownerBookings.value = res.data;
  } catch (e) {
    ownerBookingError.value = 'Failed to fetch owner bookings.';
  }
}

async function confirmBooking(id) {
  try {
    await axios.patch(`/api/bookings/${id}/confirm`);
    fetchOwnerBookings();
  } catch (e) {
    ownerBookingError.value = 'Failed to confirm booking.';
  }
}

async function denyBooking(id) {
  try {
    await axios.patch(`/api/bookings/${id}/deny`);
    fetchOwnerBookings();
  } catch (e) {
    ownerBookingError.value = 'Failed to deny booking.';
  }
}

fetchOwnerBookings();
</script>
