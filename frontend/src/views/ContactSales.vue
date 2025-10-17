<template>
  <div class="contact-page">
    <section class="hero card">
      <div class="hero-copy">
        <h1>{{ t('contactSales.heroTitle') }}</h1>
        <p>{{ t('contactSales.heroSubtitle') }}</p>
        <ul class="highlights">
          <li>{{ t('contactSales.highlightOne') }}</li>
          <li>{{ t('contactSales.highlightTwo') }}</li>
          <li>{{ t('contactSales.highlightThree') }}</li>
        </ul>
      </div>
      <div class="hero-meta">
        <div class="meta-block">
          <span class="meta-label">{{ t('contactSales.metaEmailLabel') }}</span>
          <a class="meta-link" :href="'mailto:' + SALES_EMAIL">{{ SALES_EMAIL }}</a>
        </div>
        <div class="meta-block">
          <span class="meta-label">{{ t('contactSales.metaChatLabel') }}</span>
          <router-link class="meta-link" to="/upgrade">{{ t('contactSales.metaChatLink') }}</router-link>
        </div>
      </div>
    </section>

    <section class="form-card card">
      <header>
        <h2>{{ t('contactSales.formTitle') }}</h2>
        <p>{{ t('contactSales.formSubtitle') }}</p>
      </header>

      <transition name="fade">
        <div v-if="feedback.message" :class="['alert', `alert-${feedback.type}`]">{{ feedback.message }}</div>
      </transition>

      <form class="sales-form" @submit.prevent="submit">
        <label>
          {{ t('contactSales.fullNameLabel') }}
          <input v-model="form.full_name" type="text" required :placeholder="t('contactSales.fullNamePlaceholder')" />
        </label>
        <label>
          {{ t('contactSales.emailLabel') }}
          <input v-model="form.email" type="email" required :placeholder="emailPlaceholder" />
        </label>
        <div class="form-row">
          <label>
            {{ t('contactSales.companyLabel') }}
            <input v-model="form.company" type="text" :placeholder="t('contactSales.companyPlaceholder')" />
          </label>
          <label>
            {{ t('contactSales.roleLabel') }}
            <input v-model="form.role" type="text" :placeholder="t('contactSales.rolePlaceholder')" />
          </label>
        </div>
        <label>
          {{ t('contactSales.desiredPlanLabel') }}
          <select v-model="form.desired_plan">
            <option value="enterprise">{{ t('upgradePage.plans.enterprise.name') }}</option>
            <option value="pro">{{ t('upgradePage.plans.pro.name') }}</option>
            <option value="starter">{{ t('upgradePage.plans.starter.name') }}</option>
          </select>
        </label>
        <label>
          {{ t('contactSales.messageLabel') }}
          <textarea
            v-model="form.message"
            rows="5"
            :placeholder="t('contactSales.messagePlaceholder')"
          ></textarea>
        </label>
        <button type="submit" class="cta" :disabled="submitting">
          <span v-if="submitting">{{ t('contactSales.submitting') }}</span>
          <span v-else>{{ t('contactSales.submit') }}</span>
        </button>
      </form>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { submitSalesInquiry, loadCachedPlan } from '../services/subscription'

const route = useRoute()
const { t } = useI18n()
const SALES_EMAIL = 'hello@docuiq.ai'

const form = reactive({
  full_name: '',
  email: '',
  company: '',
  role: '',
  desired_plan: 'enterprise',
  message: '',
})

const submitting = ref(false)
const feedback = ref({ message: '', type: 'success' })
const emailPlaceholder = computed(() => {
  const user = t('contactSales.emailPlaceholderUser')
  const domain = t('contactSales.emailPlaceholderDomain')
  return `${user}@${domain}`
})

const resetForm = () => {
  const selectedPlan = form.desired_plan
  form.full_name = ''
  form.email = ''
  form.company = ''
  form.role = ''
  form.message = ''
  form.desired_plan = selectedPlan || 'enterprise'
}

