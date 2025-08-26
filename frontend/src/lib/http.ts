import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

// ✅ Prefer VITE_API_URL (keeps your existing places working)
//    Fallbacks: VITE_API_BASE -> default
const API_BASE =
  import.meta.env.VITE_API_URL ||
  import.meta.env.VITE_API_BASE ||
  'http://localhost:8890'

export const http = axios.create({
  baseURL: API_BASE,
  withCredentials: false,
})

http.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.accessToken) {
    config.headers = config.headers || {}
    config.headers['Authorization'] = `Bearer ${auth.accessToken}`
  }
  return config
})

// (বাকিটা আপনার আগের মতোই রাখুন: 401 refresh interceptor ইত্যাদি)
