<template>
  <div>
    <h2>My Bookings</h2>
    <button @click="fetchBookings">Refresh</button>
    <ul>
      <li v-for="booking in bookings" :key="booking.id">
        <template v-if="editBookingId !== booking.id">
          <span>
            <b>Booking #{{ booking.id }}</b><br>
            Car ID: {{ booking.car_id }} | User: {{ booking.borrower_user_id }}<br>
            From: {{ booking.start_time }}<br>
            To: {{ booking.end_time }}<br>
            Status: <b>{{ booking.status }}</b> | Cost: <b>{{ booking.total_cost }} €</b><br>
            <span v-if="booking.payment_status">Payment: {{ booking.payment_status }}<br></span>
            <span v-if="booking.cancellation_reason">Cancelled: {{ booking.cancellation_reason }}<br></span>
            <span>Created: {{ booking.created_at }} | Updated: {{ booking.updated_at }}</span><br>
            <button v-if="!booking.cancellation_reason" @click="startEditBooking(booking)">Edit</button>
            <button v-if="!booking.cancellation_reason" @click="cancelBooking(booking.id)">Cancel</button>
            <button v-if="!booking.payment_status && !booking.cancellation_reason" @click="markAsPaid(booking)">Mark as Paid</button>
          </span>
        </template>
        <template v-else>
          <span>
            <input v-model="editBooking.start_time" placeholder="Start (YYYY-MM-DD HH:MM)" />
            <input v-model="editBooking.end_time" placeholder="End (YYYY-MM-DD HH:MM)" />
            <input v-model="editBooking.payment_status" placeholder="Payment Status (optional)" />
            <input v-model="editBooking.cancellation_reason" placeholder="Cancellation Reason (optional)" />
            <button @click="saveEditBooking(booking.id)">Save</button>
            <button @click="cancelEditBooking">Cancel</button>
          </span>
        </template>
      </li>
    </ul>

    <h3>Book a Car</h3>
    <form @submit.prevent="addBooking">
      <input v-model="car_id" placeholder="Car ID" type="number" required min="1" />
      <input v-model="start_time" placeholder="Start (YYYY-MM-DD HH:MM)" required pattern="\d{4}-\d{2}-\d{2} \d{2}:\d{2}" />
      <input v-model="end_time" placeholder="End (YYYY-MM-DD HH:MM)" required pattern="\d{4}-\d{2}-\d{2} \d{2}:\d{2}" />
      <input v-model="payment_status" placeholder="Payment Status (optional)" />
      <input v-model="cancellation_reason" placeholder="Cancellation Reason (optional)" />
      <button type="submit">Book</button>
    </form>
    <div v-if="bookingError" style="color:red">{{ bookingError }}</div>
  </div>
</template>

<script setup>
async function markAsPaid(booking) {
  try {
    const jwt = localStorage.getItem('jwt');
    await axios.post('/api/payments', {
      booking_id: booking.id,
      tenant_id: booking.tenant_id
    }, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${jwt}`
      }
    });
    fetchBookings();
  } catch (e) {
    bookingError.value = 'Failed to mark as paid.';
  }
}
import { ref, onMounted } from 'vue';
import axios from 'axios';

const bookings = ref([]);
const car_id = ref('');
const start_time = ref('');
const end_time = ref('');
const payment_status = ref('');
const cancellation_reason = ref('');
const bookingError = ref('');
const editBookingId = ref(null);
const editBooking = ref({});
const userInfo = ref({});
const isLoggedIn = ref(!!localStorage.getItem('jwt'));
async function fetchUserInfo() {
  if (!isLoggedIn.value) {
    userInfo.value = {};
    return;
  }
  try {
    const res = await axios.get('/api/auth/me', {
      headers: { Authorization: `Bearer ${localStorage.getItem('jwt')}` }
    });
    userInfo.value = res.data;
  } catch (e) {
    userInfo.value = {};
  }
}

onMounted(fetchUserInfo);
function startEditBooking(booking) {
  editBookingId.value = booking.id;
  editBooking.value = {
    start_time: booking.start_time.replace('T', ' ').slice(0, 16),
    end_time: booking.end_time.replace('T', ' ').slice(0, 16),
    payment_status: booking.payment_status || '',
    cancellation_reason: booking.cancellation_reason || ''
  };
}

function cancelEditBooking() {
  editBookingId.value = null;
  editBooking.value = {};
}

async function saveEditBooking(id) {
  try {
    await axios.put(`/api/bookings/${id}`, {
      start_time: editBooking.value.start_time.replace(' ', 'T'),
      end_time: editBooking.value.end_time.replace(' ', 'T'),
      payment_status: editBooking.value.payment_status,
      cancellation_reason: editBooking.value.cancellation_reason
    }, {
      headers: { 'Content-Type': 'application/json' }
    });
    editBookingId.value = null;
    editBooking.value = {};
    fetchBookings();
  } catch (e) {
    if (e.response && e.response.status === 409) {
      bookingError.value = 'Car is already booked for this time range.';
    } else {
      bookingError.value = 'Failed to update booking.';
    }
  }
}

async function cancelBooking(id) {
  try {
    await axios.delete(`/api/bookings/${id}`);
    fetchBookings();
  } catch (e) {
    bookingError.value = 'Failed to cancel booking.';
  }
}

async function fetchBookings() {
  const res = await axios.get('/api/bookings', { params: { tenant_id: 1 } });
  bookings.value = res.data;
}

async function addBooking() {
  if (!car_id.value || !start_time.value || !end_time.value) {
    bookingError.value = 'Car, start, and end time are required.';
    return;
  }
  if (!/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/.test(start_time.value) || !/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/.test(end_time.value)) {
    bookingError.value = 'Date/time must be in YYYY-MM-DD HH:MM format.';
    return;
  }
  try {
    const jwt = localStorage.getItem('jwt');
    if (!jwt || !userInfo.value.id || !userInfo.value.tenant_id) {
      bookingError.value = 'You must be logged in to book.';
      return;
    }
    await axios.post('/api/bookings', {
      car_id: Number(car_id.value),
      borrower_user_id: userInfo.value.id,
      tenant_id: userInfo.value.tenant_id,
      start_time: start_time.value.replace(' ', 'T'),
      end_time: end_time.value.replace(' ', 'T'),
      payment_status: payment_status.value,
      cancellation_reason: cancellation_reason.value
    }, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${jwt}`
      }
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