const submit = async () => {
  submitting.value = true
  feedback.value = { message: '', type: 'success' }
  try {
    await submitSalesInquiry(form)
    feedback.value = { message: t('contactSales.success'), type: 'success' }
    resetForm()
  } catch (err) {
    feedback.value = { message: err?.message || t('contactSales.error'), type: 'error' }
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  const desired = (route.query.plan || '').toString().toLowerCase()
  if (desired && ['enterprise', 'pro', 'starter'].includes(desired)) {
    form.desired_plan = desired
  } else {
    const cached = loadCachedPlan()
    if (cached?.code) {
      form.desired_plan = cached.code
    }
  }
})
</script>

<style scoped>
.contact-page{
  display:flex;
  flex-direction:column;
  gap:24px;
  padding:12px 0 48px;
  color:#1f2937;
}

.card{
  background:#fff;
  border:1px solid #e2e8f0;
  border-radius:20px;
  padding:24px;
  box-shadow:0 12px 32px rgba(15,23,42,0.06);
}

.hero{
  display:flex;
  justify-content:space-between;
  gap:24px;
}

.hero-copy h1{
  font-size:32px;
  font-weight:800;
  margin:0 0 12px;
}

.hero-copy p{
  margin:0;
  font-size:16px;
  line-height:1.6;
  color:#64748b;
}

.highlights{
  margin:18px 0 0;
  padding-left:20px;
  color:#475569;
  display:flex;
  flex-direction:column;
  gap:6px;
}

.hero-meta{
  min-width:220px;
  display:flex;
  flex-direction:column;
  gap:16px;
  align-items:flex-start;
}

.meta-block{
  background:rgba(37,99,235,0.08);
  border:1px solid rgba(37,99,235,0.2);
  border-radius:16px;
  padding:14px 16px;
  width:100%;
}

.meta-label{
  font-size:12px;
  text-transform:uppercase;
  letter-spacing:0.1em;
  color:#1d4ed8;
}

.meta-link{
  display:block;
  margin-top:4px;
  font-weight:700;
  color:#1f2937;
  text-decoration:none;
}

.form-card header h2{
  margin:0 0 8px;
  font-size:24px;
  font-weight:800;
}

.form-card header p{
  margin:0 0 18px;
  color:#64748b;
}

.sales-form{
  display:flex;
  flex-direction:column;
  gap:18px;
}

label{ display:flex; flex-direction:column; gap:6px; font-weight:600; color:#1f2937; }
input,select,textarea{
  border:1px solid #cbd5f5;
  border-radius:10px;
  padding:11px 12px;
  font-size:15px;
  color:#1e293b;
  background:#f8fafc;
  transition:border .2s ease, box-shadow .2s ease;
}
input:focus,select:focus,textarea:focus{
  outline:none;
  border-color:#2563eb;
  box-shadow:0 0 0 3px rgba(37,99,235,0.15);
  background:#fff;
}

.form-row{
  display:grid;
  grid-template-columns:repeat(2, minmax(0, 1fr));
  gap:16px;
}

.cta{
  align-self:flex-start;
  border:none;
  border-radius:999px;
  padding:12px 22px;
  font-weight:700;
  background:#2563eb;
  color:#fff;
  cursor:pointer;
  transition:transform .2s ease, box-shadow .2s ease;
}

.cta:hover{ transform:translateY(-2px); box-shadow:0 10px 24px rgba(37,99,235,0.25); }
.cta:disabled{ opacity:0.7; cursor:not-allowed; transform:none; box-shadow:none; }

.alert{
  padding:12px 16px;
  border-radius:12px;
  font-weight:600;
}
.alert-success{ background:rgba(22,163,74,0.12); border:1px solid rgba(22,163,74,0.2); color:#166534; }
.alert-error{ background:rgba(220,38,38,0.12); border:1px solid rgba(220,38,38,0.2); color:#b91c1c; }

.fade-enter-active,.fade-leave-active{ transition:opacity .25s ease; }
.fade-enter-from,.fade-leave-to{ opacity:0; }

@media (max-width:960px){
  .hero{ flex-direction:column; }
  .meta-block{ display:flex; justify-content:space-between; align-items:center; }
}

@media (max-width:640px){
  .card{ padding:20px; }
  .form-row{ grid-template-columns:1fr; }
}
</style>
