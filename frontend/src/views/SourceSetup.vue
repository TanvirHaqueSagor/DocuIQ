<template>
  <div class="setup-wrap">
    <header class="head">
      <div class="title">
        <span class="ico">{{ schema.emoji }}</span>
        <div class="tt">
          <h1>{{ schema.title }}</h1>
          <p class="sub">{{ schema.description }}</p>
        </div>
      </div>
      <button class="ghost" @click="goBack">← Back</button>
    </header>

    <section class="card">
      <!-- Files special flow -->
      <div v-if="kind === 'files' || ['video','audio','image'].includes(kind)" class="pane">
        <div class="row">
          <label>Files</label>
          <input type="file" multiple @change="onPickFiles" />
          <ul class="picked" v-if="pickedFiles.length">
            <li v-for="f in pickedFiles" :key="f.name">{{ f.name }} ({{ f.size }}B)</li>
          </ul>
        </div>
        <div class="row">
          <label>Title <span class="muted">(optional)</span></label>
          <input v-model="filesForm.title" placeholder="e.g. Annual Report 2025" />
        </div>
        <div class="row">
          <label>Tags <span class="muted">(optional)</span></label>
          <input v-model="filesForm.tags" placeholder="comma,separated,tags" />
        </div>
        <div class="row">
          <label>Language <span class="muted">(optional)</span></label>
          <input v-model="filesForm.language" placeholder="e.g. en, bn, ja" />
        </div>
        <div class="actions">
          <button class="primary" :disabled="!pickedFiles.length || loading" @click="startFileImport">
            {{ loading ? 'Importing…' : 'Start import' }}
          </button>
        </div>
        <div class="status" v-if="statusMsg">{{ statusMsg }}</div>
      </div>

      <!-- Generic source setup -->
      <div v-else class="pane">
        <div class="row">
          <label>Connection name</label>
          <input v-model="name" placeholder="e.g. {{ schema.title }}" />
        </div>

        <div v-for="f in schema.fields" :key="f.key" class="row">
          <label>{{ f.label }} <span v-if="!f.required" class="muted">(optional)</span></label>
          <template v-if="f.type==='text' || f.type==='url' || f.type==='password' || f.type==='number'">
            <input :type="f.type==='password' ? 'password' : (f.type==='number' ? 'number' : 'text')"
                   v-model="config[f.key]"
                   :placeholder="f.placeholder || ''" />
          </template>
          <template v-else-if="f.type==='textarea'">
            <textarea v-model="config[f.key]" :placeholder="f.placeholder || ''" rows="4"></textarea>
          </template>
          <template v-else-if="f.type==='select'">
            <select v-model="config[f.key]">
              <option v-for="opt in f.options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
          </template>
          <template v-else-if="f.type==='multi'">
            <input v-model="config[f.key]" :placeholder="f.placeholder || 'comma,separated'" />
            <small class="hint">Comma separated</small>
          </template>
          <template v-else-if="f.type==='checkbox'">
            <label><input type="checkbox" v-model="config[f.key]" /> {{ f.help || '' }}</label>
          </template>
          <template v-else-if="f.type==='date'">
            <input type="date" v-model="config[f.key]" />
          </template>
          <template v-else-if="f.type==='json'">
            <textarea v-model="config[f.key]" placeholder="{\n  &quot;param&quot;: &quot;value&quot;\n}"></textarea>
            <small class="hint">Paste JSON; validated on save</small>
          </template>
          <template v-else-if="f.type==='oauth'">
            <div class="oauth-box">
              <button class="btn" @click="fakeOauth(f.provider)">{{ oauthConnected ? 'Reconnect' : 'Connect' }} {{ f.provider }}</button>
              <span class="muted" v-if="oauthConnected">Connected</span>
            </div>
          </template>
        </div>

        <div class="actions">
          <button class="ghost" :disabled="loading" @click="saveSource(false)">Save source</button>
          <button class="primary" :disabled="loading || !name" @click="saveSource(true)">{{ loading ? 'Saving…' : 'Save & run' }}</button>
        </div>
        <div class="status" v-if="statusMsg">{{ statusMsg }}</div>
      </div>
    </section>
  </div>
  
</template>

