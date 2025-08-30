<template>
  <div v-if="bus.open" class="iw-overlay" @click.self="onClose">
    <div class="iw-modal">
      <header class="iw-head">
        <h3>➕ Add data</h3>
        <button class="x" @click="onClose">✕</button>
      </header>

      <nav class="iw-tabs">
        <button v-for="t in tabs" :key="t.key"
          :class="['tab', {active: activeTab===t.key}]"
          @click="activeTab = t.key">{{ t.label }}</button>
      </nav>

      <section class="iw-body">
        <!-- Files -->
        <div v-if="activeTab==='files'" class="pane">
          <h4>Upload files</h4>
          <input type="file" multiple @change="onPickFiles" />
          <p class="hint">pdf, docx, xlsx, pptx, html, image, audio/video…</p>
          <ul class="picked" v-if="pickedFiles.length">
            <li v-for="f in pickedFiles" :key="f.name">{{ f.name }} ({{ f.size }} bytes)</li>
          </ul>
          <div class="row">
            <label>Collection / Folder</label>
            <input v-model="meta.collection" placeholder="e.g. Finance 2025" />
          </div>
          <div class="row">
            <label>Tags</label>
            <input v-model="meta.tags" placeholder="comma,separated,tags" />
          </div>
          <div class="actions">
            <button class="btn" :disabled="uploading || !pickedFiles.length" @click="startUpload">
              {{ uploading ? 'Uploading...' : 'Start import' }}
            </button>
          </div>
        </div>

        <!-- Web -->
        <div v-else-if="activeTab==='web'" class="pane">
          <h4>Website</h4>
          <div class="row">
            <label>URL</label>
            <input v-model="web.url" placeholder="https://example.com/page" />
          </div>
          <div class="row">
            <label><input type="checkbox" v-model="web.crawl" /> Crawl sub-urls</label>
          </div>
          <div class="row" v-if="web.crawl">
            <label>Depth</label>
            <input type="number" v-model.number="web.depth" min="1" max="3" />
          </div>
          <div class="actions">
            <button class="btn" :disabled="!validWeb" @click="createWebJob">Start import</button>
          </div>
        </div>

        <!-- S3 -->
        <div v-else-if="activeTab==='s3'" class="pane">
          <h4>AWS S3</h4>
          <div class="row"><label>Connection name</label><input v-model="s3.name" placeholder="My S3 Bucket" /></div>
          <div class="row"><label>Bucket</label><input v-model="s3.bucket" placeholder="my-bucket" /></div>
          <div class="row"><label>Prefix (optional)</label><input v-model="s3.prefix" placeholder="folder/path/" /></div>
          <div class="row"><label><input type="checkbox" v-model="s3.sync" /> Keep folder in sync</label></div>
          <div class="actions">
            <button class="btn" :disabled="!validS3" @click="createS3Job">Connect & import</button>
          </div>
          <p class="hint">নোট: ক্রেডেনশিয়াল/STS কনফিগ ব্যাকএন্ডে সিকিউরভাবে রাখবেন।</p>
        </div>

        <!-- Placeholders for other connectors -->
        <div v-else class="pane">
          <h4>{{ currentTabLabel }}</h4>
          <p>Connector coming soon. Create a “Source” now and attach later.</p>
          <div class="row"><label>Connection name</label><input v-model="generic.name" placeholder="My {{ currentTabLabel }}" /></div>
          <div class="actions"><button class="btn" :disabled="!generic.name" @click="createGenericSource">Create source</button></div>
        </div>
      </section>

      <footer class="iw-foot">
        <div class="status" v-if="statusMsg">{{ statusMsg }}</div>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, watch, onMounted } from 'vue'
import { API_BASE_URL } from '../config'
import { importWizardBus as bus, closeImportWizard } from '../stores/importWizardBus'

const tabs = [
  { key: 'files', label: 'Files' },
  { key: 'web', label: 'Web' },
  { key: 's3', label: 'S3' },
  { key: 'gdrive', label: 'Google Drive' },
  { key: 'email', label: 'Email' },
  { key: 'slack', label: 'Slack' },
  { key: 'github', label: 'GitHub' },
  { key: 'db', label: 'Database' },
  { key: 'api', label: 'API' },
  { key: 'media', label: 'Media' },
]
const activeTab = ref('files')
watch(() => bus.preset, (p) => { if (p?.tab) activeTab.value = p.tab })

const token = () => localStorage.getItem('token') || localStorage.getItem('access')
const authHeaders = () => ({ Authorization: `Bearer ${token()}` })

const pickedFiles = ref([])
const meta = reactive({ collection: '', tags: '' })
const uploading = ref(false)
const statusMsg = ref('')

