<template>
  <div class="pricing-page">
    <section class="hero card">
      <div class="hero-copy">
        <h1>{{ t('upgradePage.heroTitle') }}</h1>
        <p>{{ t('upgradePage.heroSubtitle') }}</p>
        <div class="hero-actions">
          <button class="cta secondary" @click="scrollToSection('plans')">{{ t('upgradePage.heroPrimaryCta') }}</button>
          <button class="cta outline" @click="scrollToSection('comparison')">{{ t('upgradePage.heroSecondaryCta') }}</button>
        </div>
      </div>
      <div class="hero-status" v-if="planInfo">
        <span class="status-label">{{ t('upgradePage.statusLabel') }}</span>
        <span class="status-chip" :class="planChipClass">{{ currentPlanLabel }}</span>
        <p class="status-note" v-if="planInfo.source === 'organization'">{{ t('upgradePage.statusManaged') }}</p>
      </div>
    </section>

    <transition name="fade">
      <div v-if="feedback.message" :class="['alert', `alert-${feedback.type}`]">
        {{ feedback.message }}
      </div>
    </transition>

    <section class="plans-section" id="plans">
      <div class="plans-grid">
        <article
          v-for="plan in plans"
          :key="plan.id"
          class="plan-card card"
          :class="[plan.accentClass, { current: plan.isCurrent }]"
        >
          <header class="plan-header">
            <span class="plan-emoji" aria-hidden="true">{{ plan.emoji }}</span>
            <div class="plan-title">
              <h2>{{ plan.name }}</h2>
              <p class="plan-tagline">{{ plan.tagline }}</p>
            </div>
          </header>
          <p class="plan-price">{{ plan.price }}</p>
          <p class="plan-best">{{ plan.bestFor }}</p>
          <p v-if="plan.includesNote" class="plan-note">{{ plan.includesNote }}</p>
          <ul class="plan-features">
            <li v-for="feature in plan.features" :key="feature">
              <span class="check" aria-hidden="true">✔</span>
              <span>{{ feature }}</span>
            </li>
          </ul>
          <button
            class="cta primary"
            :class="plan.buttonClass"
            :disabled="plan.disabled || planLoading || (upgrading && plan.id === 'pro')"
            @click="handleCta(plan)"
          >
            <span v-if="plan.isCurrent">{{ t('upgradePage.planCurrentLabel') }}</span>
            <span v-else-if="upgrading && plan.id === 'pro'">{{ t('upgradePage.planUpdatingLabel') }}</span>
            <span v-else>{{ plan.ctaLabel }}</span>
          </button>
        </article>
      </div>
    </section>

    <section class="addons-section card">
      <header class="section-head">
        <h2>{{ t('upgradePage.addonsTitle') }}</h2>
        <p>{{ t('upgradePage.addonsSubtitle') }}</p>
      </header>
      <div class="table-wrap">
        <table class="addons-table">
          <thead>
            <tr>
              <th>{{ addonsHeaders.name }}</th>
              <th>{{ addonsHeaders.description }}</th>
              <th>{{ addonsHeaders.price }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="addOn in addOns" :key="addOn.name">
              <td>{{ addOn.name }}</td>
              <td>{{ addOn.description }}</td>
              <td>{{ addOn.price }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="comparison-section card" id="comparison">
      <header class="section-head">
        <h2>{{ t('upgradePage.comparisonTitle') }}</h2>
        <p>{{ t('upgradePage.comparisonSubtitle') }}</p>
      </header>
      <div class="table-wrap comparison-table">
        <table>
          <thead>
            <tr>
              <th scope="col">{{ comparisonHeaders.feature }}</th>
              <th scope="col">{{ comparisonHeaders.starter }}</th>
              <th scope="col">{{ comparisonHeaders.pro }}</th>
              <th scope="col">{{ comparisonHeaders.enterprise }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in comparisonRows" :key="row.feature">
              <th scope="row">{{ row.feature }}</th>
              <td :data-label="comparisonHeaders.starter">{{ row.starter }}</td>
              <td :data-label="comparisonHeaders.pro">{{ row.pro }}</td>
              <td :data-label="comparisonHeaders.enterprise">{{ row.enterprise }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="faq-section card">
      <header class="section-head">
        <h2>{{ t('upgradePage.faqTitle') }}</h2>
      </header>
      <div class="faq-grid">
        <details v-for="item in faqItems" :key="item.q" class="faq-item">
          <summary>{{ item.q }}</summary>
          <p>{{ item.a }}</p>
        </details>
      </div>
    </section>
  </div>
</template>

<script>
import { defineComponent, computed, ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { fetchSubscriptionPlan, updateSubscriptionPlan, loadCachedPlan } from '../services/subscription'

export default defineComponent({
  name: 'PricingPage',
  setup() {
    const router = useRouter()
    const route = useRoute()
    const { t, tm } = useI18n()

    const planInfo = ref(loadCachedPlan())
    const planLoading = ref(false)
    const upgrading = ref(false)
    const feedback = ref({ message: '', type: 'success' })

    const getObject = (key) => {
      if (typeof tm === 'function') {
        const value = tm(key)
        return value && typeof value === 'object' && !Array.isArray(value) ? value : {}
      }
      return {}
    }

    const getArray = (key) => {
      if (typeof tm === 'function') {
        const value = tm(key)
        return Array.isArray(value) ? value : []
      }
      return []
    }

    const planDefinitions = computed(() => {
      const plansMessage = getObject('upgradePage.plans')
      const ids = ['starter', 'pro', 'enterprise']
      return ids.map((id) => {
        const info = plansMessage[id] || {}
        const visuals = {
          starter: { emoji: '🟩', accentClass: 'plan-green', buttonClass: 'cta-green' },
          pro: { emoji: '🟦', accentClass: 'plan-blue', buttonClass: 'cta-blue' },
          enterprise: { emoji: '🟨', accentClass: 'plan-yellow', buttonClass: 'cta-yellow' },
        }[id]
        return {
          id,
          emoji: visuals.emoji,
          accentClass: visuals.accentClass,
          buttonClass: visuals.buttonClass,
          name: info.name || '',
          tagline: info.tagline || '',
          price: info.price || '',
          bestFor: info.bestFor || '',
          includesNote: info.includes || '',
          ctaLabel: info.cta || '',
          features: Array.isArray(info.features) ? info.features : [],
        }
      })
    })

    const plans = computed(() => {
      const currentCode = planInfo.value?.code || ''
      return planDefinitions.value.map(plan => ({
        ...plan,
        isCurrent: currentCode === plan.id,
        disabled: currentCode === plan.id,
      }))
    })

    const addOns = computed(() => getArray('upgradePage.addons'))
    const addonsHeaders = computed(() => {
      const headers = getObject('upgradePage.addonsHeaders')
      return {
        name: headers.name || t('upgradePage.addonsHeaders.name'),
        description: headers.description || t('upgradePage.addonsHeaders.description'),
        price: headers.price || t('upgradePage.addonsHeaders.price'),
      }
    })
    const comparisonRows = computed(() => getArray('upgradePage.comparisonRows'))
    const comparisonHeaders = computed(() => {
      const headers = getObject('upgradePage.comparisonHeaders')
      return {
        feature: headers.feature || t('upgradePage.comparisonHeaders.feature'),
        starter: headers.starter || t('upgradePage.comparisonHeaders.starter'),
        pro: headers.pro || t('upgradePage.comparisonHeaders.pro'),
        enterprise: headers.enterprise || t('upgradePage.comparisonHeaders.enterprise'),
      }
    })
    const faqItems = computed(() => getArray('upgradePage.faq'))

    const planChipClass = computed(() => {
      const code = planInfo.value?.code
      if (code === 'pro') return 'chip-blue'
      if (code === 'enterprise') return 'chip-gold'
      return 'chip-green'
    })

    const currentPlanLabel = computed(() => {
      const code = planInfo.value?.code
      if (!code) {
        return planInfo.value?.label || ''
      }
      const translated = t(`upgradePage.plans.${code}.name`, planInfo.value?.label || code)
      return translated || planInfo.value?.label || t('upgradePage.planStatusUnknown')
    })

    const applyPlan = (data) => {
      if (!data) return
      const code = data.code || ''
      const translatedName = code ? t(`upgradePage.plans.${code}.name`, code) : ''
      planInfo.value = {
        ...data,
        label: data.label || translatedName || t('upgradePage.planStatusUnknown'),
      }
      try { localStorage.setItem('subscription_plan', JSON.stringify(planInfo.value)) } catch (_) {}
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('docuiq-plan-changed', { detail: planInfo.value }))
      }
    }

    const loadPlan = async () => {
      planLoading.value = true
      feedback.value = { message: '', type: 'success' }
      try {
        const data = await fetchSubscriptionPlan()
        applyPlan(data)
        const desired = (route.query.plan || '').toString().toLowerCase()
        if (desired && desired !== data.code && desired !== 'starter') {
          if (desired === 'pro') {
            feedback.value = { message: t('upgradePage.feedbackPro'), type: 'info' }
          } else if (desired === 'enterprise') {
            feedback.value = { message: t('upgradePage.feedbackEnterprise'), type: 'info' }
          }
        }
      } catch (err) {
        feedback.value = { message: t('upgradePage.feedbackLoadError'), type: 'error' }
      } finally {
        planLoading.value = false
      }
    }

    const handleCta = async (plan) => {
      if (!plan || plan.disabled) return
      if (plan.id === 'starter') {
        router.push('/documents')
        return
      }
      if (plan.id === 'pro') {
        upgrading.value = true
        feedback.value = { message: '', type: 'success' }
        try {
          const data = await updateSubscriptionPlan('pro')
          applyPlan(data)
          feedback.value = { message: t('upgradePage.feedbackUpgradeSuccess'), type: 'success' }
        } catch (err) {
          feedback.value = { message: err?.message || t('upgradePage.feedbackUpgradeError'), type: 'error' }
        } finally {
          upgrading.value = false
        }
        return
      }
      if (plan.id === 'enterprise') {
        router.push({ path: '/contact-sales', query: { plan: 'enterprise' } })
      }
    }

    const scrollToSection = (anchorId) => {
      const el = document.getElementById(anchorId)
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }

    onMounted(() => {
      if (planInfo.value && !planInfo.value.label) {
        const code = planInfo.value.code
        const translatedName = code ? t(`upgradePage.plans.${code}.name`, code) : ''
        planInfo.value.label = translatedName || planInfo.value.code || t('upgradePage.planStatusUnknown')
      }
      loadPlan()
    })

    return {
      t,
      plans,
      addOns,
      addonsHeaders,
      comparisonRows,
      comparisonHeaders,
      faqItems,
      planInfo,
      currentPlanLabel,
      planLoading,
      upgrading,
      feedback,
      planChipClass,
      handleCta,
      scrollToSection,
    }
  },
})
</script>

<style scoped>
.pricing-page{
  display:flex;
  flex-direction:column;
  gap:24px;
  padding:12px 0 48px;
  color:var(--text);
  --text:#1f2937;
  --text-muted:#64748b;
  --border:#e2e8f0;
  --card:#ffffff;
  --shadow:0 12px 32px rgba(15,23,42,0.08);
  --green:#16a34a;
  --blue:#2563eb;
  --yellow:#d97706;
}

.card{
  background:var(--card);
  border:1px solid var(--border);
  border-radius:20px;
  padding:24px;
  box-shadow:var(--shadow);
}

.hero{
  display:flex;
  justify-content:space-between;
  align-items:flex-start;
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
  color:var(--text-muted);
}

.hero-actions{
  margin-top:20px;
  display:flex;
  gap:12px;
  flex-wrap:wrap;
}

.hero-status{
  min-width:220px;
  display:flex;
  flex-direction:column;
  gap:8px;
  padding:16px;
  border-radius:18px;
  background:rgba(37,99,235,0.08);
  border:1px solid rgba(37,99,235,0.25);
  align-self:stretch;
}

.status-label{
  font-size:13px;
  text-transform:uppercase;
  letter-spacing:0.08em;
  color:#1d4ed8;
}

.status-chip{
  display:inline-flex;
  align-items:center;
  padding:6px 12px;
  border-radius:999px;
  font-weight:700;
}

.chip-green{ background:rgba(22,163,74,0.18); color:#166534; }
.chip-blue{ background:rgba(37,99,235,0.18); color:#1d4ed8; }
.chip-gold{ background:rgba(217,119,6,0.2); color:#b45309; }

.status-note{
  margin:0;
  font-size:13px;
  color:#475569;
}

.cta{
  border:none;
  border-radius:999px;
  padding:12px 20px;
  font-weight:700;
  font-size:15px;
  cursor:pointer;
  transition:transform .2s ease, box-shadow .2s ease, background .2s ease, color .2s ease;
}

.cta.primary{ width:100%; justify-content:center; }

.cta.primary:hover,.cta.secondary:hover{
  transform:translateY(-2px);
  box-shadow:0 10px 24px rgba(15,23,42,0.12);
}

.cta.secondary{ background:var(--blue); color:#fff; }
.cta.secondary:hover{ background:#1d4ed8; }

.cta.outline{ border:1px solid var(--border); background:transparent; color:var(--text); }
.cta.outline:hover{ background:#f1f5f9; }

.cta:disabled{
  cursor:not-allowed;
  opacity:0.7;
  transform:none;
  box-shadow:none;
}

.plans-grid{
  display:grid;
  grid-template-columns:repeat(3, minmax(0, 1fr));
  gap:20px;
}

.plan-card{
  display:flex;
  flex-direction:column;
  gap:16px;
  position:relative;
  overflow:hidden;
  transition:transform .2s ease, box-shadow .2s ease;
}

.plan-card:hover{
  transform:translateY(-6px);
  box-shadow:0 24px 48px rgba(15,23,42,0.16);
}

.plan-card.current{
  border-width:2px;
}

.plan-header{ display:flex; gap:16px; align-items:center; }
.plan-emoji{ font-size:32px; }
.plan-title h2{ margin:0; font-size:24px; font-weight:800; }
.plan-tagline{ margin:4px 0 0; font-size:16px; color:var(--text-muted); }
.plan-price{ margin:0; font-weight:700; font-size:18px; }
.plan-best{ margin:0; font-size:15px; color:var(--text-muted); }
.plan-note{ margin:8px 0 0; font-weight:600; color:var(--text); }

.plan-features{ list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:10px; }
.plan-features li{ display:flex; align-items:flex-start; gap:10px; font-size:14px; line-height:1.6; }
.plan-features .check{ color:var(--green); font-weight:700; margin-top:2px; }

.plan-green{ border:1px solid rgba(22,163,74,0.25); background:linear-gradient(160deg, rgba(22,163,74,0.12), rgba(22,163,74,0.04)); }
.plan-blue{ border:1px solid rgba(37,99,235,0.25); background:linear-gradient(160deg, rgba(37,99,235,0.15), rgba(37,99,235,0.05)); }
.plan-yellow{ border:1px solid rgba(217,119,6,0.25); background:linear-gradient(160deg, rgba(217,119,6,0.16), rgba(217,119,6,0.06)); }

.cta-green{ background:var(--green); color:#fff; }
.cta-green:hover{ background:#15803d; }
.cta-blue{ background:var(--blue); color:#fff; }
.cta-blue:hover{ background:#1d4ed8; }
.cta-yellow{ background:var(--yellow); color:#fff; }
.cta-yellow:hover{ background:#b45309; }

.section-head h2{ margin:0 0 6px; font-size:24px; font-weight:800; }
.section-head p{ margin:0; color:var(--text-muted); line-height:1.6; }

.table-wrap{ margin-top:20px; border-radius:16px; overflow:hidden; border:1px solid var(--border); }
.addons-table{ width:100%; border-collapse:collapse; font-size:14px; }
.addons-table th,.addons-table td{ padding:14px 16px; text-align:left; border-bottom:1px solid var(--border); }
.addons-table tbody tr:hover{ background:#f8fafc; }

.comparison-table{ overflow-x:auto; position:relative; }
.comparison-table table{ width:100%; border-collapse:collapse; font-size:14px; min-width:720px; }
.comparison-table th,.comparison-table td{ padding:14px 16px; border-bottom:1px solid var(--border); text-align:left; vertical-align:top; }
.comparison-table thead th{ position:sticky; top:0; background:#f8fafc; z-index:1; font-weight:700; }
.comparison-table tbody tr:nth-child(even){ background:#f9fbff; }
.comparison-table tbody tr:hover{ background:#eef2ff; }
.comparison-table th[scope="row"]{ font-weight:600; color:var(--text); }

.faq-grid{ display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:16px; }
.faq-item{ background:var(--card); border:1px solid var(--border); border-radius:14px; padding:16px 18px; box-shadow:var(--shadow); }
.faq-item summary{ font-weight:700; cursor:pointer; color:var(--text); list-style:none; }
.faq-item summary::-webkit-details-marker{ display:none; }
.faq-item summary::after{ content:"+"; float:right; font-weight:700; color:#1d4ed8; }
.faq-item[open] summary::after{ content:"−"; }
.faq-item p{ margin:12px 0 0; color:var(--text-muted); line-height:1.6; }

.alert{
  padding:14px 18px;
  border-radius:14px;
  font-weight:600;
}

.alert-success{ background:rgba(22,163,74,0.1); border:1px solid rgba(22,163,74,0.2); color:#166534; }
.alert-error{ background:rgba(220,38,38,0.1); border:1px solid rgba(220,38,38,0.2); color:#b91c1c; }
.alert-info{ background:rgba(37,99,235,0.1); border:1px solid rgba(37,99,235,0.2); color:#1d4ed8; }

.fade-enter-active,.fade-leave-active{ transition:opacity .25s ease; }
.fade-enter-from,.fade-leave-to{ opacity:0; }

@media (max-width:1100px){
  .plans-grid{ grid-template-columns:repeat(2, minmax(0, 1fr)); }
  .faq-grid{ grid-template-columns:repeat(2, minmax(0, 1fr)); }
}

@media (max-width:870px){
  .hero{ flex-direction:column; }
  .hero-status{ width:100%; align-items:flex-start; }
  .plans-grid{ grid-template-columns:1fr; }
}

@media (max-width:640px){
  .card{ padding:20px; }
  .hero-copy h1{ font-size:26px; }
  .comparison-table table{ font-size:13px; }
  .comparison-table th,.comparison-table td{ padding:12px; }
  .faq-grid{ grid-template-columns:1fr; }
}

@media (max-width:480px){
  .cta{ width:100%; }
  .hero-actions{ flex-direction:column; gap:10px; }
}
</style>
