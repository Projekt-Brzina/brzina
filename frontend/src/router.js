import { createRouter, createWebHistory } from 'vue-router';


import Home from './pages/Home.vue';
import Cars from './pages/Cars.vue';
import Bookings from './pages/Bookings.vue';
import Login from './pages/Login.vue';
import Register from './pages/Register.vue';

import Profile from './pages/Profile.vue';
import Admin from './pages/Admin.vue';

const routes = [
  { path: '/', component: Home },
  { path: '/cars', component: Cars },
  { path: '/bookings', component: Bookings },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  { path: '/profile', component: Profile },
  { path: '/admin', component: Admin }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
