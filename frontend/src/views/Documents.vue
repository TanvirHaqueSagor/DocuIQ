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
        <button class="primary" @click="openWizard('files')">＋ {{ $t ? $t('addData') : 'Add Data' }}</button>
      </div>
    </header>

    <!-- Drag & Drop hero (click opens file picker) -->
    <section
      class="dropzone"
      :class="{ over: isOver }"
      @dragover.prevent="onDragOver"
      @dragleave.prevent="onDragLeave"
      @drop.prevent="onDrop"
      @click="fileInput?.click()"
    >
      <input ref="fileInput" type="file" multiple class="hidden" @change="onPickFiles" />
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
        <nav class="tabs">
          <button :class="['tab', {active: tab==='imports'}]" @click="tab='imports'">
            {{ $t ? $t('imports') : 'Imports' }}
          </button>
          <button :class="['tab', {active: tab==='docs'}]" @click="tab='docs'">
            {{ $t ? $t('documents') : 'Documents' }}
          </button>
        </nav>

        <!-- Imports table -->
        <div v-if="tab==='imports'" class="table-wrap">
          <div class="table-tools">
            <label class="chk">
              <input type="checkbox" v-model="autoRefresh" />
              <span>{{ $t ? $t('autoRefresh') : 'Auto refresh' }}</span>
            </label>
          </div>
          <table class="tbl" role="table">
            <thead>
              <tr>
                <th>ID</th><th>Title</th><th>Status</th><th>Progress</th><th>Created</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="j in filteredJobs" :key="j.id">
                <td>{{ j.id }}</td>
                <td class="truncate">{{ jobTitle(j) }}</td>
                <td><span class="badge" :class="j.status">{{ prettyStatus(j.status) }}</span></td>
                <td class="prog-cell">
                  <div class="prog"><div class="bar" :style="{ width: (j.progress||0) + '%' }"></div></div>
                </td>
                <td>{{ fmtDate(j.created_at) }}</td>
              </tr>
              <tr v-if="!filteredJobs.length">
                <td colspan="5" class="empty">No imports yet</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Documents list -->
        <div v-else class="docs-grid">
          <div v-for="d in filteredDocs" :key="d.id" class="doc-card">
            <div class="doc-ico">{{ fileEmoji(d.filename || d.title) }}</div>
            <div class="doc-title" :title="d.title || d.filename">{{ d.title || d.filename }}</div>
            <div class="doc-meta">{{ fmtDate(d.created_at) }}</div>
            <div class="doc-actions">
              <RouterLink class="link" :to="`/documents/${d.id}`">Open</RouterLink>
              <button class="link danger" @click="deleteDoc(d)">Delete</button>
            </div>
          </div>
          <div v-if="!filteredDocs.length" class="empty-card">
            {{ $t ? $t('noDocs') : 'No documents yet. Use Add Data above.' }}
          </div>
        </div>
      </section>

      <!-- Right: KPIs + Connected Sources (no floating mini) -->
      <aside class="side">
        <div class="kpis">
          <div class="kpi">
            <div class="kpi-title">Documents</div>
            <div class="kpi-val">{{ kpi.documents }}</div>
          </div>
          <div class="kpi">
            <div class="kpi-title">Running jobs</div>
            <div class="kpi-val">{{ kpi.running }}</div>
          </div>
          <div class="kpi">
            <div class="kpi-title">Server</div>
            <div class="kpi-val" :class="kpi.health ? 'ok' : 'bad'">{{ kpi.health ? 'OK' : 'Down' }}</div>
          </div>
        </div>

        <div class="sources">
          <div class="sources-head">
            <h3>Sources</h3>
            <button class="ghost" @click="openWizard('gdrive')">＋ Connect</button>
          </div>

          <div class="src-grid">
            <button v-for="s in srcPalette" :key="s.key" class="src-btn" @click="openWizard(s.key)">
              <div class="src-ico">{{ s.emoji }}</div>
              <div class="src-name">{{ s.name }}</div>
            </button>
          </div>

          <div class="connected" v-if="sources.length">
            <div class="conn-title">Connected</div>
            <div class="conn-list">
              <div v-for="s in filteredSources" :key="s.id" class="conn-item">
                <div class="ci-left">
                  <span class="dot"></span>
                  <span class="nm">{{ s.name }}</span>
                  <span class="kind">· {{ prettyKind(s.kind) }}</span>
                </div>
                <div class="ci-actions">
                  <button class="link" @click="runSource(s)">Run</button>
                  <button class="link danger" @click="deleteSource(s)">Delete</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>

    <!-- Add Data Modal -->
    <div v-if="wizard.open" class="modal" @click.self="wizard.open=false">
      <div class="modal-box">
        <header class="modal-head">
          <h3>Add Data</h3>
          <button class="close" @click="wizard.open=false" aria-label="Close">✕</button>
        </header>

        <nav class="wizard-tabs">
          <button v-for="t in wizardTabs" :key="t.key"
                  :class="['wtab', {active: wizard.tab===t.key}]"
                  @click="wizard.tab=t.key">{{ t.label }}</button>
        </nav>

        <section class="wizard-body">
          <!-- Files -->
          <div v-if="wizard.tab==='files'" class="pane">
            <h4>Upload files</h4>
            <input type="file" multiple @change="onPickFiles" />
            <ul class="picked" v-if="pickedFiles.length">
              <li v-for="f in pickedFiles" :key="f.name">{{ f.name }} ({{ f.size }}B)</li>
            </ul>
            <div class="row">
              <label>Collection</label>
              <input v-model="meta.collection" placeholder="e.g. Annual Reports" />
            </div>
            <div class="row">
              <label>Tags</label>
              <input v-model="meta.tags" placeholder="comma,separated" />
            </div>
            <div class="actions">
              <button class="primary" :disabled="!pickedFiles.length" @click="startUpload">
                {{ uploading ? 'Uploading…' : 'Start import' }}
              </button>
            </div>
            <div class="status" v-if="statusMsg">{{ statusMsg }}</div>
          </div>

          <!-- Web -->
          <div v-else-if="wizard.tab==='web'" class="pane">
            <h4>Website</h4>
            <div class="row"><label>URL</label><input v-model="web.url" placeholder="https://example.com/page" /></div>
            <div class="row"><label><input type="checkbox" v-model="web.crawl" /> Crawl sub-urls</label></div>
            <div class="row" v-if="web.crawl"><label>Depth</label><input type="number" min="1" max="3" v-model.number="web.depth" /></div>
            <div class="actions"><button class="primary" :disabled="!validWeb" @click="createWebJob">Start import</button></div>
            <div class="status" v-if="statusMsg">{{ statusMsg }}</div>
          </div>

          <!-- S3 -->
          <div v-else-if="wizard.tab==='s3'" class="pane">
            <h4>AWS S3</h4>
            <div class="row"><label>Name</label><input v-model="s3.name" placeholder="My S3" /></div>
            <div class="row"><label>Bucket</label><input v-model="s3.bucket" placeholder="my-bucket" /></div>
            <div class="row"><label>Prefix</label><input v-model="s3.prefix" placeholder="folder/path/" /></div>
            <div class="row"><label><input type="checkbox" v-model="s3.sync" /> Keep in sync</label></div>
            <div class="actions"><button class="primary" :disabled="!validS3" @click="createS3Job">Connect & import</button></div>
            <div class="status" v-if="statusMsg">{{ statusMsg }}</div>
          </div>

          <!-- Google Drive (placeholder create source) -->
          <div v-else-if="wizard.tab==='gdrive'" class="pane">
            <h4>Google Drive</h4>
            <p>OAuth will open when connector is implemented.</p>
            <div class="row"><label>Name</label><input v-model="gdrive.name" placeholder="My Drive" /></div>
            <div class="actions"><button class="primary" :disabled="!gdrive.name" @click="createGenericSource('gdrive')">Connect</button></div>
            <div class="status" v-if="statusMsg">{{ statusMsg }}</div>
          </div>

          <!-- Future connectors -->
          <div v-else class="pane">
            <h4>{{ currentTabLabel }}</h4>
            <p>Create a Source entry now (connector coming soon).</p>
            <div class="row"><label>Name</label><input v-model="generic.name" :placeholder="`My ${currentTabLabel}`" /></div>
            <div class="actions"><button class="primary" :disabled="!generic.name" @click="createGenericSource(wizard.tab)">Create source</button></div>
            <div class="status" v-if="statusMsg">{{ statusMsg }}</div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { API_BASE_URL as API } from '../config'

