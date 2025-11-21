<template>
  <div class="page">
    <header class="page-head">
      <div class="left">
        <button class="ghost" @click="goBack">← {{ backLabel }}</button>
        <h1 class="ttl">{{ doc?.title || doc?.filename || ('#'+id) }}</h1>
      </div>
      <div class="right">
        <span class="badge" :class="statusClass(doc?.status)">{{ prettyStatus(doc?.status) }}</span>
      </div>
    </header>

    <section class="meta" v-if="doc">
      <div class="row">
        <div class="label">{{ $t ? $t('title') : 'Title' }}</div>
        <div class="val">{{ doc.title || doc.filename }}</div>
      </div>
      <div class="row">
        <div class="label">ID</div>
        <div class="val">{{ doc.id }}</div>
      </div>
      <div class="row">
        <div class="label">{{ $t ? $t('imported') : 'Imported' }}</div>
        <div class="val">{{ fmtDate(doc.created_at) }}</div>
      </div>
      <div class="row" v-if="sourceUrl">
        <div class="label">URL</div>
        <div class="val"><a :href="sourceUrl" target="_blank" rel="noopener">{{ sourceUrl }}</a></div>
      </div>
    </section>

    <!-- References panel removed per request; focus on exact PDF location only -->

    <section class="viewer" v-if="pdfUrl">
      <h3 class="vr-title">PDF</h3>
      <component :is="usePdfJs ? PdfJsViewer : 'iframe'"
                 class="pdf-viewer"
                 v-bind="viewerBindings"
                 title="Document PDF" />
    </section>
  </div>
  
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { API_BASE_URL } from '../config'
import { authFetch } from '../lib/authFetch'
import PdfJsViewer from '../components/PdfJsViewer.vue'

const route = useRoute()
const router = useRouter()
const id = computed(() => route.params?.id)
const doc = ref(null)
const references = ref([])
const loading = ref(true)

const sourceUrl = computed(() => {
  try { return (doc.value?.steps_json || {}).source_url || '' } catch { return '' }
})
const isUploadedDoc = computed(() => !sourceUrl.value)
const documentFileUrl = computed(() => {
  try {
    return doc.value?.id ? `${API_BASE_URL}/api/documents/${doc.value.id}/file` : ''
  } catch {
    return ''
  }
})

