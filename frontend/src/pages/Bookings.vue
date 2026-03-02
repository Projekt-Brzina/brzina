<template>
  <div class="container py-4">
    <h2 class="mb-3">My Bookings</h2>
    <button class="btn btn-primary mb-3" @click="fetchBookings">Refresh</button>

    <div v-if="pendingOwnerBookings.length" class="mb-4">
      <h3 class="text-warning">Pending Bookings for Your Cars</h3>
      <ul class="list-group">
        <li v-for="booking in pendingOwnerBookings" :key="'owner-' + booking.id" class="list-group-item bg-warning-subtle border-warning mb-2">
          <b>Booking #{{ booking.id }}</b> | Car: {{ getCarDisplay(booking.car_id) }} | User: {{ getUserDisplay(booking.borrower_user_id) }}<br>
          From: {{ formatDateTime(booking.start_time) }}<br>
          To: {{ formatDateTime(booking.end_time) }}<br>
          Status: <b>{{ booking.status }}</b> | Cost: <b>{{ booking.total_cost }} €</b><br>
          <button class="btn btn-success btn-sm me-2" @click="confirmBooking(booking.id)">Confirm</button>
          <button class="btn btn-danger btn-sm" @click="denyBooking(booking.id)">Deny</button>
        </li>
      </ul>
    </div>

    <ul class="list-group mb-4">
      <li v-for="booking in bookings" :key="booking.id" class="list-group-item">
        <template v-if="editBookingId !== booking.id">
          <span>
            <b>Booking #{{ booking.id }}</b><br>
            Car: {{ getCarDisplay(booking.car_id) }} | User: {{ getUserDisplay(booking.borrower_user_id) }}<br>
            From: {{ formatDateTime(booking.start_time) }}<br>
            To: {{ formatDateTime(booking.end_time) }}<br>
            Status: <b>{{ booking.status }}</b> | Cost: <b>{{ booking.total_cost }} €</b><br>
            <span v-if="booking.payment_status">Payment: {{ booking.payment_status }}<br></span>
            <span v-if="booking.status === 'cancelled'">
              <b class="text-danger">CANCELLED</b>
              <span v-if="booking.cancellation_reason">: {{ booking.cancellation_reason }}</span><br>
            </span>
            <span>Created: {{ formatDateTime(booking.created_at) }} | Updated: {{ formatDateTime(booking.updated_at) }}</span><br>
            <template v-if="booking.status !== 'cancelled'">
              <button class="btn btn-secondary btn-sm me-2" @click="startEditBooking(booking)">Edit</button>
              <button class="btn btn-warning btn-sm me-2" @click="promptCancelBooking(booking.id)">Cancel</button>
              <button v-if="!booking.payment_status" class="btn btn-success btn-sm" @click="markAsPaid(booking)">Mark as Paid</button>
            </template>

            <div v-if="cancelReasonDialog.show" class="modal d-block" tabindex="-1" style="background:rgba(0,0,0,0.3);">
              <div class="modal-dialog">
                <div class="modal-content p-3">
                  <h3>Cancel Booking</h3>
                  <label>Reason for cancellation:</label>
                  <input v-model="cancelReasonDialog.reason" placeholder="Enter reason..." class="form-control mb-2" />
                  <div class="d-flex gap-2 justify-content-end">
                    <button class="btn btn-secondary" @click="closeCancelDialog">Close</button>
                    <button class="btn btn-danger" @click="confirmCancelBooking" :disabled="!cancelReasonDialog.reason">Confirm Cancel</button>
                  </div>
                </div>
              </div>
            </div>
          </span>
        </template>
        <template v-else>
          <span class="d-flex flex-wrap gap-2 align-items-center">
            <input v-model="editBooking.start_time" placeholder="Start (YYYY-MM-DD HH:MM)" class="form-control form-control-sm w-auto" />
            <input v-model="editBooking.end_time" placeholder="End (YYYY-MM-DD HH:MM)" class="form-control form-control-sm w-auto" />
            <input v-model="editBooking.payment_status" placeholder="Payment Status (optional)" class="form-control form-control-sm w-auto" />
            <input v-model="editBooking.cancellation_reason" placeholder="Cancellation Reason (optional)" class="form-control form-control-sm w-auto" />
            <button class="btn btn-success btn-sm me-2" @click="saveEditBooking(booking.id)">Save</button>
            <button class="btn btn-secondary btn-sm" @click="cancelEditBooking">Cancel</button>
          </span>
        </template>
      </li>
    </ul>

    <h3>Book a Car</h3>
    <form @submit.prevent="addBooking" class="row g-3 mb-4">
      <div class="col-md-4">
        <label for="car-picker" class="form-label">Car:</label>
        <select v-model="car_id" id="car-picker" class="form-select" required>
          <option value="" disabled>Select a car</option>
          <option v-for="car in availableCars" :key="car.id" :value="car.id">
            {{ car.brand }} {{ car.model }} ({{ car.plate }})
          </option>
        </select>
      </div>
      <div class="col-md-4">
        <label for="start-time" class="form-label">Start:</label>
        <input v-model="start_time" id="start-time" type="datetime-local" class="form-control" required />
      </div>
      <div class="col-md-4">
        <label for="end-time" class="form-label">End:</label>
        <input v-model="end_time" id="end-time" type="datetime-local" class="form-control" required />
      </div>
      <div class="col-md-4">
        <input v-model="payment_status" class="form-control mt-2" placeholder="Payment Status (optional)" />
      </div>
      <div class="col-md-4">
        <input v-model="cancellation_reason" class="form-control mt-2" placeholder="Cancellation Reason (optional)" />
      </div>
      <div class="col-12">
        <button type="submit" class="btn btn-primary">Book</button>
      </div>
    </form>
    <div v-if="bookingError" class="alert alert-danger">{{ bookingError }}</div>
  </div>
