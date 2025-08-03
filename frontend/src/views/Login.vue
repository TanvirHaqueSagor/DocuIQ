<template>
  <div class="login-bg">
    <div class="login-container">
      <div class="login-logo">
        <span class="brand-title">Docu<span class="brand-highlight">IQ</span></span>
      </div>
      <div class="welcome-text">{{ $t('welcome') }}</div>
      <h2 class="login-heading">{{ $t('signInTitle') }}</h2>
      <form @submit.prevent="onSubmit" class="login-form">
        <div class="form-group">
          <label for="email">{{ $t('email') }}</label>
          <input
            v-model="email"
            id="email"
            type="email"
            :placeholder="$t('emailPlaceholder')"
            required
            autofocus
            @input="error = ''"
          />
        </div>
        <div class="form-group">
          <label for="password">{{ $t('password') }}</label>
          <input
            v-model="password"
            id="password"
            type="password"
            :placeholder="$t('passwordPlaceholder')"
            required
            @input="error = ''"
          />
        </div>
        <button type="submit" class="login-btn" :disabled="loading">
          <span v-if="loading">{{ $t('signingIn') }}</span>
          <span v-else>{{ $t('login') }}</span>
        </button>
        <div v-if="error" class="login-error">{{ error }}</div>
      </form>
      <div class="login-footer">
        <span>{{ $t('noAccount') }}</span>
        <router-link to="/register">{{ $t('signUp') }}</router-link>
      </div>
      <div class="login-switcher-wrap">
        <LanguageSwitcher />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'
import { API_BASE_URL } from '../config'

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

const router = useRouter()
const { t } = useI18n()

const onSubmit = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await fetch(`${API_BASE_URL}/api/accounts/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email.value,
        password: password.value,
      }),
      credentials: 'include'
    })
    const data = await response.json()
    if (response.ok && data && !data.error) {
      router.push('/home')
    } else {
      error.value = t('invalidAuth')
    }
  } catch (e) {
    error.value = t('somethingWrong')
  }
  loading.value = false
}
</script>

<style scoped>
.login-bg {
  min-height: 100vh;
  background: linear-gradient(135deg, #3f51b5 0%, #2196f3 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}
.login-container {
  background: #fff;
  padding: 2.5rem 2rem 2rem 2rem;
  border-radius: 18px;
  box-shadow: 0 6px 32px 0 rgba(63, 81, 181, 0.12);
  max-width: 370px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.login-logo {
  margin-bottom: 10px;
  font-size: 2.1rem;
  font-weight: 700;
  color: #3f51b5;
  letter-spacing: -2px;
}
.brand-title {
  font-weight: 700;
  color: #3f51b5;
}
.brand-highlight {
  color: #2196f3;
}
.welcome-text {
  font-size: 1.12rem;
  color: #2788df;
  margin-bottom: 10px;
  text-align: center;
  font-weight: 600;
  letter-spacing: .3px;
}
.login-heading {
  font-size: 1.2rem;
  margin-bottom: 24px;
  color: #444;
  text-align: center;
}
.login-form {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 15px;
}
.form-group {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  width: 100%;
}
.form-group label {
  font-size: 0.98rem;
  color: #666;
  margin-bottom: 6px;
}
.form-group input {
  width: 100%;
  padding: 9px 12px;
  border: 1px solid #d6e0f5;
  border-radius: 8px;
  background: #f7faff;
  font-size: 1rem;
  outline: none;
  transition: border 0.2s;
}
.form-group input:focus {
  border: 1.7px solid #2196f3;
  background: #fff;
}
.login-btn {
  background: linear-gradient(90deg, #3f51b5 60%, #2196f3 100%);
  color: #fff;
  font-weight: 700;
  border: none;
  padding: 10px 0;
  border-radius: 8px;
  font-size: 1.1rem;
  margin-top: 10px;
  cursor: pointer;
  transition: box-shadow 0.15s;
  box-shadow: 0 2px 8px 0 rgba(33, 150, 243, 0.08);
}
.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
.login-error {
  color: #f44336;
  margin-top: 8px;
  font-size: 0.98rem;
  text-align: center;
}
.login-footer {
  margin-top: 22px;
  font-size: 0.95rem;
  color: #555;
  display: flex;
  gap: 6px;
  align-items: center;
  justify-content: center;
}
.login-footer a {
  color: #2196f3;
  text-decoration: none;
  font-weight: 600;
}
.login-switcher-wrap {
  display: flex;
  width: 100%;
  justify-content: center;
  margin-top: 20px;
}
@media (max-width: 500px) {
  .login-container {
    padding: 1.3rem 0.7rem 1.2rem 0.7rem;
    max-width: 95vw;
  }
}
</style>
