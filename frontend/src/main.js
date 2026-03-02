// Global axios response interceptor for session expiry
axios.interceptors.response.use(
	response => response,
	error => {
		if (error.response && (error.response.status === 401 || error.response.status === 403)) {
			localStorage.removeItem('jwt');
			delete axios.defaults.headers.common['Authorization'];
			alert('Session expired or unauthorized. Please log in again.');
			window.location.href = '/login';
			return Promise.reject();
		}
		return Promise.reject(error);
	}
);

import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import axios from 'axios';
import 'bootstrap/dist/css/bootstrap.min.css';

// Set Authorization header from localStorage if JWT exists
const jwt = localStorage.getItem('jwt');
if (jwt) {
	axios.defaults.headers.common['Authorization'] = `Bearer ${jwt}`;
}

createApp(App).use(router).mount('#app');