/* ----- state ----- */
const q = ref('')
const tab = ref('imports')
const isOver = ref(false); let overTimer=null
const autoRefresh = ref(true)
const jobs = ref([]); const docs = ref([]); const sources = ref([])
const kpi = reactive({ documents: 0, running: 0, health: true })
const fileInput = ref(null)

/* ----- wizard ----- */
const wizard = reactive({ open:false, tab:'files' })
const wizardTabs = [
  { key:'files', label:'Files' }, { key:'web', label:'Web' },
  { key:'s3', label:'S3' }, { key:'gdrive', label:'Google Drive' }
]
const openWizard = (t='files') => { wizard.tab=t; wizard.open=true }

onMounted(async () => {
  try {
    ensureAuthOrRedirect()   // টোকেন না থাকলে এখানে থেমে /login এ যাবে
    await refreshAll()
    poll = setInterval(() => { if (autoRefresh.value) fetchJobs() }, 5000)
  } catch (e) {
    // redirected; কিছুই করার নেই
  }
})

/* ----- helpers ----- */
import { useRouter, useRoute } from 'vue-router'
const router = useRouter()
const route  = useRoute()

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
const fmtDate = (iso) => { try { return new Date(iso).toLocaleString() } catch { return iso||'' } }
const prettyStatus = (s)=> s ? s[0].toUpperCase()+s.slice(1) : s
const prettyKind = (k)=> ({ s3:'S3', gdrive:'Google Drive', web:'Web', email:'Email', slack:'Slack', github:'GitHub', db:'Database', api:'API', media:'Media' }[k] || k)
const jobTitle = (j) => {
  const m=(j.mode||'').toUpperCase()
  if(j.mode==='web') return `${m} · ${j.payload?.url||''}`
  if(j.mode==='s3')  return `${m} · ${j.payload?.bucket||''}/${j.payload?.prefix||''}`
  if(j.mode==='upload') return `${m} · ${(j.payload?.file_ids?.length||0)} files`
  return m
}
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

