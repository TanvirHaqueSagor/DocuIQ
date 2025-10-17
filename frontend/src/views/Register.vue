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
          <div class="error" v-if="submitted && clientErrors.name">{{ clientErrors.name }}</div>
        </div>

        <div class="form-group" v-if="accountType === 'organization'">
          <label for="orgName">{{ $t('orgName') }}</label>
          <input
            v-model="orgName"
            id="orgName"
            type="text"
            :placeholder="$t('orgNamePlaceholder')"
          />
          <div class="error" v-if="submitted && clientErrors.orgName">{{ clientErrors.orgName }}</div>
        </div>

        <!-- NEW: Subdomain (org only) -->
        <div class="form-group" v-if="accountType === 'organization'">
          <label for="subdomain">{{ $t('subdomain') || 'Subdomain' }}</label>
          <input
            v-model="subdomain"
            id="subdomain"
            type="text"
            :placeholder="$t('subdomainPlaceholder') || 'e.g. acme'"
          />
          <small class="hint">
            {{ $t('preview') || 'Preview' }}:
            <strong>{{ subdomainPreview }}</strong>
          </small>
          <div class="error" v-if="submitted && clientErrors.subdomain">{{ clientErrors.subdomain }}</div>
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
          <div class="error" v-if="submitted && clientErrors.email">{{ clientErrors.email }}</div>
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
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'
import { API_BASE_URL } from '../config'

const { t } = useI18n()
const router = useRouter()

const accountType = ref('individual')
const name = ref('')
const orgName = ref('')
const subdomain = ref('') // NEW
const email = ref('')
const password = ref('')

const error = ref('')
const success = ref(false)
const loading = ref(false)
const clientErrors = ref({})
const submitted = ref(false)

const ROOT_DOMAIN = import.meta.env.VITE_ROOT_DOMAIN || window.location.hostname

const normalizedSubdomain = computed(() =>
  (subdomain.value || '').trim().toLowerCase()
)

const subdomainPreview = computed(() => {
  const sub = normalizedSubdomain.value
  return sub ? `${sub}.${ROOT_DOMAIN}` : ROOT_DOMAIN
})

// basic subdomain rule: 2-63 chars, a-z0-9 and hyphen, must start/end alnum, no reserved
const isValidSubdomain = (s) => {
  const v = (s || '').trim().toLowerCase()
  if (v.length < 2 || v.length > 63) return false
  if (!/^[a-z0-9]([a-z0-9-]*[a-z0-9])$/.test(v)) return false
  const reserved = new Set(['www', 'api', 'admin'])
  return !reserved.has(v)
}

watch(accountType, () => {
  // reset org-only fields on switch
  if (accountType.value === 'individual') {
    orgName.value = ''
    subdomain.value = ''
  }
})

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
    const sd = normalizedSubdomain.value
    if (!sd) {
      clientErrors.value.subdomain = t('subdomainRequired') || 'Subdomain is required'
    } else if (!isValidSubdomain(sd)) {
      clientErrors.value.subdomain =
        t('subdomainInvalid') || 'Only letters, numbers, hyphens; 2–63 chars; cannot be reserved (www, api, admin).'
    }
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test((email.value || '').trim()))
    clientErrors.value.email = t('invalidEmail')

  if ((password.value || '').length < 8)
    clientErrors.value.password = t('shortPassword')
}

const hasClientErrors = computed(() => Object.keys(clientErrors.value).length > 0)

const onRegister = async () => {
  submitted.value = true
  clientValidate()
  if (hasClientErrors.value) return

  error.value = ''
  success.value = false
  loading.value = true

  try {
    const body = {
      account_type: accountType.value,
      name: name.value,
      org_name: orgName.value,
      email: (email.value || '').trim().toLowerCase(),
      password: password.value,
    }
    if (accountType.value === 'organization') {
      body.subdomain = normalizedSubdomain.value
    }

    const res = await fetch(`${API_BASE_URL}/api/accounts/register/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    const data = await res.json().catch(() => ({}))

    if (res.ok) {
      success.value = true
      setTimeout(() => router.push('/login'), 1200)
    } else {
      // Try to map server-side field errors nicely
      if (data && typeof data === 'object') {
        // prefer field-level mapping when possible
        const fields = ['email', 'password', 'name', 'org_name', 'subdomain', 'account_type', 'detail']
        let shown = false
        for (const f of fields) {
          if (data[f]) {
            const msg = Array.isArray(data[f]) ? data[f][0] : data[f]
            clientErrors.value[f === 'org_name' ? 'orgName' : f] = msg
            shown = true
          }
        }
        if (!shown) {
          const firstKey = Object.keys(data)[0]
          const firstVal = data[firstKey]
          error.value = Array.isArray(firstVal) ? firstVal[0] : (firstVal || t('registrationFailed'))
        }
      } else {
        error.value = t('registrationFailed')
      }
    }
  } catch (e) {
    error.value = t('networkError')
  } finally {
    loading.value = false
  }
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
  background: var(--card);
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
  color: var(--blue);
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
  background: var(--card);
}
.hint {
  margin-top: 6px;
  font-size: 0.85rem;
  color: #607d8b;
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
