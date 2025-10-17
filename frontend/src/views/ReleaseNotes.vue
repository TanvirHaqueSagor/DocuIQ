<template>
  <div class="page release-notes">
    <section class="hero">
      <div class="hero-icon" aria-hidden="true">🗒️</div>
      <div class="hero-copy">
        <h1>{{ t('releaseNotes.heroTitle') }}</h1>
        <p>{{ t('releaseNotes.heroSubtitle') }}</p>
      </div>
      <div class="hero-meta">
        <span>{{ t('releaseNotes.lastUpdated') }}</span>
      </div>
    </section>

    <section class="timeline">
      <article v-for="entry in entries" :key="entry.version" class="timeline-item">
        <div class="timeline-marker"></div>
        <div class="timeline-card">
          <header>
            <div class="version">{{ entry.version }}</div>
            <div class="date">{{ entry.date }}</div>
          </header>
          <div class="highlights" v-if="entry.highlights && entry.highlights.length">
            <h3>{{ t('releaseNotes.highlightsTitle') }}</h3>
            <ul>
              <li v-for="highlight in entry.highlights" :key="highlight">{{ highlight }}</li>
            </ul>
          </div>
          <div class="changes" v-if="entry.changes && entry.changes.length">
            <h4>{{ t('releaseNotes.changesTitle') }}</h4>
            <ul>
              <li v-for="change in entry.changes" :key="change">{{ change }}</li>
            </ul>
          </div>
          <footer v-if="entry.links && entry.links.length" class="links">
            <a v-for="link in entry.links" :key="link.href" :href="link.href" target="_blank" rel="noreferrer">
              {{ link.label }}
            </a>
          </footer>
        </div>
      </article>
    </section>

    <section class="up-next" v-if="upNext && upNext.length">
      <h2>{{ t('releaseNotes.upNextTitle') }}</h2>
      <ul>
        <li v-for="item in upNext" :key="item">{{ item }}</li>
      </ul>
      <p class="feedback">
        {{ t('releaseNotes.feedbackPrompt') }}
        <a href="mailto:feedback@docuiq.ai">feedback@docuiq.ai</a>
      </p>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t, tm } = useI18n()

const entries = computed(() => {
  const value = tm('releaseNotes.entries')
  return Array.isArray(value) ? value : []
})

const upNext = computed(() => {
  const value = tm('releaseNotes.upNext')
  return Array.isArray(value) ? value : []
})
</script>

<style scoped>
.release-notes {
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
  background: linear-gradient(120deg, rgba(15, 118, 110, 0.12), rgba(59, 130, 246, 0.12));
  border: 1px solid rgba(59, 130, 246, 0.2);
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

.hero-meta span {
  font-size: 0.9rem;
  color: #1d4ed8;
  font-weight: 600;
}

.timeline {
  position: relative;
  padding-left: 20px;
  display: grid;
  gap: 24px;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 8px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: rgba(148, 163, 184, 0.4);
}

.timeline-item {
  display: flex;
  gap: 16px;
  position: relative;
}

.timeline-marker {
  position: absolute;
  left: -4px;
  top: 18px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #2563eb;
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.15);
}

.timeline-card {
  margin-left: 20px;
  width: 100%;
  background: #fff;
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 18px;
  padding: 20px;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.08);
  display: grid;
  gap: 16px;
}

.timeline-card header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.timeline-card .version {
  font-size: 20px;
  font-weight: 800;
  color: #0f172a;
}

.timeline-card .date {
  color: #475569;
  font-size: 0.9rem;
}

.timeline-card h3,
.timeline-card h4 {
  margin: 0 0 6px;
  color: #0f172a;
  font-weight: 700;
}

.timeline-card ul {
  margin: 0;
  padding-left: 20px;
  color: #475569;
  line-height: 1.6;
}

.links {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.links a {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.08);
  color: #1d4ed8;
  text-decoration: none;
  font-weight: 600;
}

.up-next {
  background: #fff;
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.08);
  display: grid;
  gap: 12px;
}

.up-next h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 800;
  color: #0f172a;
}

.up-next ul {
  margin: 0;
  padding-left: 20px;
  color: #475569;
  line-height: 1.6;
}

.feedback {
  margin: 0;
  color: #475569;
}

.feedback a {
  color: #1d4ed8;
  font-weight: 600;
  text-decoration: none;
}

@media (max-width: 768px) {
  .hero {
    flex-direction: column;
    text-align: center;
  }
  .timeline {
    padding-left: 0;
  }
  .timeline::before {
    left: 50%;
  }
  .timeline-item {
    flex-direction: column;
    align-items: center;
  }
  .timeline-marker {
    display: none;
  }
  .timeline-card {
    margin-left: 0;
  }
}
</style>
