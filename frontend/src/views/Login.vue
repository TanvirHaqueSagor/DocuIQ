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
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { API_BASE_URL } from '../config'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'

// Root domain derive: VITE_ROOT_DOMAIN থাকলে সেটা, না থাকলে current host থেকে প্রথম লেবেল ড্রপ
const deriveRootDomain = (hn) => {
  if (!hn) return 'localhost'
  if (hn === 'localhost') return 'localhost'
  const parts = hn.split('.')
  if (parts.length >= 2) return parts.slice(1).join('.')  // toyota.localhost -> localhost, acme.127.0.0.1.nip.io -> 127.0.0.1.nip.io
  return hn
}
const ROOT_DOMAIN = import.meta.env.VITE_ROOT_DOMAIN || deriveRootDomain(window.location.hostname)

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

const router = useRouter()
const route = useRoute()
const { t } = useI18n()

// 🚀 Auth-bridge: সাবডোমেইনে এলে URL hash থেকে টোকেন তুলে লোকালস্টোরেজে বসিয়ে দিন
const readHashTokens = () => {
  const h = window.location.hash || ''
  if (!h.startsWith('#')) return null
  const p = new URLSearchParams(h.slice(1))
  const at = p.get('at'); const rt = p.get('rt')
  if (!at) return null
  return { at, rt }
}
onMounted(() => {
  const tok = readHashTokens()
  if (tok && tok.at) {
    localStorage.setItem('token', tok.at)
    if (tok.rt) localStorage.setItem('refresh', tok.rt)
    // hash মুছে দিন যেন রিলোডে আবার প্রসেস না হয়
    history.replaceState(null, '', window.location.pathname + window.location.search)
    const target = (route.query.redirect ? String(route.query.redirect) : '/dashboard')
    router.replace(target)
  }
})


const onSubmit = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await fetch(`${API_BASE_URL}/api/accounts/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      // JWT flow-এ credentials লাগবে না
      body: JSON.stringify({ email: email.value, password: password.value }),
    })

    // কিছু সময়ে backend থেকে HTML/empty আসলে json() ক্র্যাশ করে — তাই safe parse
    let data = null
    try {
      data = await res.json()
    } catch (_) {
      data = null
    }

    if (res.ok && data && data.access) {
      // টোকেন সেভ → router guard OK → axios Authorization OK
      localStorage.setItem('token', data.access)
      localStorage.setItem('access', data.access)   // fallback
      if (data.refresh) localStorage.setItem('refresh', data.refresh)
      if (data.user) localStorage.setItem('user', JSON.stringify(data.user))
      if (data.account_type) localStorage.setItem('account_type', data.account_type)
      if (data.org_subdomain) localStorage.setItem('org_subdomain', data.org_subdomain); else localStorage.removeItem('org_subdomain')

      // ✅ Redirect target (query থাকলে সেটা, না থাকলে /dashboard)
      const target = (route.query.redirect ? String(route.query.redirect) : '/dashboard')

      // ✅ Org হলে: যদি অন্য হোস্টে থাকি তবে ক্রস-ডোমেইন রিডাইরেক্ট; নইলে SPA ভেতরে নেভিগেট
      if (data.account_type === 'organization' && data.org_subdomain && ROOT_DOMAIN) {
        const expectedHost = `${data.org_subdomain}.${ROOT_DOMAIN}`
        const currentHost  = window.location.hostname
        if (currentHost !== expectedHost) {
          const proto = window.location.protocol
          const port  = window.location.port ? (':' + window.location.port) : ''
          // 🔁 টোকেন hash দিয়ে সাবডোমেইনে পাঠাই; Login.vue mounted হয়ে hash পড়ে সেট করবে
          const r = encodeURIComponent(target)
          const at = encodeURIComponent(data.access)
          const rt = data.refresh ? `&rt=${encodeURIComponent(data.refresh)}` : ''
          window.location.href = `${proto}//${expectedHost}${port}/login?redirect=${r}#at=${at}${rt}`
          return
        }
      }
      await router.replace(target)
      return
    }

    // 401/ভুল ক্রেডেনশিয়াল কেস
    if (data && (data.error || data.detail)) {
      error.value = t('invalidAuth')
    } else {
      // non-JSON বা অপ্রত্যাশিত রেসপন্স
      error.value = t('somethingWrong')
    }
  } catch (e) {
    error.value = t('somethingWrong')
  } finally {
    loading.value = false
  }
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
