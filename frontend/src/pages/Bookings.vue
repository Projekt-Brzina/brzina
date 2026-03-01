<template>
  <div>
    <h2>My Bookings</h2>
    <button @click="fetchBookings">Refresh</button>
    <ul>
      <li v-for="booking in bookings" :key="booking.id">
        Car: {{ booking.car_id }} | From: {{ booking.start_time }} | To: {{ booking.end_time }} | Status: {{ booking.status }} | Cost: {{ booking.total_cost }} €
        <span v-if="booking.payment_status"> | Payment: {{ booking.payment_status }}</span>
        <span v-if="booking.cancellation_reason"> | Cancelled: {{ booking.cancellation_reason }}</span>
      </li>
    </ul>

    <h3>Book a Car</h3>
    <form @submit.prevent="addBooking">
      <input v-model="car_id" placeholder="Car ID" type="number" required />
      <input v-model="start_time" placeholder="Start (YYYY-MM-DD HH:MM)" required />
      <input v-model="end_time" placeholder="End (YYYY-MM-DD HH:MM)" required />
      <input v-model="payment_status" placeholder="Payment Status (optional)" />
      <input v-model="cancellation_reason" placeholder="Cancellation Reason (optional)" />
      <button type="submit">Book</button>
    </form>
    <div v-if="bookingError" style="color:red">{{ bookingError }}</div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';

const bookings = ref([]);
const car_id = ref('');
const start_time = ref('');
const end_time = ref('');
const payment_status = ref('');
const cancellation_reason = ref('');
const bookingError = ref('');

async function fetchBookings() {
  const res = await axios.get('/api/bookings', { params: { tenant_id: 1 } });
  bookings.value = res.data;
}

async function addBooking() {
  try {
    await axios.post('/api/bookings', {
      car_id: Number(car_id.value),
      borrower_user_id: 1, // TODO: use real user id from JWT
      tenant_id: 1,
      start_time: start_time.value.replace(' ', 'T'),
      end_time: end_time.value.replace(' ', 'T'),
      payment_status: payment_status.value,
      cancellation_reason: cancellation_reason.value
    }, {
      headers: { 'Content-Type': 'application/json' }
    });
    bookingError.value = '';
    car_id.value = start_time.value = end_time.value = payment_status.value = cancellation_reason.value = '';
    fetchBookings();
  } catch (e) {
    if (e.response && e.response.status === 409) {
      bookingError.value = 'Car is already booked for this time range.';
    } else {
      bookingError.value = 'Failed to book car.';
    }
  }
}

fetchBookings();
</script>