const web = reactive({ url: '', crawl: false, depth: 1 })
const validWeb = computed(() => /^https?:\/\//i.test(web.url || ''))

const s3 = reactive({ name: '', bucket: '', prefix: '', sync: true })
const validS3 = computed(() => !!(s3.name && s3.bucket))

const generic = reactive({ name: '' })
const currentTabLabel = computed(() => tabs.find(t=>t.key===activeTab.value)?.label || 'Source')

const onPickFiles = (e) => { pickedFiles.value = Array.from(e.target.files || []) }

const startUpload = async () => {
  if (!pickedFiles.value.length) return
  uploading.value = true
  statusMsg.value = ''
  try {
    const fd = new FormData()
    for (const f of pickedFiles.value) fd.append('files', f)
    const up = await fetch(`${API_BASE_URL}/api/ingest/upload/`, {
      method: 'POST', headers: authHeaders(), body: fd
    })
    const files = await up.json()
    if (!up.ok) throw new Error(files?.detail || 'Upload failed')
    const file_ids = files.map(x => x.id)
    // Create job
    const jobRes = await fetch(`${API_BASE_URL}/api/ingest/jobs/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({
        mode: 'upload',
        payload: { file_ids, collection: meta.collection, tags: meta.tags }
      })
    })
    const job = await jobRes.json()
    if (!jobRes.ok) throw new Error(job?.detail || 'Job create failed')
    statusMsg.value = '✅ Import started'
    // Optional: close after a short delay
    setTimeout(onClose, 900)
  } catch (e) {
    statusMsg.value = `❌ ${e.message || e}`
  } finally {
    uploading.value = false
  }
}

const createWebJob = async () => {
  statusMsg.value = ''
  try {
    const res = await fetch(`${API_BASE_URL}/api/ingest/jobs/`, {
      method: 'POST',
      headers: { 'Content-Type':'application/json', ...authHeaders() },
      body: JSON.stringify({
        mode: 'web',
        payload: { url: web.url, crawl: web.crawl, depth: web.depth }
      })
    })
    const job = await res.json()
    if (!res.ok) throw new Error(job?.detail || 'Job create failed')
    statusMsg.value = '✅ Website import queued'
    setTimeout(onClose, 900)
  } catch (e) {
    statusMsg.value = `❌ ${e.message || e}`
  }
}

const createS3Job = async () => {
  statusMsg.value = ''
  try {
    // 1) ensure source exists (or create)
    const srcRes = await fetch(`${API_BASE_URL}/api/ingest/sources/`, {
      method: 'POST',
      headers: { 'Content-Type':'application/json', ...authHeaders() },
      body: JSON.stringify({
        kind: 's3',
        name: s3.name,
        config: { bucket: s3.bucket, prefix: s3.prefix, sync: s3.sync }
      })
    })
    const src = await srcRes.json()
    if (!srcRes.ok) throw new Error(src?.detail || 'Source create failed')
    // 2) create job
    const jobRes = await fetch(`${API_BASE_URL}/api/ingest/jobs/`, {
      method: 'POST',
      headers: { 'Content-Type':'application/json', ...authHeaders() },
      body: JSON.stringify({
        mode: 's3',
        source: src.id,
        payload: { bucket: s3.bucket, prefix: s3.prefix, sync: s3.sync }
      })
    })
    const job = await jobRes.json()
    if (!jobRes.ok) throw new Error(job?.detail || 'Job create failed')
    statusMsg.value = '✅ S3 import queued'
    setTimeout(onClose, 900)
  } catch (e) {
    statusMsg.value = `❌ ${e.message || e}`
  }
}

const createGenericSource = async () => {
  statusMsg.value = ''
  try {
    const kind = activeTab.value
    const res = await fetch(`${API_BASE_URL}/api/ingest/sources/`, {
      method: 'POST',
      headers: { 'Content-Type':'application/json', ...authHeaders() },
      body: JSON.stringify({ kind, name: generic.name, config: {} })
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data?.detail || 'Source create failed')
    statusMsg.value = '✅ Source created'
    setTimeout(onClose, 900)
  } catch (e) {
    statusMsg.value = `❌ ${e.message || e}`
  }
}

const onClose = () => { closeImportWizard() }

onMounted(() => {
  if (bus.preset?.tab) activeTab.value = bus.preset.tab
})
</script>

<style scoped>
.iw-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.35); display: grid; place-items: center; z-index: 9999; }
.iw-modal { width: min(860px, 96vw); background: #fff; border-radius: 14px; border: 1px solid #e6ecf7; box-shadow: 0 16px 48px rgba(30,64,175,.15); }
.iw-head { display: flex; justify-content: space-between; align-items: center; padding: 12px 14px; border-bottom: 1px solid #eef3ff; }
.iw-head h3 { margin: 0; font-size: 1.1rem; color: #1f2a44; }
.iw-head .x { border: none; background: #fff; border-radius: 8px; padding: 4px 8px; cursor: pointer; }
.iw-tabs { display: flex; gap: 6px; padding: 10px 12px; border-bottom: 1px solid #eef3ff; overflow-x: auto; }
.tab { border: 1px solid #dbe3f3; background: #fff; padding: 6px 10px; border-radius: 8px; cursor: pointer; font-weight: 600; }
.tab.active { background: #eaf2ff; color: #1d4ed8; border-color: #c7dafb; }
.iw-body { padding: 14px; }
.pane { display: grid; gap: 10px; }
.hint { color: #607d8b; font-size: .9rem; }
.row { display: grid; gap: 6px; }
.row input[type="text"], .row input[type="number"], .row input[type="url"], .row input:not([type]) { border: 1px solid #d6e0f5; border-radius: 8px; padding: 9px 12px; background: #f7faff; }
.actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 6px; }
.btn { border: 1px solid #bcd1ff; background: #fff; color: #1e40af; font-weight: 700; border-radius: 8px; padding: 9px 12px; cursor: pointer; }
.status { padding: 10px 14px; color: #1f2a44; }
.iw-foot { border-top: 1px solid #eef3ff; }
.picked { list-style: disc; margin: 0 0 0 20px; padding: 0; color: #2f3b52; }
</style>