</template>

<script setup>
function formatDateTime(dt) {
  if (!dt) return '';
  const d = typeof dt === 'string' ? new Date(dt) : dt;
  if (isNaN(d)) return dt;
  return d.toLocaleString();
}
const cancelReasonDialog = ref({ show: false, bookingId: null, reason: '' });

function promptCancelBooking(id) {
  cancelReasonDialog.value = { show: true, bookingId: id, reason: '' };
}

async function confirmCancelBooking() {
  try {
    await axios.patch(`/api/bookings/${cancelReasonDialog.value.bookingId}/cancel`, {
      cancellation_reason: cancelReasonDialog.value.reason
    });
    cancelReasonDialog.value = { show: false, bookingId: null, reason: '' };
    fetchBookings();
  } catch (e) {
    bookingError.value = 'Failed to cancel booking.';
  }
}

function closeCancelDialog() {
  cancelReasonDialog.value = { show: false, bookingId: null, reason: '' };
}
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
const pendingOwnerBookings = ref([]);
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
const cars = ref([]);
const availableCars = ref([]);
const users = ref([]);

function getCarDisplay(carId) {
  const car = cars.value.find(c => c.id === carId);
  return car ? `${car.brand} ${car.model} (${car.plate})` : `Car #${carId}`;
}

function getUserDisplay(userId) {
  const user = users.value.find(u => u.id === userId);
  return user ? user.name || user.email : `User #${userId}`;
}
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

async function fetchCars() {
  // Fetch all cars for tenant
  try {
    const res = await axios.get('/api/cars/', { params: { tenant_id: 1 } });
    cars.value = res.data;
    // Filter out cars owned by current user and unavailable cars
    availableCars.value = cars.value.filter(car => {
      return car.owner_user_id !== userInfo.value.id && car.status === 'active';
    });

    // Fetch users for the tenant (for display)
    try {
      const userRes = await axios.get('/api/users', { params: { tenant_id: 1 } });
      users.value = userRes.data;
    } catch (e) {
      users.value = [];
    }
  } catch (e) {
    cars.value = [];
    availableCars.value = [];
    users.value = [];
  }
}

onMounted(fetchUserInfo);
onMounted(() => {
  fetchUserInfo().then(fetchCars);
});
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



async function fetchWithRetry(fn, retries = 3, delay = 1000) {
  let lastError;
  for (let i = 0; i < retries; i++) {
    try {
      return await fn();
    } catch (e) {
      lastError = e;
      if (i < retries - 1) await new Promise(res => setTimeout(res, delay));
    }
  }
  throw lastError;
}

async function fetchBookings() {
  if (!userInfo.value.id || !userInfo.value.tenant_id) {
    bookings.value = [];
    pendingOwnerBookings.value = [];
    return;
  }
  // Fetch bookings where user is borrower
  const res = await fetchWithRetry(() => axios.get('/api/bookings', {
    params: {
      tenant_id: userInfo.value.tenant_id,
      borrower_user_id: userInfo.value.id
    }
  }));
  bookings.value = res.data;

  // Fetch bookings for cars owned by user (as owner)
  const jwt = localStorage.getItem('jwt');
  try {
    const ownerRes = await fetchWithRetry(() => axios.get('/api/bookings/owner', {
      params: {
        tenant_id: userInfo.value.tenant_id,
        owner_user_id: userInfo.value.id
      },
      headers: {
        'Authorization': `Bearer ${jwt}`
      }
    }));
    // Only show pending/requested bookings
    pendingOwnerBookings.value = ownerRes.data.filter(b => b.status === 'requested');
  } catch (e) {
    pendingOwnerBookings.value = [];
  }
}
async function confirmBooking(id) {
  try {
    await axios.patch(`/api/bookings/${id}/confirm`);
    fetchBookings();
  } catch (e) {
    bookingError.value = 'Failed to confirm booking.';
  }
}

async function denyBooking(id) {
  try {
    await axios.patch(`/api/bookings/${id}/deny`);
    fetchBookings();
  } catch (e) {
    bookingError.value = 'Failed to deny booking.';
  }
}

async function addBooking() {
  if (!car_id.value || !start_time.value || !end_time.value) {
    bookingError.value = 'Car, start, and end time are required.';
    return;
  }
  // HTML5 datetime-local returns 'YYYY-MM-DDTHH:MM', backend expects 'YYYY-MM-DDTHH:MM' or 'YYYY-MM-DD HH:MM'
  let start = start_time.value;
  let end = end_time.value;
  // If value contains 'T', replace with space for backend compatibility
  if (start.includes('T')) start = start.replace('T', ' ');
  if (end.includes('T')) end = end.replace('T', ' ');
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
      start_time: start,
      end_time: end,
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
    fetchCars();
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