<script setup>
import { ref, computed, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { API_BASE_URL } from '../config'
import { authFetch } from '../lib/authFetch'

const route = useRoute()
const router = useRouter()
const kind = computed(() => String(route.params.kind || 'files').toLowerCase())

const name = ref('')
const config = reactive({})
const loading = ref(false)
const statusMsg = ref('')
const oauthConnected = ref(false)

const pickedFiles = ref([])
const filesForm = reactive({ title:'', tags:'', language:'' })
const onPickFiles = e => { pickedFiles.value = Array.from(e.target.files || []) }

const ensureAuth = () => {
  const t = localStorage.getItem('token') || localStorage.getItem('access')
  if (!t || t.indexOf('.') === -1) {
    const r = encodeURIComponent(route.fullPath)
    router.replace(`/login?redirect=${r}`)
    throw new Error('Auth required')
  }
  return t
}
const authHeaders = () => ({ Authorization: `Bearer ${ensureAuth()}` })

const goBack = () => router.back()

const fakeOauth = (provider) => {
  oauthConnected.value = true
  // In MVP, let users paste tokens into config fields; full OAuth to follow
}

const startFileImport = async () => {
  ensureAuth()
  if (!pickedFiles.value.length) return
  loading.value = true
  statusMsg.value = ''
  try {
    const fd = new FormData()
    for (const f of pickedFiles.value) fd.append('files', f)
    const up = await authFetch(`${API_BASE_URL}/api/ingest/upload/`, { method:'POST', headers: { ...authHeaders() }, body: fd })
    const text = await up.text(); let list = []
    try { list = JSON.parse(text) } catch { throw new Error(text.slice(0,180)) }
    if (!up.ok) throw new Error(list?.detail || 'Upload failed')
    const file_ids = Array.isArray(list) ? list.map(x => x.id) : []
    const filenames = Array.isArray(list) ? list.map(x => x.name) : []
    if (!file_ids.length) throw new Error('No file ids returned')
    const payload = { file_ids, filenames, title: filesForm.title, tags: filesForm.tags, language: filesForm.language }
    const j = await authFetch(`${API_BASE_URL}/api/ingest/jobs/`, { method:'POST', headers: { 'Content-Type':'application/json', ...authHeaders() }, body: JSON.stringify({ mode:'upload', payload }) })
    const jd = await j.json(); if(!j.ok) throw new Error(jd?.detail||'Job create failed')
    statusMsg.value = '✅ Import queued'
    setTimeout(() => router.replace('/documents'), 900)
  } catch (e) {
    statusMsg.value = `❌ ${e.message || e}`
  } finally { loading.value = false }
}

const saveSource = async (runAfter) => {
  ensureAuth()
  loading.value = true
  statusMsg.value = ''
  try {
    let configOut = {}
    // Try to parse any JSON-y fields
    for (const [k,v] of Object.entries(config)) {
      if (typeof v === 'string' && v.trim().startsWith('{')) {
        try { configOut[k] = JSON.parse(v) } catch { configOut[k] = v }
      } else {
        configOut[k] = v
      }
    }
    const res = await authFetch(`${API_BASE_URL}/api/ingest/sources/`, { method:'POST', headers: { 'Content-Type':'application/json', ...authHeaders() }, body: JSON.stringify({ kind: kind.value, name: name.value || schema.value.title, config: configOut }) })
    const src = await res.json(); if(!res.ok) throw new Error(src?.detail || 'Source create failed')
    if (runAfter) {
      const job = await authFetch(`${API_BASE_URL}/api/ingest/jobs/`, { method:'POST', headers: { 'Content-Type':'application/json', ...authHeaders() }, body: JSON.stringify({ mode: kind.value, source: src.id, payload: configOut }) })
      const jd = await job.json(); if(!job.ok) throw new Error(jd?.detail || 'Job create failed')
    }
    statusMsg.value = runAfter ? '✅ Saved & queued' : '✅ Source saved'
    setTimeout(() => router.replace('/documents'), 900)
  } catch (e) {
    statusMsg.value = `❌ ${e.message || e}`
  } finally { loading.value = false }
}

const schemaFor = (k) => {
  const base = (title, emoji, description, fields=[]) => ({ title, emoji, description, fields })
  switch(k){
    case 'web':
      return base('Website', '🌐', 'Scrape/crawl a website', [
        { key:'url', label:'URL', type:'url', required:true, placeholder:'https://example.com' },
        { key:'crawl', label:'Enable crawl', type:'checkbox', help:'Follow links' },
        { key:'depth', label:'Crawl depth', type:'number', placeholder:'1' },
        { key:'frequency', label:'Frequency', type:'select', options:[{value:'once',label:'One-time'},{value:'daily',label:'Daily'},{value:'weekly',label:'Weekly'}] },
      ])
    case 's3':
      return base('AWS S3', '🟦', 'Connect an S3 bucket/prefix', [
        { key:'bucket', label:'Bucket', type:'text', required:true },
        { key:'prefix', label:'Prefix', type:'text', placeholder:'folder/path/' },
        { key:'sync', label:'Keep in sync', type:'checkbox', help:'Auto-sync folder' },
      ])
    case 'gdrive':
      return base('Google Drive', '🟩', 'Authorize access to your Drive', [
        { key:'oauth', label:'Authorization', type:'oauth', provider:'Google' },
        { key:'folder_id', label:'Folder or File ID', type:'text' },
        { key:'scope', label:'Scope', type:'select', options:[{value:'readonly',label:'Read-only'},{value:'full',label:'Full sync'}] },
        { key:'frequency', label:'Sync', type:'select', options:[{value:'manual',label:'Manual'},{value:'daily',label:'Daily'},{value:'realtime',label:'Real-time'}] },
      ])
    case 'dropbox':
      return base('Dropbox', '🟦', 'Connect Dropbox', [
        { key:'oauth', label:'Authorization', type:'oauth', provider:'Dropbox' },
        { key:'folder_path', label:'Folder path', type:'text' },
        { key:'scope', label:'Scope', type:'select', options:[{value:'readonly',label:'Read-only'},{value:'full',label:'Full sync'}] },
        { key:'frequency', label:'Sync', type:'select', options:[{value:'manual',label:'Manual'},{value:'daily',label:'Daily'}] },
      ])
    case 'onedrive':
      return base('OneDrive', '🟦', 'Connect OneDrive', [
        { key:'oauth', label:'Authorization', type:'oauth', provider:'Microsoft' },
        { key:'folder_id', label:'Folder or File ID', type:'text' },
        { key:'scope', label:'Scope', type:'select', options:[{value:'readonly',label:'Read-only'},{value:'full',label:'Full sync'}] },
      ])
    case 'box':
      return base('Box', '📦', 'Connect Box storage', [
        { key:'oauth', label:'Authorization', type:'oauth', provider:'Box' },
        { key:'folder_id', label:'Folder or File ID', type:'text' },
      ])
    case 'sharepoint':
      return base('SharePoint', '🏢', 'Connect SharePoint site', [
        { key:'site_url', label:'Site URL', type:'url', required:true },
        { key:'oauth', label:'Authorization', type:'oauth', provider:'Microsoft' },
        { key:'library', label:'Library/Folder', type:'text' },
      ])
    case 'confluence':
      return base('Confluence', '📘', 'Connect Atlassian Confluence', [
        { key:'site_url', label:'Site URL', type:'url', required:true },
        { key:'api_token', label:'API Token (or OAuth)', type:'password' },
        { key:'space_key', label:'Space Key', type:'text' },
        { key:'page_id', label:'Page ID (optional)', type:'text' },
      ])
    case 'notion':
      return base('Notion', '⬛', 'Connect Notion workspace', [
        { key:'oauth', label:'Authorization', type:'oauth', provider:'Notion' },
        { key:'workspace_id', label:'Workspace ID', type:'text' },
        { key:'database_id', label:'Database/Page ID', type:'text' },
      ])
    case 'airtable':
      return base('Airtable', '📋', 'Connect Airtable', [
        { key:'api_key', label:'API Key', type:'password' },
        { key:'base_id', label:'Base ID', type:'text' },
        { key:'table', label:'Table', type:'text' },
      ])
    case 'gmail':
    case 'outlook':
      return base(k==='gmail'?'Gmail':'Outlook', '✉️', 'Index emails', [
        { key:'oauth', label:'Authorization', type:'oauth', provider: k==='gmail'?'Google':'Microsoft' },
        { key:'mailbox', label:'Mailbox/Label', type:'text' },
        { key:'date_from', label:'Date from', type:'date' },
        { key:'date_to', label:'Date to', type:'date' },
        { key:'keywords', label:'Keywords', type:'text' },
      ])
    case 'slack':
      return base('Slack', '🟩', 'Index Slack messages and files', [
        { key:'oauth', label:'Authorization', type:'oauth', provider:'Slack' },
        { key:'workspace_id', label:'Workspace ID', type:'text' },
        { key:'channels', label:'Channels', type:'multi', placeholder:'#general,#random' },
        { key:'date_from', label:'Date from', type:'date' },
        { key:'date_to', label:'Date to', type:'date' },
        { key:'types', label:'Types', type:'multi', placeholder:'messages,files,threads' },
      ])
    case 'teams':
      return base('Microsoft Teams', '🟦', 'Index Teams chats/files', [
        { key:'oauth', label:'Authorization', type:'oauth', provider:'Microsoft' },
        { key:'tenant_id', label:'Tenant/Workspace ID', type:'text' },
        { key:'channels', label:'Channels', type:'multi' },
      ])
    case 'zoom':
      return base('Zoom', '🎥', 'Index meeting recordings/transcripts', [
        { key:'oauth', label:'Authorization', type:'oauth', provider:'Zoom' },
        { key:'meeting_ids', label:'Meeting IDs', type:'multi' },
        { key:'date_from', label:'Date from', type:'date' },
        { key:'date_to', label:'Date to', type:'date' },
      ])
    case 'github':
    case 'gitlab':
      return base(k==='github'?'GitHub':'GitLab', '💻', 'Index repository issues/PRs/wiki', [
        { key:'token', label:'Personal Access Token', type:'password', required:true },
        { key:'repo', label:'Repository (name or URL)', type:'text', required:true },
        { key:'scope', label:'Data scope', type:'multi', placeholder:'issues,prs,commits,wiki,discussions' },
        { key:'branch', label:'Branch/Tag', type:'text' },
      ])
    case 'jira':
      return base('Jira', '🟦', 'Index Jira issues', [
        { key:'site_url', label:'Site URL', type:'url', required:true },
        { key:'api_token', label:'API Token / OAuth', type:'password' },
        { key:'project', label:'Project/Board ID', type:'text' },
        { key:'jql', label:'JQL filter', type:'text' },
      ])
    case 'trello':
      return base('Trello', '🗂️', 'Index Trello boards', [
        { key:'api_key', label:'API Key', type:'password' },
        { key:'token', label:'Token', type:'password' },
        { key:'board_id', label:'Board ID', type:'text' },
      ])
    case 'postgres':
    case 'mysql':
      return base(k==='postgres'?'PostgreSQL':'MySQL', '🗄️', 'Index from database', [
        { key:'host', label:'Host', type:'text', required:true },
        { key:'port', label:'Port', type:'number', placeholder: k==='postgres'?'5432':'3306' },
        { key:'database', label:'Database name', type:'text', required:true },
        { key:'username', label:'Username', type:'text' },
        { key:'password', label:'Password', type:'password' },
        { key:'ssl', label:'Use SSL', type:'checkbox' },
        { key:'table', label:'Table name(s)', type:'text' },
        { key:'query', label:'Custom SQL (optional)', type:'textarea' },
      ])
    case 'mongodb':
      return base('MongoDB', '🍃', 'Index from MongoDB', [
        { key:'connection', label:'Connection string', type:'text', required:true },
        { key:'database', label:'Database', type:'text' },
        { key:'collection', label:'Collection', type:'text' },
        { key:'query', label:'Query (JSON)', type:'json' },
      ])
    case 'snowflake':
      return base('Snowflake', '❄️', 'Index from Snowflake', [
        { key:'connection', label:'Connection', type:'text' },
        { key:'account', label:'Account', type:'text' },
        { key:'user', label:'User', type:'text' },
        { key:'warehouse', label:'Warehouse', type:'text' },
        { key:'database', label:'Database', type:'text' },
        { key:'schema', label:'Schema', type:'text' },
        { key:'sql', label:'SQL', type:'textarea' },
      ])
    case 'bigquery':
      return base('BigQuery', '🟨', 'Index from BigQuery', [
        { key:'service_key', label:'Service key JSON', type:'json' },
        { key:'project_id', label:'Project ID', type:'text' },
        { key:'dataset', label:'Dataset', type:'text' },
        { key:'table', label:'Table', type:'text' },
        { key:'sql', label:'SQL (optional)', type:'textarea' },
      ])
    case 'elasticsearch':
      return base('Elasticsearch', '🔍', 'Index from Elasticsearch', [
        { key:'url', label:'Cluster URL', type:'url' },
        { key:'index', label:'Index', type:'text' },
        { key:'query', label:'Query (JSON)', type:'json' },
      ])
    case 'rss':
      return base('RSS Feeds', '📰', 'Subscribe to RSS/Atom feeds', [
        { key:'urls', label:'Feed URLs', type:'textarea', placeholder:'One per line' },
        { key:'frequency', label:'Frequency', type:'select', options:[{value:'hourly',label:'Hourly'},{value:'daily',label:'Daily'}] },
      ])
    case 'api':
      return base('Custom API', '🔗', 'Pull from JSON API', [
        { key:'url', label:'Endpoint URL', type:'url', required:true },
        { key:'api_key', label:'API Key', type:'password' },
        { key:'params', label:'Query params (JSON)', type:'json' },
        { key:'frequency', label:'Frequency', type:'select', options:[{value:'manual',label:'Manual'},{value:'hourly',label:'Hourly'}] },
      ])
    case 'bloomberg':
    case 'refinitiv':
    case 'esg':
      return base(k==='bloomberg'?'Bloomberg':(k==='refinitiv'?'Refinitiv':'ESG API'), '📈', 'Financial/ESG data', [
        { key:'api_key', label:'API Key', type:'password' },
        { key:'dataset', label:'Dataset/Tickers', type:'text' },
        { key:'params', label:'Params (JSON)', type:'json' },
      ])
    case 'linkedin':
    case 'twitter':
      return base(k==='linkedin'?'LinkedIn':'Twitter (X)', '🔮', 'Social feeds', [
        { key:'oauth', label:'Authorization', type:'oauth', provider: k==='linkedin'?'LinkedIn':'Twitter' },
        { key:'handles', label:'Account handles', type:'multi', placeholder:'@company,@ceo' },
        { key:'date_from', label:'Date from', type:'date' },
        { key:'date_to', label:'Date to', type:'date' },
      ])
    case 'gcal':
      return base('Google Calendar', '📆', 'Calendar events', [
        { key:'oauth', label:'Authorization', type:'oauth', provider:'Google' },
        { key:'calendar', label:'Calendar', type:'text' },
        { key:'keywords', label:'Event keywords', type:'text' },
      ])
    case 'figma':
      return base('Figma', '🎨', 'Design files metadata', [
        { key:'api_key', label:'API Key / OAuth', type:'password' },
        { key:'file_id', label:'File/Project ID', type:'text' },
        { key:'frames', label:'Frame selection', type:'text' },
      ])
    default:
      return base(k.toUpperCase(), '🔗', 'Configure your source', [])
  }
}

const schema = computed(() => schemaFor(kind.value))

onMounted(() => {
  // Default connection name
  name.value = `${schema.value.title}`
})
</script>

<style scoped>
.setup-wrap{ width:min(900px,94%); margin:18px auto; display:grid; gap:12px; }
.head{ display:flex; align-items:center; justify-content:space-between; }
.title{ display:flex; align-items:center; gap:10px; }
.ico{ font-size:28px; }
.tt h1{ margin:0; font-size:22px; }
.tt .sub{ margin:4px 0 0; color:#64748b; font-size:13px; }
.ghost{ border:1px solid #dbe3f3; background:#fff; color:#1f47c5; border-radius:10px; padding:8px 10px; font-weight:800; cursor:pointer; }
.card{ background:#fff; border:1px solid #e6ecf7; border-radius:12px; padding:12px; }
.pane{ display:grid; gap:10px; }
.row{ display:grid; gap:6px; }
input, select, textarea{ border:1px solid #d6e0f5; border-radius:8px; padding:9px 12px; background:#f7faff; }
textarea{ min-height:90px; }
.muted{ color:#6b7280; font-size:12px; }
.hint{ color:#6b7280; font-size:12px; }
.actions{ display:flex; gap:8px; justify-content:flex-end; margin-top:6px; }
.primary{ border:none; background:#1f47c5; color:#fff; font-weight:800; border-radius:10px; padding:9px 12px; cursor:pointer; }
.btn{ border:1px solid #bcd1ff; background:#fff; color:#1e40af; font-weight:700; border-radius:8px; padding:6px 10px; cursor:pointer; }
.status{ padding:8px 0; color:#1f2a44; }
.picked{ list-style:disc; margin:0 0 0 18px; padding:0; color:#2f3b52; }
</style>
