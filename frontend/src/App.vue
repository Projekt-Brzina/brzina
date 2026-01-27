<template>
  <div>
    <h1>Brzina Car Sharing</h1>
    <nav>
      <router-link to="/">Home</router-link> |
      <router-link to="/cars">Cars</router-link> |
      <router-link to="/bookings">Bookings</router-link> |
      <router-link to="/login">Login</router-link> |
      <router-link to="/register">Register</router-link>
    </nav>
    <router-view />
  </div>
</template>

<script setup>
</script>
