<template>
  <div class="page bug-report">
    <section class="hero">
      <div class="hero-icon" aria-hidden="true">🐞</div>
      <div class="hero-copy">
        <h1>{{ t('bugReport.heroTitle') }}</h1>
        <p>{{ t('bugReport.heroSubtitle') }}</p>
      </div>
    </section>

    <section class="form-card">
      <form class="report-form" @submit.prevent="submit">
        <label>
          {{ t('bugReport.form.summary') }}
          <input v-model="summary" type="text" required :placeholder="t('bugReport.placeholders.summary')" />
        </label>
        <label>
          {{ t('bugReport.form.environment') }}
          <input v-model="environment" type="text" :placeholder="t('bugReport.placeholders.environment')" />
        </label>
        <label>
          {{ t('bugReport.form.steps') }}
          <textarea v-model="steps" rows="4" required :placeholder="t('bugReport.placeholders.steps')"></textarea>
        </label>
        <label>
          {{ t('bugReport.form.expected') }}
          <textarea v-model="expected" rows="3" :placeholder="t('bugReport.placeholders.expected')"></textarea>
        </label>
        <label>
          {{ t('bugReport.form.actual') }}
          <textarea v-model="actual" rows="3" :placeholder="t('bugReport.placeholders.actual')"></textarea>
        </label>
        <label>
          {{ t('bugReport.form.contact') }}
          <input v-model="contact" type="email" :placeholder="t('bugReport.placeholders.contact')" />
        </label>
        <div class="actions">
          <button type="submit" :disabled="submitting">
            <span v-if="submitting">{{ t('bugReport.sending') }}</span>
            <span v-else>{{ t('bugReport.submit') }}</span>
          </button>
          <p v-if="feedback" :class="['feedback', feedbackType]">{{ feedback }}</p>
        </div>
      </form>
      <aside class="tips">
        <h3>{{ t('bugReport.tips.title') }}</h3>
        <ul>
          <li v-for="tip in tips" :key="tip">{{ tip }}</li>
        </ul>
      </aside>
    </section>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t, tm } = useI18n()

const tips = computed(() => {
  const value = tm('bugReport.tips.items')
  return Array.isArray(value) ? value : []
})

const summary = ref('')
const environment = ref('')
const steps = ref('')
const expected = ref('')
const actual = ref('')
const contact = ref('')
const submitting = ref(false)
const feedback = ref('')
const feedbackType = ref('success')

function submit() {
  submitting.value = true
  feedback.value = ''
  feedbackType.value = 'success'
  try {
    const subject = encodeURIComponent(`Bug Report: ${summary.value}`)
    const body = encodeURIComponent([
      `Environment: ${environment.value}`,
      '',
      'Steps to reproduce:',
      steps.value,
      '',
      'Expected result:',
      expected.value,
      '',
      'Actual result:',
      actual.value,
      '',
      `Reporter: ${contact.value || '—'}`,
    ].join('\n'))
    window.open(`mailto:support@docuiq.ai?subject=${subject}&body=${body}`, '_blank')
    feedback.value = t('bugReport.success')
    feedbackType.value = 'success'
    summary.value = ''
    environment.value = ''
    steps.value = ''
    expected.value = ''
    actual.value = ''
    contact.value = ''
  } catch (error) {
    feedback.value = t('bugReport.error')
    feedbackType.value = 'error'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.bug-report {
  display: grid;
  gap: 24px;
  padding-bottom: 48px;
}

.hero {
  display: flex;
  gap: 24px;
  align-items: center;
  background: linear-gradient(135deg, rgba(220, 38, 38, 0.12), rgba(234, 179, 8, 0.12));
  border: 1px solid rgba(220, 38, 38, 0.22);
  border-radius: 24px;
  padding: 28px;
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

.form-card {
  display: grid;
  gap: 24px;
  grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
}

.report-form {
  background: #fff;
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 22px;
  padding: 24px;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.08);
  display: grid;
  gap: 16px;
}

.report-form label {
  display: grid;
  gap: 8px;
  font-weight: 600;
  color: #0f172a;
}

.report-form input,
.report-form textarea {
  border: 1px solid rgba(148, 163, 184, 0.35);
  border-radius: 12px;
  padding: 10px 12px;
  font-size: 15px;
  color: #1f2937;
  background: #f8fafc;
  transition: border .2s ease, box-shadow .2s ease;
}

.report-form input:focus,
.report-form textarea:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
  background: #fff;
}

.actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.actions button {
  padding: 11px 20px;
  border-radius: 999px;
  border: none;
  background: #2563eb;
  color: #fff;
  font-weight: 700;
  cursor: pointer;
  transition: transform .2s ease, box-shadow .2s ease;
}

.actions button:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 32px rgba(37, 99, 235, 0.25);
}

.actions button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}

.feedback {
  margin: 0;
  font-size: 0.9rem;
}

.feedback.success {
  color: #15803d;
}

.feedback.error {
  color: #dc2626;
}

.tips {
  background: #fff;
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 22px;
  padding: 24px;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.06);
}

.tips h3 {
  margin: 0 0 10px;
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.tips ul {
  margin: 0;
  padding-left: 18px;
  color: #475569;
  line-height: 1.6;
}

@media (max-width: 900px) {
  .form-card {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 680px) {
  .hero {
    flex-direction: column;
    text-align: center;
  }
  .actions {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
