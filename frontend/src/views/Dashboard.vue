# =============================
# src/views/Dashboard.vue
# =============================
<template>
  <div class="page">
    <header class="page-head">
      <div class="left">
        <h1>{{ t('dashboard') }}</h1>
      </div>
      <div class="right">
        <RouterLink class="primary" to="/documents">{{ t('uploadDocuments') }}</RouterLink>
      </div>
    </header>

    <section class="grid stats-grid">
      <StatsCard icon="📄" :title="t('dashboardTotalDocuments')" :value="summary.total_documents" :delta="summary.delta_documents" />
      <StatsCard icon="🔎" :title="t('dashboardQueries7d')" :value="summary.queries_last_7d" :delta="summary.delta_queries" />
      <StatsCard icon="⏱️" :title="t('dashboardAvgAnswerTime')" :value="summary.avg_answer_time_ms ? (summary.avg_answer_time_ms/1000).toFixed(2) + 's' : '—'" :delta="summary.delta_answer_time" :isGoodDown="true" />
      <StatsCard icon="✅" :title="t('dashboardAnswerConfidence')" :value="summary.answer_confidence ? summary.answer_confidence + '%' : '—'" :delta="summary.delta_confidence" />
    </section>

    <section class="grid single">
      <article class="card glass">
        <header class="card-title">📈 {{ t('usageActivitySpan', { days: USAGE_WINDOW_DAYS }) }}</header>
        <UsageSparkline :series="usageSeries" :labels="usageLabels"/>
      </article>
    </section>

    <section class="grid single">
      <article class="card glass">
        <header class="card-title">🗂️ {{ t('recentDocumentsTitle') }}</header>
        <RecentDocumentsTable :rows="recentDocs" @view="openDoc" @delete="deleteDoc" />
      </article>
    </section>
  </div>
 </template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import StatsCard from '../components/dashboard/StatsCard.vue'
import UsageSparkline from '../components/dashboard/UsageSparkline.vue'
import RecentDocumentsTable from '../components/dashboard/RecentDocumentsTable.vue'
import { fetchDashboardSummary, fetchUsage, fetchRecentDocuments, deleteDocument } from '../services/dashboard'

const router = useRouter()
const { t } = useI18n()

const summary = ref({
  total_documents: 0,
  delta_documents: 0,
  queries_last_7d: 0,
  delta_queries: 0,
  avg_answer_time_ms: 0,
  delta_answer_time: 0,
  answer_confidence: 0,
  delta_confidence: 0,
})

const USAGE_WINDOW_DAYS = 30
const usageSeries = ref([])
const usageLabels = ref([])
const recentDocs = ref([])

onMounted(async () => {
  try { summary.value = await fetchDashboardSummary() } catch {}

  try {
    const usage = await fetchUsage(USAGE_WINDOW_DAYS)
    usageSeries.value = usage.map(d => d.count)
    usageLabels.value = usage.map(d => d.date)
  } catch {}

  try { recentDocs.value = await fetchRecentDocuments(8) } catch {}
})

function openDoc(row){ router.push(`/documents/${row.id}`) }
async function deleteDoc(row){
  if(!confirm(t('confirmDeleteDoc', { name: row.title ?? '' }))) return
  await deleteDocument(row.id)
  recentDocs.value = recentDocs.value.filter(r => r.id !== row.id)
}
</script>

<style scoped>
:root{
  --bg:#f6f8ff; --card:#ffffff; --line:#e6ecf7; --txt:#25324a; --muted:#6e7b90; --blue:#1d4ed8;
  --md-shadow-1: 0 1px 3px rgba(16,24,40,.08), 0 1px 2px rgba(16,24,40,.06);
  --md-shadow-2: 0 2px 6px rgba(16,24,40,.10), 0 4px 12px rgba(16,24,40,.08);
}
.page{ background:var(--bg); min-height:100vh; padding: 0 12px; display:grid; gap:12px; }
.page-head{ width:100%; margin:16px 0 10px; display:flex; align-items:center; justify-content:space-between; gap:12px; }
.page-head h1{ margin:0; font-size:22px; color:var(--txt); font-weight:800; letter-spacing:.2px; }
.left{ display:flex; align-items:center; gap:12px; }
.right{ display:flex; gap:8px; }
.primary{ border:none; background:var(--blue); color:#fff; font-weight:800; border-radius:10px; padding:9px 12px; cursor:pointer; text-decoration:none; }
.ghost{ border:1px solid var(--line); background:var(--card); color:var(--blue); border-radius:10px; padding:8px 10px; font-weight:800; cursor:pointer; text-decoration:none; }

.grid{ display:grid; gap:12px; }
.stats-grid{ grid-template-columns: repeat(4, minmax(0,1fr)); }
.single{ grid-template-columns: 1fr; }

.card{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:12px; box-shadow: var(--md-shadow-1); color:var(--txt); }
.card-title{ font-weight:900; color:var(--txt); margin-bottom:10px; display:flex; align-items:center; gap:8px; }
.card-title::before{ content:""; width:8px; height:8px; border-radius:999px; background:#1f47c5; box-shadow:0 0 0 3px rgba(31,71,197,.12); }

@media (max-width:1024px){
  .stats-grid{ grid-template-columns:repeat(2, minmax(0,1fr)); }
}
@media (max-width:640px){
  .stats-grid{ grid-template-columns:1fr; }
}
</style>
