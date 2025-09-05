<template>
  <div class="page">
    <!-- Page Header (no brand duplicate) -->
    <header class="page-head">
      <div class="left">
        <h1>{{ $t ? $t('documents') : 'Documents' }}</h1>
        <div class="search">
          <input
            v-model="q"
            type="text"
            :placeholder="$t ? $t('search') : 'Search jobs, titles…'"
            @keydown.enter.prevent="applySearch"
            aria-label="Search"
          />
          <button class="icon" @click="applySearch" aria-label="Search">🔎</button>
        </div>
      </div>
      <div class="right">
        <button class="ghost" @click="refreshAll" :title="$t ? $t('refresh') : 'Refresh'">⟳</button>
      </div>
    </header>

    <!-- Drag & Drop hero (click opens file picker) -->
    <section
      class="dropzone"
      :class="{ over: isOver }"
      @dragover.prevent="onDragOver"
      @dragleave.prevent="onDragLeave"
      @drop.prevent="onDrop"
      @click="goFiles"
    >
      
      <div class="dz-inner">
        <div class="cloud" aria-hidden="true">☁️</div>
        <div class="dz-title">{{ $t ? $t('dropFiles') : 'Drag & drop files here or click to upload' }}</div>
        <div class="dz-sub">{{ $t ? $t('dropHint') : 'PDF, DOCX, PPTX, XLSX, HTML, images, media' }}</div>
      </div>
    </section>

    <!-- Main content grid -->
    <div class="grid">
      <!-- Left: Imports / Documents -->
      <section class="panel">
        <!-- Unified list: Imports + Documents -->
        <div class="table-wrap">
          <div class="table-tools">
            <label class="chk">
              <input type="checkbox" v-model="autoRefresh" />
              <span>{{ $t ? $t('autoRefresh') : 'Auto refresh' }}</span>
            </label>
          </div>
          <div class="info-line">{{ $t ? $t('docsInfo') : 'Data from uploads and connected sources is indexed into your vector database. Use Re-run Import to refresh vectors.' }}</div>
          <table class="tbl" role="table">
            <thead>
              <tr>
                <th>{{ $t ? $t('type') : 'Type' }}</th>
                <th>{{ $t ? $t('title') : 'Title' }}</th>
                <th>{{ $t ? $t('status') : 'Status' }}</th>
                <th>{{ $t ? $t('imported') : 'Imported' }}</th>
                <th>{{ $t ? $t('actions') : 'Actions' }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in filteredCombined" :key="row.id">
                <td class="type-cell">
                  <span class="type-ico"><img class="src-ico-img" :src="rowIconComp(row)" :alt="rowType(row)" /></span>
                  <span>{{ rowType(row) }}</span>
                </td>
                <td class="truncate">{{ row.title }}</td>
                <td>
                  <span class="badge" :class="badgeClass(row)">
                    <template v-if="isRowRunning(row)">
                      {{ $t ? $t('running') : 'running' }}<span class="dots" aria-hidden="true"><span>.</span><span>.</span><span>.</span></span>
                    </template>
                    <template v-else>{{ displayStatus(row) }}</template>
                  </span>
                </td>
                <td>{{ fmtDate(row.created_at) }}</td>
                <td>
                  <template v-if="row.type==='doc'">
                    <div class="row-actions">
                      <button class="link icon-btn" @click="editRow(row)" :title="$t ? $t('edit') : 'Edit'" aria-label="Edit">
                        <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25ZM20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83Z"/></svg>
                      </button>
                      <button class="link icon-btn" @click="rerunImport(row)" :disabled="isRowRunning(row) || isRowDeleting(row)" :title="$t ? $t('rerunImport') : 'Re-run Import'" aria-label="Re-run Import">
                        <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 5a7 7 0 1 1-6.9 8.2h2.1A5 5 0 1 0 12 7V3l5 4-5 4V9a3 3 0 1 1-3 3H5A7 7 0 0 1 12 5Z"/></svg>
                      </button>
                      <button class="link danger icon-btn" @click="deleteDoc(row)" :disabled="isRowRunning(row) || isRowDeleting(row)" :title="$t ? $t('delete') : 'Delete'" aria-label="Delete">
                        <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M9 3h6l1 2h4v2H4V5h4l1-2Zm-3 6h12l-1 10a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L6 9Zm5 2v8h2v-8h-2Z"/></svg>
                      </button>
                    </div>
                  </template>
                  <template v-else>
                    <div class="row-actions">
                      <button class="link icon-btn" @click="editRow(row)" :title="$t ? $t('edit') : 'Edit'" aria-label="Edit">
                        <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25ZM20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83Z"/></svg>
                      </button>
                      <button class="link icon-btn" @click="rerunImport(row)" :disabled="isRowRunning(row) || isRowDeleting(row)" :title="$t ? $t('rerunImport') : 'Re-run Import'" aria-label="Re-run Import">
                        <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 5a7 7 0 1 1-6.9 8.2h2.1A5 5 0 1 0 12 7V3l5 4-5 4V9a3 3 0 1 1-3 3H5A7 7 0 0 1 12 5Z"/></svg>
                      </button>
                      <button class="link danger icon-btn" @click="deleteJob(row)" :disabled="isRowRunning(row) || isRowDeleting(row)" :title="$t ? $t('delete') : 'Delete'" aria-label="Delete">
                        <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M9 3h6l1 2h4v2H4V5h4l1-2Zm-3 6h12l-1 10a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L6 9Zm5 2v8h2v-8h-2Z"/></svg>
                      </button>
                    </div>
                  </template>
                </td>
              </tr>
              <tr v-if="!filteredCombined.length">
                <td colspan="5" class="empty">{{ $t ? $t('noItems') : 'No items yet' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Right: KPIs + Connected Sources (no floating mini) -->
      <aside class="side">
        <div class="kpis">
          <div class="kpi">
            <div class="kpi-title">{{ $t ? $t('documents') : 'Documents' }}</div>
            <div class="kpi-val">{{ kpi.documents }}</div>
          </div>
          <div class="kpi">
            <div class="kpi-title">{{ $t ? $t('runningJobs') : 'Running jobs' }}</div>
            <div class="kpi-val">{{ kpi.running }}</div>
          </div>
          <div class="kpi">
            <div class="kpi-title">{{ $t ? $t('server') : 'Server' }}</div>
            <div class="kpi-val" :class="kpi.health ? 'ok' : 'bad'">{{ kpi.health ? 'OK' : 'Down' }}</div>
          </div>
        </div>

          <div class="sources">
          <div class="sources-head">
            <h3>{{ $t ? $t('sources') : 'Sources' }}</h3>
          </div>

          <div class="src-grid">
            <button v-for="s in srcPalette" :key="s.key" class="src-btn" @click="openWizard(s.key)">
              <span class="src-ico-comp"><img class="src-ico-img" :src="iconForKind(s.key)" :alt="s.name" /></span>
              <div class="src-name">{{ s.name }}</div>
            </button>
          </div>

          <div class="connected" v-if="sources.length">
            <div class="conn-title">{{ $t ? $t('connected') : 'Connected' }}</div>
            <div class="conn-list">
              <div v-for="s in filteredSources" :key="s.id" class="conn-item">
                <div class="ci-left">
                  <span class="dot"></span>
                  <span class="src-ico-comp"><img class="src-ico-img" :src="iconForKind((s.kind||'').toLowerCase())" :alt="prettyKind(s.kind)" /></span>
                  <span class="nm">{{ s.name }}</span>
                  <span class="kind">· {{ prettyKind(s.kind) }}</span>
                </div>
                <div class="ci-actions">
                  <button class="link icon-btn" @click="runSource(s)" :title="$t ? $t('run') : 'Run'" aria-label="Run">
                    <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M8 5v14l11-7L8 5Z"/></svg>
                  </button>
                  <button class="link danger icon-btn" @click="deleteSource(s)" :disabled="isSourceDeleting(s)" :title="$t ? $t('delete') : 'Delete'" aria-label="Delete">
                    <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M9 3h6l1 2h4v2H4V5h4l1-2Zm-3 6h12l-1 10a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L6 9Zm5 2v8h2v-8h-2Z"/></svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>

    
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import { API_BASE_URL as API } from '../config'
// Icon components (via unplugin-icons)
import { authFetch } from '../lib/authFetch'

import icFile from '../assets/icons/file.svg'
import icWeb from '../assets/icons/web.svg'
import icS3 from '../assets/icons/S3.svg'
import icGdrive from '../assets/icons/gdrive.svg'
import icGmail from '../assets/icons/gmail.svg'
import icDropbox from '../assets/icons/dropbox.svg'
import icOnedrive from '../assets/icons/onedrive.svg'
import icBox from '../assets/icons/box.svg'
// Enterprise / productivity
import icSharepoint from '../assets/icons/sharePoint.svg'
import icConfluence from '../assets/icons/confluence.svg'
import icNotion from '../assets/icons/Notion.svg'
import icAirtable from '../assets/icons/airtable.svg'
// Comms
import icOutlook from '../assets/icons/outlook.svg'
import icSlack from '../assets/icons/slack.svg'
import icTeams from '../assets/icons/teams.svg'
import icZoom from '../assets/icons/zoom.svg'
// Dev/Project
import icGithub from '../assets/icons/github.svg'
import icGitlab from '../assets/icons/gitlab.svg'
import icJira from '../assets/icons/jira.svg'
import icTrello from '../assets/icons/trello.svg'
// Databases/BI/Search
import icPostgres from '../assets/icons/postgresql.svg'
import icMysql from '../assets/icons/mysql.svg'
import icMongodb from '../assets/icons/mongodb.svg'
import icSnowflake from '../assets/icons/snowflake.svg'
import icBigQuery from '../assets/icons/bigquery.svg'
import icElasticsearch from '../assets/icons/elasticsearch.svg'
// Feeds/APIs
import icRss from '../assets/icons/rss.svg'
import icApi from '../assets/icons/api.svg'
import icBloomberg from '../assets/icons/blloomberg.svg'
import icRefinitiv from '../assets/icons/Refintiv.svg'
import icEsg from '../assets/icons/esg.svg'
// Social/Calendar/Design
import icLinkedIn from '../assets/icons/linkedin.svg'
import icTwitterX from '../assets/icons/x.svg'
import icGCal from '../assets/icons/google-calendar.svg'
import icFigma from '../assets/icons/figma.svg'
/* ----- state ----- */
const q = ref('')
const isOver = ref(false); let overTimer=null
const autoRefresh = ref(true)
const jobs = ref([]); const docs = ref([]); const sources = ref([])
const kpi = reactive({ documents: 0, running: 0, health: true })
const fileInput = ref(null)
// Track rows set to re-run; key by row.id
const rerunning = ref({})
// Track rows being deleted; key by row.id
const deletingRows = ref({})
// Track sources being deleted; key by source.id
const deletingSources = ref({})

/* ----- wizard ----- */
const wizard = reactive({ open:false, tab:'' })
// Replace modal with dedicated per-source setup pages
const openWizard = (t='gdrive') => { router.push(`/connect/${t}`) }

onMounted(async () => {
  try {
    ensureAuthOrRedirect()   // টোকেন না থাকলে এখানে থেমে /login এ যাবে
    // Seed search from query param (?q=...)
    try { q.value = String(route.query.q || '').trim() } catch (_) { /* ignore */ }
    await refreshAll()
    // Auto-refresh both jobs and documents so statuses update in UI
    poll = setInterval(() => { if (autoRefresh.value) refreshAll() }, 5000)
  } catch (e) {
    // redirected; কিছুই করার নেই
  }
})

/* ----- helpers ----- */
import { useRouter, useRoute } from 'vue-router'
const router = useRouter()
const route  = useRoute()
const { t } = useI18n ? useI18n() : { t: (s)=>s }
const goFiles = () => router.push('/connect/files')

const getAccessToken = () =>
  localStorage.getItem('token') || localStorage.getItem('access') || ''

// শুধুমাত্র টোকেন থাকলে হেডার দিন; না থাকলে খালি অবজেক্ট
const authHeaders = () => {
  const t = getAccessToken()
  // JWT হলে সাধারণত 2টা ডট থাকে (x.y.z) — ধরা সহজ
  return t && t.includes('.') ? { Authorization: `Bearer ${t}` } : {}
}

// টোকেন না থাকলে সাথে সাথে লগইনে পাঠান
const ensureAuthOrRedirect = () => {
  const t = getAccessToken()
  if (!t) {
    router.replace(`/login?redirect=${encodeURIComponent(route.fullPath)}`)
    throw new Error('Auth required')
  }
}
const fmtDate = (iso) => {
  try {
    return new Date(iso).toLocaleDateString()
  } catch {
    return iso ? String(iso).split('T')[0] : ''
  }
}
const prettyStatus = (s)=> s ? s[0].toUpperCase()+s.slice(1) : s
const prettyKind = (k)=> ({
  // Storage
  files:'File', upload:'File', file:'File', web:'Web', s3:'S3', gdrive:'Google Drive', dropbox:'Dropbox', onedrive:'OneDrive', box:'Box',
  // Enterprise
  sharepoint:'SharePoint', confluence:'Confluence', notion:'Notion', airtable:'Airtable',
  // Comms
  email:'Email', gmail:'Gmail', outlook:'Outlook', slack:'Slack', teams:'Teams', zoom:'Zoom',
  // Dev/Project
  github:'GitHub', gitlab:'GitLab', jira:'Jira', trello:'Trello',
  // Databases/BI/Search
  postgres:'PostgreSQL', mysql:'MySQL', mongodb:'MongoDB', snowflake:'Snowflake', bigquery:'BigQuery', elasticsearch:'Elasticsearch', db:'Database',
  // Feeds/APIs
  rss:'RSS', api:'API', bloomberg:'Bloomberg', refinitiv:'Refinitiv', esg:'ESG API',
  // Social/Calendar/Design
  linkedin:'LinkedIn', twitter:'Twitter (X)', gcal:'Google Calendar', figma:'Figma',
  media:'Media', video:'Video', audio:'Audio'
}[k] || (k ? k[0].toUpperCase()+k.slice(1) : ''))
const jobTitle = (j) => {
  const m=(j.mode||'').toUpperCase()
  if (j.mode==='upload') {
    const names = j.payload?.filenames || j.payload?.files
    if (Array.isArray(names) && names.length) {
      return names.length === 1 ? names[0] : `${names[0]} (+${names.length-1} more)`
    }
    return `${m} · ${(j.payload?.file_ids?.length||0)} files`
  }
  if (j.mode==='web') return `${m} · ${j.payload?.url||''}`
  if (j.mode==='s3')  return `${m} · ${j.payload?.bucket||''}/${j.payload?.prefix||''}`
  return m
}
// Deduplication key for jobs so re-run doesn't show duplicates
const stableStr = (obj) => {
  if (obj === null || obj === undefined) return ''
  if (typeof obj !== 'object') return String(obj)
  const keys = Object.keys(obj).sort()
  return keys.map(k => `${k}:${stableStr(obj[k])}`).join('|')
}
const jobKey = (j) => {
  const mode = String(j.mode||'').toLowerCase()
  if (mode === 'web') return `web|${j.payload?.url||''}`
  if (mode === 's3') return `s3|${j.payload?.bucket||''}|${j.payload?.prefix||''}`
  if (j.source) return `${mode}|src:${j.source}`
  return `${mode}|${stableStr(j.payload||{})}`
}
// Human-friendly type for unified list
const isWebDoc = (row) => {
  try { return !!(row?._raw?.steps_json && row._raw.steps_json.source_url) } catch { return false }
}
const rowType = (row) => {
  if (row?.type === 'job') {
    const k = String(row?._raw?.mode || '').toLowerCase()
    if (!k) return 'Import'
    return prettyKind(k)
  }
  // Documents: detect web-fetched items via steps_json.source_url
  if (isWebDoc(row)) return 'Web'
  // Default to File; we can refine by extension later
  return 'File'
}

// Map job statuses to friendly labels
const mapDocStatus = (s) => {
  const v = String(s || '').toUpperCase()
  if (['READY','PARTIAL_READY'].includes(v)) return 'Imported'
  if (['FAILED','CANCELLED','DELETED'].includes(v)) return 'Failed'
  if (['QUEUED','FETCHING','NORMALIZING','CHUNKING','EMBEDDING','INDEXING'].includes(v)) return 'Processing'
  return 'Uploaded'
}
const mapUnifiedStatus = (row) => {
  // Desired: Uploaded, Processing, Imported
  if (row?.type === 'job') {
    const v = String(row._raw?.status || '').toLowerCase()
    if (v === 'queued' || v === 'running') return 'Processing'
    if (v === 'success') return 'Imported'
    if (v === 'failed') return 'Failed'
    return 'Uploaded'
  }
  // Documents: use backend-provided status if present
  return mapDocStatus(row?._raw?.status)
}
const displayStatus = (row) => mapUnifiedStatus(row)
const statusClass = (row) => String(mapUnifiedStatus(row)).toLowerCase()
const isRowRunning = (row) => !!(rerunning.value || {})[row?.id]
const badgeClass = (row) => isRowRunning(row) ? 'processing' : statusClass(row)
const isRowDeleting = (row) => !!(deletingRows.value || {})[row?.id]
const isSourceDeleting = (s) => !!(deletingSources.value || {})[s?.id]
const fileEmoji = (name='')=>{
  const n=(name||'').toLowerCase()
  if(n.endsWith('.pdf')) return '📕'
  if(n.endsWith('.doc')||n.endsWith('.docx')) return '📘'
  if(n.endsWith('.ppt')||n.endsWith('.pptx')) return '📙'
  if(n.endsWith('.xls')||n.endsWith('.xlsx')||n.endsWith('.csv')) return '📗'
  if(n.endsWith('.html')||n.endsWith('.htm')) return '🌐'
  if(n.endsWith('.png')||n.endsWith('.jpg')||n.endsWith('.jpeg')) return '🖼️'
  return '📄'
}

// Icon URLs for known kinds (fallback to file)
const ICONS = {
  // Storage / generic
  file: icFile, files: icFile, upload: icFile,
  web: icWeb,
  s3: icS3,
  gdrive: icGdrive,
  dropbox: icDropbox,
  onedrive: icOnedrive,
  box: icBox,

  // Enterprise
  sharepoint: icSharepoint,
  confluence: icConfluence,
  notion: icNotion,
  airtable: icAirtable,

  // Comms
  email: icGmail, // generic email → gmail icon
  gmail: icGmail,
  outlook: icOutlook,
  slack: icSlack,
  teams: icTeams,
  zoom: icZoom,

  // Dev/Project
  github: icGithub,
  gitlab: icGitlab,
  jira: icJira,
  trello: icTrello,

  // Databases/BI/Search
  postgres: icPostgres,
  postgresql: icPostgres,
  mysql: icMysql,
  mongodb: icMongodb,
  snowflake: icSnowflake,
  bigquery: icBigQuery,
  elasticsearch: icElasticsearch,
  db: icPostgres,

  // Feeds/APIs
  rss: icRss,
  api: icApi,
  bloomberg: icBloomberg,
  refinitiv: icRefinitiv,
  esg: icEsg,

  // Social/Calendar/Design
  linkedin: icLinkedIn,
  twitter: icTwitterX,
  gcal: icGCal,
  figma: icFigma,
}
const iconForKind = (k) => ICONS[k] || icFile

// Icon for each row (connector kind or generic file)
const rowIconComp = (row) => {
  if (row?.type === 'job') {
    const k = String(row?._raw?.mode || '').toLowerCase()
    return iconForKind(k)
  }
  return isWebDoc(row) ? iconForKind('web') : icFile
}

/* ----- filters ----- */
// Unified list: show documents + non-upload jobs (e.g., Web, S3, etc.)
const combinedRows = computed(() => {
  // Deduplicate non-upload jobs by a stable key; keep the most recent
  // Show web jobs only when they are NOT successful (to surface errors/progress).
  // Hide successful web jobs because the resulting document row is shown separately.
  const nonUpload = (jobs.value || []).filter(j => {
    const m = String(j.mode || '').toLowerCase()
    if (m === 'upload') return false
    if (m === 'web') return String(j.status || '').toLowerCase() !== 'success'
    return true
  })
  const latestByKey = new Map()
  for (const j of nonUpload) {
    const k = jobKey(j)
    const prev = latestByKey.get(k)
    if (!prev) { latestByKey.set(k, j); continue }
    const da = prev.created_at ? new Date(prev.created_at).getTime() : 0
    const db = j.created_at ? new Date(j.created_at).getTime() : 0
    if (db >= da) latestByKey.set(k, j)
  }
  const jobRows = Array.from(latestByKey.values()).map(j => ({
    id: `job-${j.id}`,
    type: 'job',
    title: jobTitle(j),
    status: j.status,
    progress: j.progress || 0,
    created_at: j.created_at,
    _raw: j,
  }))

  const docRows = (docs.value || []).map(d => ({
    id: `doc-${d.id}`,
    type: 'doc',
    title: d.title || d.filename,
    status: d.status || 'QUEUED',
    progress: null,
    created_at: d.status_updated_at || d.created_at,
    _raw: d,
  }))

  const out = [...jobRows, ...docRows]
  out.sort((a,b) => {
    const da = a.created_at ? new Date(a.created_at).getTime() : 0
    const db = b.created_at ? new Date(b.created_at).getTime() : 0
    return db - da
  })
  return out
})
const filteredCombined = computed(() => {
  if (!q.value) return combinedRows.value
  const s = q.value.toLowerCase()
  return combinedRows.value.filter(r =>
    (r.title||'').toLowerCase().includes(s) ||
    (r.status||'').toLowerCase().includes(s) ||
    r.type.includes(s)
  )
})
const uniqueSources = computed(()=>{
  const seen = new Set(); const out = []
  for (const s of (sources.value||[])) {
    const k = `${(s.name||'').toLowerCase()}|${(s.kind||'').toLowerCase()}`
    if (seen.has(k)) continue; seen.add(k); out.push(s)
  }
  return out
})
const filteredSources = computed(()=>{
  if(!q.value) return uniqueSources.value
  const s=q.value.toLowerCase()
  return uniqueSources.value.filter(x => (x.name||'').toLowerCase().includes(s) || (x.kind||'').toLowerCase().includes(s))
})
const applySearch = ()=>{}

/* ----- API ----- */
const fetchJobs = async ()=>{
  const r = await authFetch(`${API}/api/ingest/jobs/`, { headers: { ...authHeaders() } })
  if(r.ok) jobs.value = await r.json()
  kpi.running = jobs.value.filter(j=>['queued','running'].includes(String(j.status||'').toLowerCase())).length
}
const fetchDocs = async ()=>{
  const r = await authFetch(`${API}/api/documents?limit=20&sort=-created_at`, { headers: authHeaders() })
  if(r.ok) docs.value = await r.json()
  kpi.documents = docs.value.length
}
const fetchSources = async ()=>{
  const r = await authFetch(`${API}/api/ingest/sources/`, { headers: authHeaders() })
  if(r.ok) sources.value = await r.json()
}
const checkHealth = async ()=>{
  try{ const r=await fetch(`${API}/health/`); kpi.health=r.ok }catch{ kpi.health=false }
}
const refreshAll = async ()=>{ await Promise.all([fetchJobs(), fetchDocs(), fetchSources(), checkHealth()]) }

// Re-run import: for docs -> create upload job with file_ids; for jobs -> clone job
const rerunImport = async (row)=>{
  try{
    // mark as running (animated)
    const setFlag = (v)=>{ rerunning.value = { ...(rerunning.value||{}), [row.id]: v } }
    setFlag(true)
    if (row?.type === 'doc'){
      const d = row._raw
      const payload = { file_ids: [d.id] }
      const r = await authFetch(`${API}/api/ingest/jobs/`, { method:'POST', headers:{ 'Content-Type':'application/json', ...authHeaders() }, body: JSON.stringify({ mode:'upload', payload }) })
      if (r.ok) await fetchJobs()
      return
    }
    if (row?.type === 'job'){
      const j = row._raw
      const body = { mode: j.mode, payload: j.payload || {}, source: j.source || undefined }
      const r = await authFetch(`${API}/api/ingest/jobs/`, { method:'POST', headers:{ 'Content-Type':'application/json', ...authHeaders() }, body: JSON.stringify(body) })
      if (r.ok) await fetchJobs()
    }
  }catch(_){ /* ignore */ }
  finally{
    // clear the flag after a short delay to avoid being stuck
    setTimeout(() => {
      const m = { ...(rerunning.value||{}) }; delete m[row.id]; rerunning.value = m
    }, 6000)
  }
}

/* ----- DnD / File pick ----- */
const onDragOver = (e)=>{ e.dataTransfer.dropEffect='copy'; isOver.value=true }
const onDragLeave = ()=>{ clearTimeout(overTimer); overTimer=setTimeout(()=>isOver.value=false,60) }
const onDrop = async (e)=>{ isOver.value=false; const files=[...(e.dataTransfer?.files||[])]; if(files.length){ router.push('/connect/files') } }

/* ----- Wizard logic removed in favor of /connect/:kind pages ----- */

/* ----- palette ----- */
const srcPalette = [
  { key:'files', name:'Files', emoji:'📁' },
  { key:'web', name:'Web', emoji:'🌐' },
  { key:'gdrive', name:'Google Drive', emoji:'🟩' },
  { key:'dropbox', name:'Dropbox', emoji:'🟦' },
  { key:'onedrive', name:'OneDrive', emoji:'🟦' },
  { key:'box', name:'Box', emoji:'📦' },
  { key:'s3', name:'S3', emoji:'🟦' },
  { key:'sharepoint', name:'SharePoint', emoji:'🏢' },
  { key:'confluence', name:'Confluence', emoji:'📘' },
  { key:'notion', name:'Notion', emoji:'⬛' },
  { key:'airtable', name:'Airtable', emoji:'📋' },
  { key:'gmail', name:'Gmail', emoji:'✉️' },
  { key:'outlook', name:'Outlook', emoji:'✉️' },
  { key:'slack', name:'Slack', emoji:'🟩' },
  { key:'teams', name:'Teams', emoji:'🟦' },
  { key:'zoom', name:'Zoom', emoji:'🎥' },
  { key:'github', name:'GitHub', emoji:'💻' },
  { key:'gitlab', name:'GitLab', emoji:'💻' },
  { key:'jira', name:'Jira', emoji:'🟦' },
  { key:'trello', name:'Trello', emoji:'🗂️' },
  { key:'postgres', name:'PostgreSQL', emoji:'🗄️' },
  { key:'mysql', name:'MySQL', emoji:'🗄️' },
  { key:'mongodb', name:'MongoDB', emoji:'🍃' },
  { key:'snowflake', name:'Snowflake', emoji:'❄️' },
  { key:'bigquery', name:'BigQuery', emoji:'🟨' },
  { key:'elasticsearch', name:'Elasticsearch', emoji:'🔍' },
  { key:'rss', name:'RSS', emoji:'📰' },
  { key:'api', name:'API', emoji:'🔗' },
  { key:'bloomberg', name:'Bloomberg', emoji:'📈' },
  { key:'refinitiv', name:'Refinitiv', emoji:'📈' },
  { key:'esg', name:'ESG API', emoji:'🌱' },
  { key:'linkedin', name:'LinkedIn', emoji:'🔮' },
  { key:'twitter', name:'Twitter (X)', emoji:'🔮' },
  { key:'gcal', name:'Google Calendar', emoji:'📆' },
  { key:'figma', name:'Figma', emoji:'🎨' },
]

/* ----- lifecycle ----- */
let poll=null
onBeforeUnmount(()=> clearInterval(poll))

// Run a saved source now
const runSource = async (s)=>{
  try{
    const r = await authFetch(`${API}/api/ingest/jobs/`,{
      method:'POST', headers:{ 'Content-Type':'application/json', ...authHeaders() },
      body: JSON.stringify({ mode: s.kind || 'source', source: s.id, payload: {} })
    })
    if(r.ok){ await fetchJobs(); }
  }catch(_){ /* ignore */ }
}

// Delete a document
const deleteDoc = async (rowOrDoc)=>{
  const d = rowOrDoc?._raw || rowOrDoc
  if (!d || !d.id) return
  const msg = (typeof t === 'function') ? t('confirmDeleteDoc', { name: d.title || d.filename || d.id }) : `Delete "${d.title || d.filename || d.id}"? This cannot be undone.`
  if (!confirm(msg)) return
  try{
    const row = rowOrDoc?._raw ? rowOrDoc : { id: `doc-${d.id}` }
    deletingRows.value = { ...(deletingRows.value||{}), [row.id]: true }
    const r = await authFetch(`${API}/api/documents/${d.id}`, { method:'DELETE', headers: { ...authHeaders() } })
    if (r.ok) { await fetchDocs() }
  }catch(_){ /* noop */ }
  finally{
    const row = rowOrDoc?._raw ? rowOrDoc : { id: `doc-${d.id}` }
    const m = { ...(deletingRows.value||{}) }; delete m[row.id]; deletingRows.value = m
  }
}

// Delete a source
const deleteSource = async (s)=>{
  if (!s || !s.id) return
  const smsg = (typeof t === 'function') ? t('confirmDeleteSource', { name: s.name }) : `Delete source "${s.name}"?`
  if (!confirm(smsg)) return
  try{
    deletingSources.value = { ...(deletingSources.value||{}), [s.id]: true }
    const r = await authFetch(`${API}/api/ingest/sources/${s.id}/`, { method:'DELETE', headers: { ...authHeaders() } })
    if (r.ok) { await fetchSources() }
  }catch(_){ /* noop */ }
  finally{
    const m = { ...(deletingSources.value||{}) }; delete m[s.id]; deletingSources.value = m
  }
}

// Open a job (web → open URL; others → navigate to setup)
const openJob = (row)=>{
  const j = row?._raw || {}
  const mode = String(j.mode || '').toLowerCase()
  if (mode === 'web' && j?.payload?.url) {
    try { window.open(j.payload.url, '_blank', 'noopener') } catch (_) {}
    return
  }
  if (mode) router.push(`/connect/${mode}`)
}

// Edit action: route to appropriate setup UI used for adding sources/uploads
const editRow = (row)=>{
  // Jobs
  if (row?.type === 'job') {
    const j = row._raw || {}
    const mode = String(j.mode || '').toLowerCase()
    if (mode === 'web'){
      const u = j.payload?.url || j.payload?.start_url || ''
      const q = u ? (`?url=${encodeURIComponent(u)}`) : ''
      router.push(`/connect/web${q}`)
      return
    }
    if (mode){ router.push(`/connect/${mode}`); return }
  }
  // Documents
  if (isWebDoc(row)){
    const u = (row?._raw?.steps_json || {}).source_url || ''
    const q = u ? (`?url=${encodeURIComponent(u)}`) : ''
    router.push(`/connect/web${q}`)
    return
  }
  router.push('/connect/files')
}

// Delete a job (owner only)
const deleteJob = async (row)=>{
  const j = row?._raw
  if (!j || !j.id) return
  const jmsg = (typeof t === 'function') ? t('confirmDeleteJob', { name: row.title }) : `Delete job "${row.title}"? This will remove the import record.`
  if (!confirm(jmsg)) return
  try{
    deletingRows.value = { ...(deletingRows.value||{}), [row.id]: true }
    const r = await authFetch(`${API}/api/ingest/jobs/${j.id}/`, { method:'DELETE', headers: { ...authHeaders() } })
    if (r.ok) await fetchJobs()
  }catch(_){ /* ignore */ }
  finally{
    const m = { ...(deletingRows.value||{}) }; delete m[row.id]; deletingRows.value = m
  }
}

// Delete files associated with an upload job row (payload.file_ids)
const deleteUploadFiles = async (row)=>{
  const job = row?._raw
  const ids = job?.payload?.file_ids
  if (!Array.isArray(ids) || !ids.length) return
  const label = row.title || `${ids.length} file(s)`
  const umsg = (typeof t === 'function') ? t('confirmDeleteFiles', { name: label }) : `Delete ${label}? This cannot be undone.`
  if (!confirm(umsg)) return
  try {
    for (const id of ids) {
      await authFetch(`${API}/api/documents/${id}`, { method: 'DELETE', headers: { ...authHeaders() } })
    }
    jobs.value = jobs.value.filter(j => j.id !== job.id)
    await fetchDocs()
  } catch (_) { /* ignore */ }
}

</script>

<style scoped>
:root{
  --bg:#f6f8ff; --card:#ffffff; --line:#e6ecf7; --txt:#25324a; --muted:#6e7b90; --blue:#1d4ed8;
  --md-shadow-1: 0 1px 3px rgba(16,24,40,.08), 0 1px 2px rgba(16,24,40,.06);
  --md-shadow-2: 0 2px 6px rgba(16,24,40,.10), 0 4px 12px rgba(16,24,40,.08);
  --md-shadow-3: 0 6px 16px rgba(16,24,40,.12), 0 8px 24px rgba(16,24,40,.10);
}
.page{ background:var(--bg); min-height:100vh; padding: 0 12px; }

.page-head{ width:100%; margin:16px 0 10px; display:flex; align-items:center; justify-content:space-between; gap:12px; }
.page-head h1{ margin:0; font-size:22px; color:var(--txt); font-weight:800; letter-spacing:.2px; }
.left{ display:flex; align-items:center; gap:12px; }
.search{ display:flex; gap:6px; align-items:center; background:#fff; border:1px solid #e5e9f5; border-radius:999px; padding:4px 6px 4px 10px; box-shadow: var(--md-shadow-1); }
.search input{ border:none; padding:8px 10px; min-width:300px; outline:none; border-radius:999px; }
.icon{ border:none; background:#1f47c5; color:#fff; border-radius:999px; width:38px; height:32px; display:inline-flex; align-items:center; justify-content:center; box-shadow: var(--md-shadow-1); }
.right{ display:flex; gap:8px; }
.primary{ border:none; background:#1f47c5; color:#fff; font-weight:800; border-radius:10px; padding:9px 12px; cursor:pointer; }
.ghost{ border:1px solid #dbe3f3; background:#fff; color:#1f47c5; border-radius:10px; padding:8px 10px; font-weight:800; cursor:pointer; }

/* dropzone */
.dropzone{ width:100%; margin:0 0 12px; background:#fff; border:2px dashed #cfe0ff; border-radius:16px; min-height:160px; display:grid; place-items:center; cursor:pointer; box-shadow: var(--md-shadow-1); transition: box-shadow .18s ease, background .18s ease; }
.dropzone.over{ background:#f0f6ff; border-color:#97bfff; box-shadow: var(--md-shadow-2); }
.dz-inner{ text-align:center; padding:24px; }
.cloud{ font-size:36px; }
.dz-title{ font-weight:800; color:#2b3a59; font-size:18px; }
.dz-sub{ color:#6e7b90; font-size:13px; margin-top:6px; }

/* grid */
.grid{ width:100%; margin:0; display:grid; grid-template-columns: 1.6fr .9fr; gap:14px; }

/* panel */
.panel{ background:var(--card); border:1px solid #e8eef8; border-radius:14px; padding:12px; box-shadow: var(--md-shadow-1); }
.tabs{ display:flex; gap:10px; border-bottom:1px solid var(--line); padding-bottom:8px; }
.tab{ border:1px solid transparent; background:#fff; color:#374151; border-radius:9px; padding:8px 12px; cursor:pointer; font-weight:800; transition: color .15s ease, background .15s ease; }
.tab:hover{ background:#f4f7ff; }
.tab.active{ background:#eaf2ff; color:#1d4ed8; border-color:#c7dafb; box-shadow: var(--md-shadow-1); }

.table-wrap{ margin-top:10px; }
.table-tools{ display:flex; justify-content:space-between; margin-bottom:6px; }
.chk{ display:flex; align-items:center; gap:6px; color:#41506a; font-size:14px; }
.tbl{ width:100%; border-collapse:separate; border-spacing:0; background:#fff; border-radius:12px; overflow:hidden; box-shadow: var(--md-shadow-1); }
.tbl th,.tbl td{ text-align:left; padding:12px 10px; border-bottom:1px solid var(--line); font-size:14px; color:var(--txt); }
.tbl th{ color:#5b6b86; font-weight:800; }
.tbl tr:hover td{ background:#fafcff; }
.truncate{ max-width:380px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.type-cell{ display:flex; align-items:center; gap:8px; }
.type-ico { display:inline-flex; font-size: 18px; line-height: 1; }
.badge{ padding:3px 8px; border-radius:999px; font-size:12px; font-weight:800; border:1px solid transparent; }
.badge.uploaded{ background:#fff0da; color:#9a6700; border-color:#ffd89a; }
.badge.processing{ background:#eaf2ff; color:#1d4ed8; border-color:#c7dafb; }
.badge.imported{ background:#e8f7ee; color:#047857; border-color:#b7e5c9; }
.badge.failed{ background:#ffe8e6; color:#b42318; border-color:#f6b2ad; }
.dots{ display:inline-flex; gap:1px; margin-left:1px; }
.dots span{ opacity:0; animation: dotblink 1.2s infinite; }
.dots span:nth-child(2){ animation-delay:.2s }
.dots span:nth-child(3){ animation-delay:.4s }
@keyframes dotblink{ 0%,20%{ opacity:0 } 50%{ opacity:1 } 100%{ opacity:0 } }
.prog-cell{ width:190px; }
.prog{ width:100%; height:8px; background:#edf2ff; border:1px solid #dfe8fb; border-radius:999px; overflow:hidden; }
.prog .bar{ height:100%; width:0%; background:#4f7cff; transition:width .25s; }
.empty{ color:#8a97ab; text-align:center; padding:12px 0; }

/* docs */
.docs-grid{ display:grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap:10px; padding-top:10px; }
.doc-card{ background:#fff; border:1px solid #e8eef8; border-radius:12px; padding:12px; display:grid; gap:6px; box-shadow: var(--md-shadow-1); transition: transform .15s ease, box-shadow .15s ease; }
.doc-card:hover{ transform: translateY(-2px); box-shadow: var(--md-shadow-2); }
.doc-ico{ font-size:24px; }
.doc-title{ font-weight:800; color:#2a3342; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.doc-meta{ color:#6e7b90; font-size:13px; }
.doc-actions{ display:flex; gap:10px; }
.link{ background:transparent; border:none; color:#1d4ed8; font-weight:800; cursor:pointer; padding:0; }
.link.danger{ color:#b42318; }
.row-actions{ display:inline-flex; gap:10px; align-items:center; }
.link[disabled]{ opacity:.6; pointer-events:none; }
.icon-btn{ width:28px; height:28px; display:inline-flex; align-items:center; justify-content:center; border-radius:6px; }
.icon-btn:hover{ background:#eef3ff; }
.icon-svg{ width:16px; height:16px; display:block; }

/* right */
.side{ display:grid; gap:12px; }
.kpis{ display:grid; grid-template-columns: repeat(3, 1fr); gap:8px; }
.kpi{ background:#fff; border:1px solid #e8eef8; border-radius:12px; padding:12px; box-shadow: var(--md-shadow-1); }
.kpi-title{ color:#6e7b90; font-size:13px; font-weight:800; }
.kpi-val{ font-size:22px; font-weight:900; color:#1f2a44; }
.kpi-val.ok{ color:#0a8d3a } .kpi-val.bad{ color:#b42318 }

.sources{ background:#fff; border:1px solid #e8eef8; border-radius:12px; padding:12px; box-shadow: var(--md-shadow-1); }
.sources-head{ display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
.src-grid{ display:grid; grid-template-columns: repeat(6, 1fr); gap:10px; }
.src-btn{ background:#fff; border:1px solid #e6ecf7; border-radius:12px; padding:12px; cursor:pointer; text-align:center; box-shadow: var(--md-shadow-1); transition: transform .15s ease, box-shadow .15s ease, background .12s ease; display:grid; gap:8px; justify-items:center; }
.src-btn:hover{ background:#f8fbff; transform: translateY(-2px); box-shadow: var(--md-shadow-2); }
.src-ico{ font-size:20px; } .src-name{ margin-top:6px; font-size:12.5px; font-weight:800; color:#2a3342; }
.src-ico-comp{ display:inline-flex; font-size: 20px; line-height: 1; }
.src-ico-img{ width:1em; height:1em; display:inline-block; object-fit:contain; }
.info-line{ font-size:12.5px; color:#5b6b86; padding:8px 10px; border:1px dashed #dbe3f3; border-radius:10px; background:#fafcff; margin-bottom:8px; }

.connected{ margin-top:12px; }
.conn-title{ font-weight:900; color:#2a3342; margin-bottom:6px; }
.conn-list{ display:grid; gap:6px; }
.conn-item{ display:flex; align-items:center; justify-content:space-between; background:#fff; border:1px solid #e8eef8; border-radius:10px; padding:10px 12px; box-shadow: var(--md-shadow-1); }
.ci-left{ display:flex; align-items:center; gap:8px; color:#344562; }
.dot{ width:8px; height:8px; background:#22c55e; border-radius:999px; display:inline-block; }
.kind{ color:#8192aa; }

/* modal */
.modal{ position:fixed; inset:0; background:rgba(0,0,0,.35); display:grid; place-items:center; z-index:30; }
.modal-box{ width:min(860px, 96vw); background:#fff; border-radius:14px; border:1px solid var(--line); box-shadow:0 18px 48px rgba(31,64,175,.18); }
.modal-head{ display:flex; align-items:center; justify-content:space-between; padding:12px 14px; border-bottom:1px solid var(--line); }
.close{ background:transparent; border:none; font-size:18px; cursor:pointer; }
.wizard-tabs{ display:flex; gap:8px; padding:8px 12px; border-bottom:1px solid var(--line); overflow-x:auto; }
.wtab{ border:1px solid #dbe3f3; background:#fff; color:#1e2a44; border-radius:9px; padding:6px 10px; cursor:pointer; font-weight:800; }
.wtab.active{ background:#eaf2ff; color:#1d4ed8; border-color:#c7dafb; }
.wizard-body{ padding:14px; }
.pane{ display:grid; gap:10px; }
.row{ display:grid; gap:6px; }
.row input{ border:1px solid #dbe3f3; border-radius:10px; padding:9px 12px; }
.actions{ display:flex; justify-content:flex-end; gap:8px; }
.status{ color:#1e3a8a; font-weight:800; }

.hidden{ display:none; }

@media (max-width: 990px){
  .grid{ grid-template-columns:1fr; }
}
@media (max-width: 640px){
  .kpis{ grid-template-columns:1fr; }
  .src-grid{ grid-template-columns: repeat(3, 1fr); }
}
</style>
