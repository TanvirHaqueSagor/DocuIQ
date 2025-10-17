import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import i18n from './i18n'
import './style.css'

// Apply theme early based on saved preference
try {
  const el = document.documentElement
  const saved = localStorage.getItem('theme') || 'system'
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
  const mode = saved === 'system' ? (prefersDark ? 'dark' : 'light') : saved
  el.setAttribute('data-theme', mode)
} catch(_) {}

createApp(App)
  .use(router)
  .use(i18n)
  .mount('#app')
