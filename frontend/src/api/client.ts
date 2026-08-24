import axios from 'axios';

// Vite uses import.meta.env.MODE instead of process.env.NODE_ENV
const API_BASE_URL = import.meta.env.MODE === 'production'
  ? 'https://ai-resume-screener-yfnp.onrender.com/api/v1'
  : 'http://127.0.0.1:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Automatically attach JWT token to every request if it exists
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});