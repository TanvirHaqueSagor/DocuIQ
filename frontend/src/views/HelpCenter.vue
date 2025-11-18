<template>
  <div class="page help-center">
    <section class="hero">
      <div class="hero-copy">
        <h1>{{ t('helpCenter.heroTitle') }}</h1>
        <p>{{ t('helpCenter.heroSubtitle') }}</p>
        <div class="search-box">
          <span aria-hidden="true">🔍</span>
          <input :placeholder="t('helpCenter.searchPlaceholder')" v-model="searchTerm" />
        </div>
      </div>
      <div class="hero-illustration" aria-hidden="true">🛟</div>
    </section>

    <section class="quick-links">
      <header>
        <h2>{{ t('helpCenter.quickLinksTitle') }}</h2>
        <p>{{ t('helpCenter.quickLinksSubtitle') }}</p>
      </header>
      <div class="link-grid">
        <article
          v-for="card in filteredQuickLinks"
          :key="card.key"
          class="link-card"
          @click="scrollTo(card.anchor)"
        >
          <div class="link-icon" aria-hidden="true">{{ card.icon }}</div>
          <div class="link-body">
            <h3>{{ card.title }}</h3>
            <p>{{ card.desc }}</p>
          </div>
          <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </article>
      </div>
    </section>

    <section
      v-for="section in filteredSections"
      :key="section.id"
      :id="section.id"
      class="section-card"
    >
      <header>
        <h2>{{ section.title }}</h2>
        <p v-if="section.summary">{{ section.summary }}</p>
      </header>
      <div class="article-grid">
        <article v-for="article in section.articles" :key="article.title" class="article-card">
          <h3>{{ article.title }}</h3>
          <p>{{ article.body }}</p>
        </article>
      </div>
    </section>

    <section class="faq-section">
      <header>
        <h2>{{ t('helpCenter.faqTitle') }}</h2>
      </header>
      <div class="faq-list">
        <details v-for="item in filteredFaq" :key="item.q">
          <summary>{{ item.q }}</summary>
          <p>{{ item.a }}</p>
        </details>
      </div>
    </section>

    <section class="cta">
      <div class="cta-content">
        <div class="cta-copy">
          <h3>{{ t('helpCenter.cta.title') }}</h3>
          <p>{{ t('helpCenter.cta.description') }}</p>
          <p class="cta-email">
            <span>{{ t('helpCenter.cta.emailLabel') }}</span>
            <a href="mailto:support@docuiq.ai">support@docuiq.ai</a>
          </p>
        </div>
        <button type="button" class="cta-button" @click="contactSupport">
          {{ t('helpCenter.cta.button') }}
        </button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t, tm } = useI18n()
const searchTerm = ref('')

const iconMap = {
  gettingStarted: '✨',
  workspaceAdmin: '🛡️',
  troubleshooting: '🛠️',
  bestPractices: '🚀',
}

const quickLinks = computed(() => {
  const links = tm('helpCenter.quickLinks')
  if (!Array.isArray(links)) return []
  return links.map((item) => ({
    ...item,
    icon: iconMap[item.key] || '📄',
  }))
})

const sections = computed(() => {
  const value = tm('helpCenter.sections')
  return Array.isArray(value) ? value : []
})

const faqItems = computed(() => {
  const value = tm('helpCenter.faq')
  return Array.isArray(value) ? value : []
})

const filteredQuickLinks = computed(() => {
  const term = searchTerm.value.trim().toLowerCase()
  if (!term) return quickLinks.value
  return quickLinks.value.filter((link) =>
    [link.title, link.desc].some((text) => (text || '').toLowerCase().includes(term))
  )
})

const filteredSections = computed(() => {
  const term = searchTerm.value.trim().toLowerCase()
  if (!term) return sections.value
  return sections.value
    .map((section) => {
      const articles = (section.articles || []).filter((article) =>
        [article.title, article.body].some((text) => (text || '').toLowerCase().includes(term))
      )
      if (articles.length) return { ...section, articles }
      if ((section.title || '').toLowerCase().includes(term)) return section
      return null
    })
    .filter(Boolean)
})

const filteredFaq = computed(() => {
  const term = searchTerm.value.trim().toLowerCase()
  if (!term) return faqItems.value
  return faqItems.value.filter((item) =>
    [item.q, item.a].some((text) => (text || '').toLowerCase().includes(term))
  )
})

