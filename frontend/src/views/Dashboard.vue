# =============================
# src/views/Dashboard.vue
# =============================
<template>
  <div class="page">
    <header class="page-head">
      <div class="left">
        <h1>Dashboard</h1>
      </div>
      <div class="right">
        <RouterLink class="primary" to="/documents">Upload Documents</RouterLink>
      </div>
    </header>

    <section class="grid stats-grid">
      <StatsCard icon="📄" title="Total Documents" :value="summary.total_documents" :delta="summary.delta_documents" />
      <StatsCard icon="🔎" title="Queries (7d)" :value="summary.queries_last_7d" :delta="summary.delta_queries" />
      <StatsCard icon="⏱️" title="Avg. Answer Time" :value="summary.avg_answer_time_ms ? (summary.avg_answer_time_ms/1000).toFixed(2) + 's' : '—'" :delta="summary.delta_answer_time" :isGoodDown="true" />
      <StatsCard icon="✅" title="Answer Confidence" :value="summary.answer_confidence ? summary.answer_confidence + '%' : '—'" :delta="summary.delta_confidence" />
    </section>

    <section class="grid two-col">
      <article class="card glass">
        <header class="card-title">📈 Usage (Last 14 days)</header>
        <UsageSparkline :series="usageSeries" :labels="usageLabels"/>
      </article>

      <article class="card glass">
        <header class="card-title">⚡ Quick Actions</header>
        <QuickActions @upload="goUpload" @newSearch="goSearch" @addDoc="goUpload" />
      </article>
    </section>

    <section class="grid single">
      <article class="card glass">
        <header class="card-title">🗂️ Recent Documents</header>
        <RecentDocumentsTable :rows="recentDocs" @view="openDoc" @delete="deleteDoc" />
      </article>
    </section>
  </div>
 </template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import StatsCard from '../components/dashboard/StatsCard.vue'
import UsageSparkline from '../components/dashboard/UsageSparkline.vue'
import RecentDocumentsTable from '../components/dashboard/RecentDocumentsTable.vue'
import QuickActions from '../components/dashboard/QuickActions.vue'
import { fetchDashboardSummary, fetchUsage, fetchRecentDocuments, deleteDocument } from '../services/dashboard'

const router = useRouter()

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

const usageSeries = ref([])
const usageLabels = ref([])
const recentDocs = ref([])

onMounted(async () => {
  try { summary.value = await fetchDashboardSummary() } catch {}

  try {
    const usage = await fetchUsage(14)
    usageSeries.value = usage.map(d => d.count)
    usageLabels.value = usage.map(d => d.date)
  } catch {}

  try { recentDocs.value = await fetchRecentDocuments(8) } catch {}
})

function goUpload(){ router.push('/documents') }
function goSearch(){ router.push('/') }
function openDoc(row){ router.push(`/documents/${row.id}`) }
async function deleteDoc(row){
  if(!confirm(`Delete “${row.title}”? This cannot be undone.`)) return
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
.primary{ border:none; background:#1f47c5; color:#fff; font-weight:800; border-radius:10px; padding:9px 12px; cursor:pointer; text-decoration:none; }
.ghost{ border:1px solid #dbe3f3; background:#fff; color:#1f47c5; border-radius:10px; padding:8px 10px; font-weight:800; cursor:pointer; text-decoration:none; }

.grid{ display:grid; gap:12px; }
.stats-grid{ grid-template-columns: repeat(4, minmax(0,1fr)); }
.two-col{ grid-template-columns: 2fr 1fr; }
.single{ grid-template-columns: 1fr; }

.card{ background:#fff; border:1px solid #e8eef8; border-radius:12px; padding:12px; box-shadow: var(--md-shadow-1); color:#1f2a44; }
.card-title{ font-weight:900; color:#1f2a44; margin-bottom:10px; display:flex; align-items:center; gap:8px; }
.card-title::before{ content:""; width:8px; height:8px; border-radius:999px; background:#1f47c5; box-shadow:0 0 0 3px rgba(31,71,197,.12); }

@media (max-width:1024px){
  .stats-grid{ grid-template-columns:repeat(2, minmax(0,1fr)); }
  .two-col{ grid-template-columns:1fr; }
}
@media (max-width:640px){
  .stats-grid{ grid-template-columns:1fr; }
}
</style>
