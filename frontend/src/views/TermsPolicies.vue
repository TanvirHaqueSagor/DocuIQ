<template>
  <div class="page terms-policies">
    <section class="hero">
      <div class="hero-icon" aria-hidden="true">📜</div>
      <div class="hero-copy">
        <h1>{{ t('termsPolicies.heroTitle') }}</h1>
        <p>{{ t('termsPolicies.heroSubtitle') }}</p>
      </div>
      <div class="hero-meta">{{ t('termsPolicies.lastUpdated') }}</div>
    </section>

    <section class="content">
      <article v-for="section in sections" :key="section.title" class="content-block">
        <h2>{{ section.title }}</h2>
        <p v-if="section.description">{{ section.description }}</p>
        <ul v-if="section.points">
          <li v-for="point in section.points" :key="point">{{ point }}</li>
        </ul>
        <div v-if="section.items" class="two-column">
          <div v-for="item in section.items" :key="item.title" class="item">
            <h3>{{ item.title }}</h3>
            <p>{{ item.body }}</p>
          </div>
        </div>
      </article>
    </section>

    <section class="cta">
      <div class="cta-body">
        <h3>{{ t('termsPolicies.questionsTitle') }}</h3>
        <p>{{ t('termsPolicies.questionsSubtitle') }}</p>
        <a class="cta-link" href="mailto:legal@docuiq.ai">legal@docuiq.ai</a>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t, tm } = useI18n()

const sections = computed(() => {
  const value = tm('termsPolicies.sections')
  return Array.isArray(value) ? value : []
})
</script>

<style scoped>
.terms-policies {
  display: grid;
  gap: 24px;
  padding-bottom: 48px;
}

.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 28px;
  border-radius: 24px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.12), rgba(14, 165, 233, 0.12));
  border: 1px solid rgba(59, 130, 246, 0.25);
}

.hero-icon {
  font-size: 48px;
}

.hero-copy h1 {
  margin: 0 0 10px;
  font-size: 30px;
  font-weight: 800;
  color: #0f172a;
}

.hero-copy p {
  margin: 0;
  color: #475569;
  line-height: 1.6;
}

.hero-meta {
  font-weight: 600;
  color: #2563eb;
}

.content {
  display: grid;
  gap: 24px;
}

.content-block {
  background: #fff;
  border-radius: 20px;
  padding: 24px;
  border: 1px solid rgba(148, 163, 184, 0.25);
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.08);
  display: grid;
  gap: 12px;
}

.content-block h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 800;
  color: #0f172a;
}

.content-block p {
  margin: 0;
  color: #475569;
  line-height: 1.6;
}

.content-block ul {
  margin: 0;
  padding-left: 20px;
  color: #475569;
  line-height: 1.6;
}

.two-column {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.item h3 {
  margin: 0 0 6px;
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.item p {
  margin: 0;
  color: #475569;
}

.cta {
  background: linear-gradient(120deg, rgba(15, 23, 42, 0.92), rgba(30, 64, 175, 0.8));
  border-radius: 20px;
  padding: 28px;
  color: #fff;
}

.cta-body {
  display: grid;
  gap: 6px;
  text-align: center;
}

.cta-body h3 {
  margin: 0;
  font-size: 22px;
  font-weight: 800;
}

.cta-body p {
  margin: 0;
  color: rgba(226, 232, 240, 0.85);
}

.cta-link {
  color: #facc15;
  font-weight: 700;
  text-decoration: none;
}

@media (max-width: 768px) {
  .hero {
    flex-direction: column;
    text-align: center;
  }
}
</style>