function scrollTo(anchor) {
  if (!anchor) return
  const el = document.getElementById(anchor)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

function contactSupport() {
  window.open('mailto:support@docuiq.ai?subject=DocuIQ%20Help%20Request', '_blank')
}
</script>

<style scoped>
.help-center {
  display: grid;
  gap: 24px;
  padding-bottom: 48px;
}

.hero {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.12), rgba(14, 116, 144, 0.08));
  border-radius: 24px;
  padding: 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  border: 1px solid rgba(37, 99, 235, 0.18);
}

.hero-copy h1 {
  margin: 0 0 12px;
  font-size: 32px;
  font-weight: 800;
  color: #0f172a;
}

.hero-copy p {
  margin: 0 0 24px;
  color: #475569;
  line-height: 1.6;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #fff;
  border-radius: 14px;
  padding: 12px 16px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12);
}

.search-box input {
  border: none;
  outline: none;
  width: 100%;
  font-size: 15px;
  color: #1f2937;
}

.hero-illustration {
  font-size: 56px;
}

.quick-links header h2,
.section-card header h2,
.faq-section header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 800;
  color: #0f172a;
}

.quick-links header p,
.section-card header p {
  margin: 6px 0 0;
  color: #475569;
}

.link-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.link-card {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 12px;
  align-items: center;
  padding: 16px;
  background: #fff;
  border: 1px solid rgba(148, 163, 184, 0.3);
  border-radius: 16px;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
  cursor: pointer;
  transition: transform .2s ease, box-shadow .2s ease;
}

.link-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.12);
}

.link-icon {
  font-size: 28px;
}

.link-body h3 {
  margin: 0 0 6px;
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.link-body p {
  margin: 0;
  color: #475569;
  font-size: 0.9rem;
}

.section-card {
  background: #fff;
  border-radius: 22px;
  padding: 24px;
  border: 1px solid rgba(148, 163, 184, 0.25);
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
  display: grid;
  gap: 18px;
}

.article-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.article-card {
  padding: 16px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(248, 250, 252, 0.9), rgba(226, 232, 240, 0.72));
  border: 1px solid rgba(148, 163, 184, 0.2);
  display: grid;
  gap: 8px;
}

.article-card h3 {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: #1f2937;
}

.article-card p {
  margin: 0;
  color: #475569;
  line-height: 1.5;
}

.faq-section {
  background: #fff;
  border-radius: 22px;
  padding: 24px;
  border: 1px solid rgba(148, 163, 184, 0.25);
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
}

.faq-list {
  display: grid;
  gap: 12px;
  margin-top: 16px;
}

.faq-list details {
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 14px;
  padding: 14px 16px;
  background: #f8fafc;
}

.faq-list summary {
  font-weight: 700;
  cursor: pointer;
  color: #0f172a;
  list-style: none;
}

.faq-list summary::-webkit-details-marker {
  display: none;
}

.faq-list summary::after {
  content: '+';
  float: right;
  font-weight: 700;
  color: #1d4ed8;
}

.faq-list details[open] summary::after {
  content: '−';
}

.faq-list p {
  margin: 12px 0 0;
  color: #475569;
  line-height: 1.6;
}

.cta {
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 64, 175, 0.85));
  border-radius: 22px;
  padding: 28px;
  color: #fff;
  display: flex;
  justify-content: center;
}

.cta-content {
  width: 100%;
  max-width: 680px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.cta-copy h3 {
  margin: 0 0 6px;
  font-size: 22px;
  font-weight: 800;
  color: #f8fafc;
}

.cta-copy p {
  margin: 0;
  color: rgba(226, 232, 240, 0.85);
}

.cta-email {
  margin: 4px 0 0;
  color: #e2e8f0;
  font-weight: 600;
}

.cta-email a {
  color: #93c5fd;
  text-decoration: none;
  margin-left: 6px;
  font-weight: 700;
}

.cta-button {
  padding: 12px 20px;
  border-radius: 999px;
  background: #f8fafc;
  color: #0f172a;
  border: none;
  font-weight: 700;
  cursor: pointer;
  transition: transform .2s ease, box-shadow .2s ease;
}

.cta-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 30px rgba(15, 23, 42, 0.26);
}

@media (max-width: 1024px) {
  .link-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .hero {
    flex-direction: column;
    text-align: center;
  }
  .hero-copy h1 {
    font-size: 28px;
  }
  .hero-illustration {
    font-size: 48px;
  }
  .link-grid {
    grid-template-columns: 1fr;
  }
  .cta-content {
    flex-direction: column;
    text-align: center;
  }
}
</style>