/* ----- filters ----- */
const filteredJobs = computed(()=>{
  if(!q.value) return jobs.value
  const s=q.value.toLowerCase()
  return jobs.value.filter(j => jobTitle(j).toLowerCase().includes(s) || (j.status||'').toLowerCase().includes(s))
})
const filteredDocs = computed(()=>{
  if(!q.value) return docs.value
  const s=q.value.toLowerCase()
  return docs.value.filter(d => (d.title||d.filename||'').toLowerCase().includes(s))
})
const filteredSources = computed(()=>{
  if(!q.value) return sources.value
  const s=q.value.toLowerCase()
  return sources.value.filter(x => (x.name||'').toLowerCase().includes(s) || (x.kind||'').toLowerCase().includes(s))
})
const applySearch = ()=>{}

/* ----- API ----- */
const fetchJobs = async ()=>{
  const r = await fetch(`${API}/api/ingest/jobs/`, { headers: { ...authHeaders() } })
  if(r.ok) jobs.value = await r.json()
  kpi.running = jobs.value.filter(j=>['queued','running'].includes(j.status)).length
}
const fetchDocs = async ()=>{
  const r = await fetch(`${API}/api/documents?limit=20&sort=-created_at`, { headers: authHeaders() })
  if(r.ok) docs.value = await r.json()
  kpi.documents = docs.value.length
}
const fetchSources = async ()=>{
  const r = await fetch(`${API}/api/ingest/sources/`, { headers: authHeaders() })
  if(r.ok) sources.value = await r.json()
}
const checkHealth = async ()=>{
  try{ const r=await fetch(`${API}/health/`); kpi.health=r.ok }catch{ kpi.health=false }
}
const refreshAll = async ()=>{ await Promise.all([fetchJobs(), fetchDocs(), fetchSources(), checkHealth()]) }

