<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100">
    <form class="bg-white p-6 rounded shadow-md" @submit.prevent="login">
      <h2 class="text-2xl font-bold mb-4">Login</h2>
      <input v-model="username" type="text" placeholder="Username" class="input mb-2 w-full" />
      <input v-model="password" type="password" placeholder="Password" class="input mb-4 w-full" />
      <button type="submit" class="bg-blue-500 text-white px-4 py-2 rounded">Login</button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
const username = ref('')
const password = ref('')
const login = async () => {
  const { data } = await axios.post('/api/token/', { username: username.value, password: password.value })
  localStorage.setItem('access', data.access)
  localStorage.setItem('refresh', data.refresh)
  location.href = '/'
}
</script>
