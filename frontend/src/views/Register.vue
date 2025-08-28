<template>
  <div class="register-bg">
    <div class="register-container">
      <h2>{{ $t('signUp') }}</h2>
      <form @submit.prevent="onRegister">
        <div class="form-group">
          <label>{{ $t('accountType') }}</label>
          <div class="radio-group">
            <label>
              <input type="radio" value="individual" v-model="accountType" />
              {{ $t('individual') }}
            </label>
            <label>
              <input type="radio" value="organization" v-model="accountType" />
              {{ $t('organization') }}
            </label>
          </div>
        </div>
        <div class="form-group" v-if="accountType === 'individual'">
          <label for="name">{{ $t('yourName') }}</label>
          <input
            v-model="name"
            id="name"
            type="text"
            :placeholder="$t('namePlaceholder')"
          />
          <div class="error"  v-if="submitted && clientErrors.name">{{ clientErrors.name }}</div>
        </div>
        <div class="form-group" v-if="accountType === 'organization'">
          <label for="orgName">{{ $t('orgName') }}</label>
          <input
            v-model="orgName"
            id="orgName"
            type="text"
            :placeholder="$t('orgNamePlaceholder')"
          />
          <div class="error"  v-if="submitted && clientErrors.orgName">{{ clientErrors.orgName }}</div>
        </div>
        <div class="form-group">
          <label for="email">{{ $t('email') }}</label>
          <input
            v-model="email"
            id="email"
            type="email"
            :placeholder="$t('emailPlaceholder')"
            autocomplete="email"
          />
          <div class="error"  v-if="submitted && clientErrors.email">{{ clientErrors.email }}</div>
        </div>
        <div class="form-group">
          <label for="password">{{ $t('password') }}</label>
          <input
            v-model="password"
            id="password"
            type="password"
            minlength="8"
            :placeholder="$t('passwordPlaceholder')"
            autocomplete="new-password"
          />
          <div class="error" v-if="submitted && clientErrors.password">{{ clientErrors.password }}</div>
        </div>
        <button type="submit" class="register-btn" :disabled="loading">
          <span v-if="loading">{{ $t('signingIn') }}</span>
          <span v-else>{{ $t('signUp') }}</span>
        </button>
      </form>
      <div v-if="error" class="register-error">{{ error }}</div>
      <div v-if="success" class="register-success">{{ $t('registrationSuccess') }}</div>
      <div class="register-footer">
        <router-link to="/login">{{ $t('login') }}</router-link>
      </div>
      <div class="lang-switch-bottom">
        <LanguageSwitcher />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'
import { API_BASE_URL } from '../config'

const { t } = useI18n()
const accountType = ref('individual')
const name = ref('')
const orgName = ref('')
const email = ref('')
const password = ref('')
const error = ref('')
const success = ref(false)
const loading = ref(false)
const clientErrors = ref({})
const submitted = ref(false)

const clientValidate = () => {
  clientErrors.value = {}
  if (accountType.value === 'individual') {
    if (!name.value.trim()) {
      clientErrors.value.name = t('nameRequired')
    }
  }
  if (accountType.value === 'organization') {
    if (!orgName.value.trim()) {
      clientErrors.value.orgName = t('orgNameRequired')
    }
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value))
    clientErrors.value.email = t('invalidEmail')
  if (password.value.length < 8)
    clientErrors.value.password = t('shortPassword')
}

const hasClientErrors = computed(() => Object.keys(clientErrors.value).length > 0)
const router = useRouter()

const onRegister = async () => {
  submitted.value = true
  clientValidate()
  if (hasClientErrors.value) return

  error.value = ''
  success.value = false
  loading.value = true
  try {
    const res = await fetch(`${API_BASE_URL}/api/accounts/register/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        account_type: accountType.value,
        name: name.value,
        org_name: orgName.value,
        email: email.value,
        password: password.value,
      }),
    })
    const data = await res.json()
    if (res.ok) {
      success.value = true
      setTimeout(() => router.push('/login'), 1200)
    } else {
      error.value = (typeof data === 'object' && Object.values(data)[0]) || t('registrationFailed')
    }
  } catch (e) {
    error.value = t('networkError')
  }
  loading.value = false
}
</script>

<style scoped>
.register-bg {
  min-height: 100vh;
  background: linear-gradient(135deg, #3f51b5 0%, #2196f3 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}
.register-container {
  background: #fff;
  padding: 2.3rem 2rem 2rem 2rem;
  border-radius: 18px;
  box-shadow: 0 6px 32px 0 rgba(63, 81, 181, 0.11);
  max-width: 370px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}
h2 {
  margin-bottom: 20px;
  font-size: 1.35rem;
  font-weight: 700;
  color: #2788df;
  letter-spacing: .4px;
}
.radio-group {
  display: flex;
  gap: 18px;
  margin: 8px 0 3px 0;
  font-size: 1rem;
}
.form-group {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  width: 100%;
  margin-bottom: 16px;
}
.form-group label {
  font-size: 0.97rem;
  color: #444;
  margin-bottom: 7px;
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
.register-btn {
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
  width: 100%;
}
.register-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
.register-error {
  color: #f44336;
  margin-top: 10px;
  font-size: 0.97rem;
  text-align: center;
}
.register-success {
  color: #2196f3;
  margin-top: 10px;
  font-size: 0.98rem;
  text-align: center;
}
.register-footer {
  margin-top: 22px;
  font-size: 0.96rem;
  color: #555;
  text-align: center;
}
.register-footer a {
  color: #2196f3;
  text-decoration: none;
  font-weight: 600;
  margin-left: 4px;
}
.lang-switch-bottom {
  width: 100%;
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
@media (max-width: 500px) {
  .register-container {
    padding: 1.2rem 0.7rem 1.1rem 0.7rem;
    max-width: 95vw;
  }
}
.error { color: #e00; font-size: 0.95rem; margin-top: 3px; }
.success { color: #2196f3; margin-top: 10px; }
</style>