/* ----- DnD / File pick ----- */
const onDragOver = (e)=>{ e.dataTransfer.dropEffect='copy'; isOver.value=true }
const onDragLeave = ()=>{ clearTimeout(overTimer); overTimer=setTimeout(()=>isOver.value=false,60) }
const onDrop = async (e)=>{ isOver.value=false; pickedFiles.value = [...(e.dataTransfer?.files||[])]; if(pickedFiles.value.length) { wizard.open=true; wizard.tab='files' } }

/* ----- Wizard logic ----- */
const pickedFiles = ref([]); const meta = reactive({ collection:'', tags:'' })
const web = reactive({ url:'', crawl:false, depth:1 })
const s3  = reactive({ name:'', bucket:'', prefix:'', sync:true })
const gdrive = reactive({ name:'' })
const generic = reactive({ name:'' })
const statusMsg = ref(''); const uploading = ref(false)
const validWeb = computed(()=> /^https?:\/\//i.test(web.url||'')); const validS3 = computed(()=> !!(s3.name && s3.bucket))
const currentTabLabel = computed(()=> wizardTabs.find(x=>x.key===wizard.tab)?.label || 'Source')
const onPickFiles = (e)=>{ pickedFiles.value = Array.from(e.target.files || []) }

// helper: safely read JSON or show the first lines of HTML/text
const readJsonSafe = async (res) => {
  const ctype = res.headers.get('content-type') || ''
  const text = await res.text()
  if (ctype.includes('application/json')) {
    try { return JSON.parse(text) } catch { /* fallthrough */ }
  }
  // not JSON → throw informative error
  throw new Error(`HTTP ${res.status} ${res.statusText} — ${text.slice(0,180)}`)
}

const startUpload = async () => {
  if (!pickedFiles.value.length) return
  statusMsg.value = ''
  uploading.value = true
  try {
    const fd = new FormData()
    for (const f of pickedFiles.value) fd.append('files', f)

    const up = await fetch(`${API}/api/ingest/upload/`, {
      method: 'POST',
      headers: { ...authHeaders() },          // Content-Type দিবেন না → ব্রাউজার boundary সেট করবে
      body: fd,
    })

    const list = await readJsonSafe(up)
    if (!up.ok) throw new Error(list?.detail || 'Upload failed')

    const file_ids = Array.isArray(list) ? list.map(x => x.id) :
                     Array.isArray(list.files) ? list.files.map(x => x.id) : []
    if (!file_ids.length) throw new Error('No file ids returned')

    const j = await fetch(`${API}/api/ingest/jobs/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({
        mode: 'upload',
        payload: { file_ids, collection: meta.collection, tags: meta.tags }
      })
    })
    const jd = await readJsonSafe(j)
    if (!j.ok) throw new Error(jd?.detail || 'Job create failed')

    statusMsg.value = '✅ Import started'
    wizard.open = false
    pickedFiles.value = []
    await fetchJobs(); await fetchDocs()
    tab.value = 'imports'
  } catch (e) {
    statusMsg.value = `❌ ${e.message || e}`
  } finally {
    uploading.value = false
  }
}


const createWebJob = async ()=>{
  statusMsg.value=''
  try{
    const r=await fetch(`${API}/api/ingest/jobs/`,{
      method:'POST', headers:{ 'Content-Type':'application/json', ...authHeaders() },
      body: JSON.stringify({ mode:'web', payload:{ url:web.url, crawl:web.crawl, depth:web.depth } })
    })
    const d=await r.json(); if(!r.ok) throw new Error(d?.detail || 'Job create failed')
    statusMsg.value='✅ Website import queued'; wizard.open=false; await fetchJobs(); tab.value='imports'
  }catch(e){ statusMsg.value=`❌ ${e.message || e}` }
}

const createS3Job = async ()=>{
  statusMsg.value=''
  try{
    const s = await fetch(`${API}/api/ingest/sources/`,{
      method:'POST', headers:{ 'Content-Type':'application/json', ...authHeaders() },
      body: JSON.stringify({ kind:'s3', name:s3.name, config:{ bucket:s3.bucket, prefix:s3.prefix, sync:s3.sync } })
    })
    const src=await s.json(); if(!s.ok) throw new Error(src?.detail || 'Source create failed')
    const j = await fetch(`${API}/api/ingest/jobs/`,{
      method:'POST', headers:{ 'Content-Type':'application/json', ...authHeaders() },
      body: JSON.stringify({ mode:'s3', source:src.id, payload:{ bucket:s3.bucket, prefix:s3.prefix, sync:s3.sync } })
    })
    const jd=await j.json(); if(!j.ok) throw new Error(jd?.detail || 'Job create failed')
    statusMsg.value='✅ S3 import queued'; wizard.open=false; await fetchSources(); await fetchJobs(); tab.value='imports'
  }catch(e){ statusMsg.value=`❌ ${e.message || e}` }
}

const createGenericSource = async (kind)=>{
  statusMsg.value=''
  try{
    const r=await fetch(`${API}/api/ingest/sources/`,{
      method:'POST', headers:{ 'Content-Type':'application/json', ...authHeaders() },
      body: JSON.stringify({ kind, name:generic.name || gdrive.name, config:{} })
    })
    const d=await r.json(); if(!r.ok) throw new Error(d?.detail || 'Source create failed')
    statusMsg.value='✅ Source created'; wizard.open=false; await fetchSources()
  }catch(e){ statusMsg.value=`❌ ${e.message || e}` }
}

/* ----- palette ----- */
const srcPalette = [
  { key:'gdrive', name:'Google Drive', emoji:'🟩' },
  { key:'s3', name:'S3', emoji:'🟦' },
  { key:'slack', name:'Slack', emoji:'🟩' },
  { key:'web', name:'Web', emoji:'🌐' },
  { key:'notion', name:'Notion', emoji:'⬛' },
  { key:'jira', name:'Jira', emoji:'🟦' },
  { key:'email', name:'Email', emoji:'✉️' },
  { key:'media', name:'Video', emoji:'🎞️' },
  { key:'db', name:'Database', emoji:'🗄️' },
  { key:'api', name:'API', emoji:'🔗' },
]

/* ----- lifecycle ----- */
let poll=null
onMounted(async ()=>{ await refreshAll(); poll=setInterval(()=>{ if(autoRefresh.value) fetchJobs() }, 5000) })
onBeforeUnmount(()=> clearInterval(poll))
</script>

<style scoped>
:root{ --bg:#f6f8ff; --card:#ffffff; --line:#e6ecf7; --txt:#25324a; --muted:#6e7b90; --blue:#1d4ed8; }
.page{ background:var(--bg); min-height:100vh; }

.page-head{ width:min(1100px, 94%); margin:16px auto 10px; display:flex; align-items:center; justify-content:space-between; gap:12px; }
.page-head h1{ margin:0; font-size:22px; color:var(--txt); font-weight:800; letter-spacing:.2px; }
.left{ display:flex; align-items:center; gap:12px; }
.search{ display:flex; gap:6px; }
.search input{ border:1px solid #dbe3f3; border-radius:10px; padding:8px 10px; min-width:260px; outline:none; }
.icon{ border:1px solid #dbe3f3; background:#fff; border-radius:10px; width:38px; }
.right{ display:flex; gap:8px; }
.primary{ border:none; background:#1f47c5; color:#fff; font-weight:800; border-radius:10px; padding:9px 12px; cursor:pointer; }
.ghost{ border:1px solid #dbe3f3; background:#fff; color:#1f47c5; border-radius:10px; padding:8px 10px; font-weight:800; cursor:pointer; }

/* dropzone */
.dropzone{ width:min(1100px, 94%); margin:0 auto 12px; background:#fff; border:2px dashed #cfe0ff; border-radius:16px; min-height:140px; display:grid; place-items:center; cursor:pointer; }
.dropzone.over{ background:#f0f6ff; border-color:#97bfff; }
.dz-inner{ text-align:center; padding:24px; }
.cloud{ font-size:32px; }
.dz-title{ font-weight:800; color:#2b3a59; }
.dz-sub{ color:#6e7b90; font-size:13px; margin-top:6px; }

/* grid */
.grid{ width:min(1100px, 94%); margin:0 auto; display:grid; grid-template-columns: 1.6fr .9fr; gap:12px; }

/* panel */
.panel{ background:var(--card); border:1px solid var(--line); border-radius:14px; padding:12px; }
.tabs{ display:flex; gap:10px; border-bottom:1px solid var(--line); padding-bottom:8px; }
.tab{ border:1px solid #dbe3f3; background:#fff; color:#374151; border-radius:9px; padding:6px 10px; cursor:pointer; font-weight:800; }
.tab.active{ background:#eaf2ff; color:#1d4ed8; border-color:#c7dafb; }

.table-wrap{ margin-top:10px; }
.table-tools{ display:flex; justify-content:space-between; margin-bottom:6px; }
.chk{ display:flex; align-items:center; gap:6px; color:#41506a; font-size:14px; }
.tbl{ width:100%; border-collapse:collapse; }
.tbl th,.tbl td{ text-align:left; padding:10px 8px; border-bottom:1px solid var(--line); font-size:14px; color:var(--txt); }
.tbl th{ color:#5b6b86; font-weight:800; }
.truncate{ max-width:380px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.badge{ padding:3px 8px; border-radius:999px; font-size:12px; font-weight:800; border:1px solid transparent; }
.badge.queued{ background:#fff0da; color:#9a6700; border-color:#ffd89a; }
.badge.running{ background:#eaf2ff; color:#1d4ed8; border-color:#c7dafb; }
.badge.success{ background:#e8f7ee; color:#047857; border-color:#b7e5c9; }
.badge.failed{ background:#ffe8e6; color:#b42318; border-color:#f6b2ad; }
.prog-cell{ width:190px; }
.prog{ width:100%; height:8px; background:#edf2ff; border:1px solid #dfe8fb; border-radius:999px; overflow:hidden; }
.prog .bar{ height:100%; width:0%; background:#4f7cff; transition:width .25s; }
.empty{ color:#8a97ab; text-align:center; padding:12px 0; }

/* docs */
.docs-grid{ display:grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap:10px; padding-top:10px; }
.doc-card{ background:#f9fbff; border:1px solid var(--line); border-radius:12px; padding:10px; display:grid; gap:6px; }
.doc-ico{ font-size:24px; }
.doc-title{ font-weight:800; color:#2a3342; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.doc-meta{ color:#6e7b90; font-size:13px; }
.doc-actions{ display:flex; gap:10px; }
.link{ background:transparent; border:none; color:#1d4ed8; font-weight:800; cursor:pointer; padding:0; }
.link.danger{ color:#b42318; }

/* right */
.side{ display:grid; gap:12px; }
.kpis{ display:grid; grid-template-columns: repeat(3, 1fr); gap:8px; }
.kpi{ background:#fff; border:1px solid var(--line); border-radius:12px; padding:12px; }
.kpi-title{ color:#6e7b90; font-size:13px; font-weight:800; }
.kpi-val{ font-size:22px; font-weight:900; color:#1f2a44; }
.kpi-val.ok{ color:#0a8d3a } .kpi-val.bad{ color:#b42318 }

.sources{ background:#fff; border:1px solid var(--line); border-radius:12px; padding:12px; }
.sources-head{ display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
.src-grid{ display:grid; grid-template-columns: repeat(5, 1fr); gap:8px; }
.src-btn{ background:#f7faff; border:1px solid #dfe8fb; border-radius:12px; padding:10px; cursor:pointer; text-align:center; }
.src-ico{ font-size:20px; } .src-name{ margin-top:6px; font-size:12.5px; font-weight:800; color:#2a3342; }

.connected{ margin-top:12px; }
.conn-title{ font-weight:900; color:#2a3342; margin-bottom:6px; }
.conn-list{ display:grid; gap:6px; }
.conn-item{ display:flex; align-items:center; justify-content:space-between; background:#fbfdff; border:1px solid #e8eefb; border-radius:10px; padding:8px 10px; }
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
