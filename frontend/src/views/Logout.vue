<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { API_BASE_URL } from '../config'

const router = useRouter()

onMounted(async () => {
  const token = localStorage.getItem('token')
  const refresh = localStorage.getItem('refresh')

  try {
    // ব্যাকএন্ডে refresh ব্ল্যাকলিস্ট (optional কিন্তু ভালো প্র্যাকটিস)
    if (token && refresh) {
      await fetch(`${API_BASE_URL}/api/accounts/logout/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ refresh })
      })
    }
  } catch (_) {
    // ব্যর্থ হলেও ক্লায়েন্ট-সাইড ক্লিয়ার করবই
  }

  // লোকাল ক্লিয়ার
  localStorage.removeItem('token')
  localStorage.removeItem('refresh')
  localStorage.removeItem('user')

  // লগইনে ফেরত
  router.replace('/login')
})
</script>

<template>
  <div style="padding:24px">{{ $t ? $t('loggingOut') : 'Logging out…' }}</div>
</template>
