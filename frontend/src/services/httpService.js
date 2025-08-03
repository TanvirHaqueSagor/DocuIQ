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
  // যদি token/localStorage থাকে, add
  const token = localStorage.getItem('token')
  if (token) config.headers['Authorization'] = `Bearer ${token}`

  // language add করুন
  config.headers['Accept-Language'] = i18n.global.locale || 'en'

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
