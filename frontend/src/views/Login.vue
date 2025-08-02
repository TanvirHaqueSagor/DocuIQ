<template>
  <div class="login-container">
    <h2>Login</h2>
    <form @submit.prevent="login">
      <input v-model="username" placeholder="Username" required />
      <input type="password" v-model="password" placeholder="Password" required />
      <button type="submit">Login</button>
    </form>
    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  data() {
    return {
      username: '',
      password: '',
      error: ''
    }
  },
  methods: {
    async login() {
      try {
        const res = await axios.post(import.meta.env.VITE_API_URL + '/api/login/', {
          username: this.username,
          password: this.password
        })
        const token = res.data.access
        localStorage.setItem('access_token', token)
        this.$router.push('/dashboard') // বা যেখানেই redirect করতে চাও
      } catch (err) {
        this.error = "Login failed"
      }
    }
  }
}
</script>

<style scoped>
.login-container {
  max-width: 300px;
  margin: auto;
}
.error {
  color: red;
}
</style>