const pdfUrl = computed(() => {
  try{
    const toAbs = (u) => {
      if (!u) return ''
      if (/^https?:/i.test(u)) return u
      if (u.startsWith('/')) return `${API_BASE_URL}${u}`
      return `${API_BASE_URL}/${u}`
    }
    const urlQ = route.query?.url
    if (urlQ) return toAbs(urlQ)
    if (isUploadedDoc.value && documentFileUrl.value) {
      return documentFileUrl.value
    }
    const f = doc.value?.file_url
    if (f) return toAbs(f)
    if (doc.value?.id && documentFileUrl.value) {
      return documentFileUrl.value
    }
    const src = sourceUrl.value
    if (src && /\.pdf(\?|#|$)/i.test(src)) return src
  }catch(_){ }
  return ''
})
const pageParam = computed(() => {
  try { const p = parseInt(route.query?.p, 10); return Number.isFinite(p) && p>0 ? p : null } catch { return null }
})
// Highlight term: accept ?h=... or fallback to ?q=...
const highlightTerm = computed(() => {
  try {
    const h = String(route.query?.h || route.query?.q || '').trim()
    return h || ''
  } catch { return '' }
})
const viewerSrc = computed(() => {
  const base = pdfUrl.value
  if (!base) return ''
  // Append access token for iframe (no headers in iframe requests)
  try {
    const access = localStorage.getItem('token') || localStorage.getItem('access') || ''
    if (access && base.startsWith(API_BASE_URL)){
      const sep = base.includes('?') ? '&' : '?'
      const withTok = `${base}${sep}access=${encodeURIComponent(access)}`
      // Build anchor with optional page and search (many PDF viewers support #search=...)
      const parts = []
      if (pageParam.value) parts.push(`page=${pageParam.value}`)
      if (highlightTerm.value) parts.push(`search=${encodeURIComponent(highlightTerm.value)}`)
      if (parts.length) return `${withTok}#${parts.join('&')}`
      return withTok
    }
  } catch(_) { /* ignore */ }
  if (pageParam.value || highlightTerm.value){
    const parts = []
    if (pageParam.value) parts.push(`page=${pageParam.value}`)
    if (highlightTerm.value) parts.push(`search=${encodeURIComponent(highlightTerm.value)}`)
    return `${base}#${parts.join('&')}`
  }
  return base
})
const viewerSrcPlain = computed(() => String(viewerSrc.value || '').split('#')[0])
const usePdfJs = computed(() => {
  try {
    if (isUploadedDoc.value) return false
    return viewerSrcPlain.value.startsWith(API_BASE_URL)
  } catch { return false }
})
const viewerBindings = computed(() => {
  if (usePdfJs.value) {
    return {
      src: viewerSrcPlain.value,
      page: pageParam.value || 1,
      query: highlightTerm.value || '',
      highlightColor: '#ff4d4f',
      style: 'width: 100%; height: auto; display: block; border:none; border-radius:10px; overflow:auto; max-height: calc(100vh - 280px); background:#0b1022;'
    }
  }
  return { src: viewerSrc.value }
})

function prettyStatus(s){ if(!s) return ''; const v=String(s).toUpperCase(); return v==='READY'?'Imported': v[0]+v.slice(1).toLowerCase() }
function statusClass(s){ const v=String(s||'').toLowerCase(); if(['queued','running','processing'].includes(v)) return 'processing'; if(['ready','partial_ready','success','imported'].includes(v)) return 'imported'; if(['failed','cancelled','deleted','error'].includes(v)) return 'failed'; return 'uploaded' }
function fmtDate(iso){ try{ return new Date(iso).toLocaleDateString() }catch{ return '' } }
function fmtDateTime(iso){ try{ const d=new Date(iso); return d.toLocaleString() }catch{ return iso } }
function asDocList(payload){
  if (!payload) return []
  if (Array.isArray(payload?.results)) return payload.results
  if (Array.isArray(payload)) return payload
  if (Array.isArray(payload?.documents)) return payload.documents
  return []
}

async function load(){
  let r
  try { r = await authFetch(`${API_BASE_URL}/api/documents/${id.value}`) } catch { r = null }
  if (r && r.ok){
    const data = await r.json()
    if (data && data.document) { doc.value = data.document; references.value = data.references || [] }
    else { doc.value = data; references.value = [] }
    loading.value = false
    return
  }
  // Fallbacks: by title hint (?t=) and by broader content list
  const titleQ = (route.query?.t || '').toString().toLowerCase()
  if (titleQ){
    // Use dedicated find endpoint first
    try{
      const rf = await authFetch(`${API_BASE_URL}/api/documents/find?title=${encodeURIComponent(titleQ)}`)
      if (rf.ok){
        doc.value = await rf.json()
        references.value = []
        loading.value = false
        return
      }
    }catch(_){ /* ignore */ }
    try{
      const r2 = await authFetch(`${API_BASE_URL}/api/documents?limit=500&sort=-created_at`)
      if (r2.ok){
        const arr = asDocList(await r2.json())
        const hit = (arr||[]).find(d => String(d.title||d.filename||'').toLowerCase().includes(titleQ))
        if (hit){ doc.value = hit; references.value = [] }
      }
    }catch(_){ /* ignore */ }
  }
  if (!doc.value){
    try{
      const r3 = await authFetch(`${API_BASE_URL}/api/content?limit=500&sort=-status_updated_at`)
      if (r3.ok){
        const arr = await r3.json()
        const hit = (arr||[]).find(d => String(d.title||d.filename||'').toLowerCase().includes(titleQ))
        if (hit){ doc.value = hit; references.value = [] }
      }
    }catch(_){ /* ignore */ }
  }
  // Last chance: load most recent document
  if (!doc.value){
    try {
      const r4 = await authFetch(`${API_BASE_URL}/api/documents?limit=1&sort=-created_at`)
      if (r4.ok){
        const arr = asDocList(await r4.json())
        if (Array.isArray(arr) && arr.length){ doc.value = arr[0] }
      }
    } catch(_) { /* ignore */ }
  }
  // If still not found, go back to listing
  if (!doc.value) {
    try { router.replace('/documents') } catch(_) {}
  }
  // Normalize URL to the resolved doc id to avoid stale 404s
  try {
    if (doc.value && String(route.params?.id) !== String(doc.value.id)){
      const q = new URLSearchParams(location.search)
      router.replace({ path: `/documents/${doc.value.id}`, query: Object.fromEntries(q.entries()) })
    }
  } catch(_) { /* ignore */ }
  loading.value = false
}

const backLabel = computed(() => route.query?.fromThread ? 'History' : 'Documents')
function goBack(){
  const fromT = route.query?.fromThread
  const fromM = route.query?.fromMessage
  if (fromT) {
    const q = fromM ? `?m=${encodeURIComponent(String(fromM))}` : ''
    router.push(`/analysis/${fromT}${q}`)
    return
  }
  router.push('/documents')
}

onMounted(load)
// If navigating between /documents/:id with the same component instance, reload
watch(() => route.params?.id, () => { try { load() } catch(_){} })
</script>

<style scoped>
.page{ background:var(--bg); min-height:100vh; padding: 10px 12px; }
.page-head{ margin:12px 0; display:flex; align-items:center; justify-content:space-between; gap:12px; }
.left{ display:flex; align-items:center; gap:10px; }
.ghost{ border:1px solid var(--line); background:var(--card); color:var(--blue); border-radius:10px; padding:8px 10px; font-weight:800; cursor:pointer; }
.ttl{ margin:0; font-size:20px; font-weight:900; color:var(--txt); }
.badge{ padding:4px 10px; border-radius:999px; font-size:12px; font-weight:800; border:1px solid transparent; }
.badge.imported{ background:#e6fcf0; color:#067647; border-color:#98f1b7; }
.badge.processing{ background:#eaf2ff; color:#1d4ed8; border-color:#c7dafb; }
.badge.uploaded{ background:#fff0da; color:#9a6700; border-color:#ffd89a; }
.badge.failed{ background:#fef3f2; color:#b42318; border-color:#f9c2bf; }

.meta{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:12px; box-shadow: var(--md-shadow-1); }
.row{ display:grid; grid-template-columns: 140px 1fr; gap:8px; padding:6px 0; border-bottom:1px dashed var(--line); }
.row:last-child{ border-bottom:none; }
.label{ color:var(--muted); font-weight:700; }
.val a{ color:var(--blue); text-decoration:none; }
.val a:hover{ text-decoration:underline; }

.refs{ margin-top:12px; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:12px; box-shadow: var(--md-shadow-1); }
.refs-head{ display:flex; align-items:center; justify-content:space-between; margin-bottom:6px; }
.refs-head h3{ margin:0; font-size:16px; font-weight:900; color:var(--txt); }
.count{ background:#eef2ff; color:var(--blue); border:1px solid #c7dafb; border-radius:999px; padding:2px 8px; font-size:12px; font-weight:800; }
.empty{ color:var(--muted); padding:8px 0; }
.ref-list{ display:grid; gap:10px; }
.ref-item{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:10px; }
.ref-top{ display:flex; justify-content:space-between; align-items:center; margin-bottom:4px; color:var(--muted); }
.snippet{ white-space:pre-wrap; color:var(--txt); margin-bottom:8px; }
.link{ background:transparent; border:none; color:var(--blue); font-weight:800; cursor:pointer; padding:0; text-decoration:none; }
.link:hover{ text-decoration:underline; }
.sources-list{ display:grid; gap:8px; }
.src-chip{ display:flex; align-items:center; flex-wrap:wrap; gap:8px; background:var(--card); border:1px solid var(--line); border-radius:10px; padding:6px 8px; }
.src-title{ font-weight:800; color:var(--txt); }
.src-meta{ color:var(--muted); }

.viewer{ margin-top:12px; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:12px; box-shadow: var(--md-shadow-1); }
.vr-title{ margin:0 0 8px; font-size:16px; font-weight:900; color:var(--txt); }
.pdf-viewer{ width:100%; max-height: calc(100vh - 280px); border:none; border-radius:10px; background:#000; overflow:auto; display:block; }
</style>
