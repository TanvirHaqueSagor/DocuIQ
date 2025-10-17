// src/services/httpService.js
import axios from 'axios'
import { API_BASE_URL } from '../config.js'
import i18n from '../i18n'

const http = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true
})

// Request Interceptor
http.interceptors.request.use(config => {
  // যদি token/localStorage থাকে এবং JWT শেইপ হয়, add
  const token = localStorage.getItem('token')
  if (token && typeof token === 'string' && token.indexOf('.') !== -1) {
    config.headers['Authorization'] = `Bearer ${token}`
  } else if (config.headers && config.headers['Authorization']) {
    delete config.headers['Authorization']
  }

  // language header (supports both string and ref locales)
  try {
    const gl = i18n.global && i18n.global.locale
    const loc = typeof gl === 'string' ? gl : (gl && gl.value) || 'en'
    config.headers['Accept-Language'] = loc
  } catch (_) {
    config.headers['Accept-Language'] = 'en'
  }

  return config
})

// Response Interceptor
http.interceptors.response.use(
  response => response,
  error => {
    // যদি 401 বা token expire হয়
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default http
