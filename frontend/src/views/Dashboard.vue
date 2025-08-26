# =============================
# src/views/Dashboard.vue
# =============================
<template>
  <div class="dashboard">
    <header class="dash-header">
        <div class="title-wrap">
            <h1>Dashboard</h1>
            <p class="subtitle">Your document intelligence at a glance</p>
        </div>
        <div class="header-actions">
            <RouterLink class="btn primary" to="/documents?upload=1">Upload Document</RouterLink>
            <RouterLink class="btn ghost" to="/search">Search</RouterLink>
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
import StatsCard from '@/components/dashboard/StatsCard.vue'
import UsageSparkline from '@/components/dashboard/UsageSparkline.vue'
import RecentDocumentsTable from '@/components/dashboard/RecentDocumentsTable.vue'
import QuickActions from '@/components/dashboard/QuickActions.vue'
import { fetchDashboardSummary, fetchUsage, fetchRecentDocuments, deleteDocument } from '@/services/dashboard'

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

function goUpload(){ router.push('/documents?upload=1') }
function goSearch(){ router.push('/search') }
function openDoc(row){ router.push(`/documents/${row.id}`) }
async function deleteDoc(row){
  if(!confirm(`Delete “${row.title}”? This cannot be undone.`)) return
  await deleteDocument(row.id)
  recentDocs.value = recentDocs.value.filter(r => r.id !== row.id)
}
</script>

<style scoped>
:root{ --bg:#0b1020; --panel:#0f1529; --muted:#98a2b3; --txt:#e6eaf2; --brand:#7c5cff; --brand-2:#22d3ee; }
@media (prefers-color-scheme: light){
  :root{ --bg:#f6f8fc; --panel:#ffffff; --muted:#667085; --txt:#0f172a; --brand:#5b67ff; --brand-2:#06b6d4; }
}

.dashboard{
  display:grid; gap:20px;
  background:linear-gradient(180deg, rgba(124,92,255,.08), rgba(34,211,238,.06) 40%, transparent 80%);
  padding:8px; border-radius:20px;
}

.dash-header{
  display:flex; align-items:flex-end; justify-content:space-between;
  padding:18px 20px; background:var(--panel);
  border:1px solid rgba(124,92,255,.18); border-radius:16px;
  position:relative; overflow:hidden;
}
.dash-header::after{
  content:""; position:absolute; right:-60px; top:-60px; width:160px; height:160px;
  background: radial-gradient(closest-side, rgba(124,92,255,.35), transparent);
  filter: blur(8px);
}
.title-wrap h1{ font-size:22px; color:var(--txt); margin:0; }
.subtitle{ margin:6px 0 0; color:var(--muted); font-size:13px; }
.header-actions{ display:flex; gap:10px; }

.btn{
  border:1px solid rgba(255,255,255,.14);
  padding:10px 14px; border-radius:10px; text-decoration:none; color:var(--txt);
  background:linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
  backdrop-filter: blur(6px);
  transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease;
  box-shadow: 0 4px 14px rgba(16,24,40,.06);
}
.btn:hover{ transform: translateY(-1px); box-shadow:0 8px 24px rgba(16,24,40,.12); }
.btn.primary{ background:linear-gradient(90deg, var(--brand), var(--brand-2)); border-color:transparent; color:white; }
.btn.ghost{ background:transparent; border-color: rgba(124,92,255,.35); }

.grid{ display:grid; gap:16px; }
.stats-grid{ grid-template-columns: repeat(4, minmax(0,1fr)); }
.two-col{ grid-template-columns: 2fr 1fr; }
.single{ grid-template-columns: 1fr; }

.card{
  background:var(--panel); border:1px solid rgba(124,92,255,.18);
  border-radius:16px; padding:16px; box-shadow:0 2px 18px rgba(2,6,23,0.18); color:var(--txt);
}
.card-title{
  font-weight:700; color:var(--txt); margin-bottom:12px; display:flex; align-items:center; gap:8px;
}
.card-title::before{
  content:""; width:8px; height:8px; border-radius:999px;
  background:linear-gradient(90deg, var(--brand), var(--brand-2));
  box-shadow:0 0 0 3px rgba(124,92,255,.15);
}

@media (max-width:1024px){
  .stats-grid{ grid-template-columns:repeat(2, minmax(0,1fr)); }
  .two-col{ grid-template-columns:1fr; }
}
@media (max-width:640px){
  .stats-grid{ grid-template-columns:1fr; }
}
</style>
