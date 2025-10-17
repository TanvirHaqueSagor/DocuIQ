<template>
  <div class="page">
    

    <!-- Chat area -->
    <section class="chat">
      <div ref="chatBody" class="chat-body">
        <div v-if="!messages.length" class="welcome">
          <div class="w-examples">
            <button class="example" @click="useExample($t ? $t('ex1') : 'Summarize the latest policy changes and list key points.')">{{ $t ? $t('ex1') : 'Summarize the latest policy changes and list key points.' }}</button>
            <button class="example" @click="useExample($t ? $t('ex2') : 'What are the onboarding steps and who approves them?')">{{ $t ? $t('ex2') : 'What are the onboarding steps and who approves them?' }}</button>
            <button class="example" @click="useExample($t ? $t('ex3') : 'Compare Q2 revenue growth across product lines with sources.')">{{ $t ? $t('ex3') : 'Compare Q2 revenue growth across product lines with sources.' }}</button>
          </div>
        </div>

        <div v-for="m in messages" :key="m.id" class="msg" :class="m.role" :data-mid="m.id">
          <div class="bubble">
            <div v-if="m.thinking && hasAnyUserMessage()" class="typing" aria-live="polite" aria-label="Thinking">
              <span class="dot"></span><span class="dot"></span><span class="dot"></span>
            </div>
            <template v-else>
            <div class="content" v-html="renderAnswer(m)"></div>
            <div v-if="isValidAnswer(m) && !hasInlineMarkers(m) && fallbackInline(m).length" class="inline-fallback">
              <template v-for="(s, i) in fallbackInline(m)" :key="i">
                <RouterLink v-if="s.type==='doc'" class="src-inline" :to="s.href">Source<span v-if="s.page"> p. {{ s.page }}</span></RouterLink>
              </template>
            </div>
            </template>
          </div>
        </div>
      </div>

      <!-- Composer (ChatGPT-like) -->
      <div class="composer">
        <div class="comp-inner">
          <textarea
            ref="composerInput"
            v-model="q"
            class="comp-input"
            rows="1"
            :placeholder="$t ? $t('askSomething') : 'Ask across your documents and sources…'"
            @input="autoGrow"
            @keydown="onKeydown"
          ></textarea>
          <div class="comp-actions">
            <button class="send" :disabled="loading || !q.trim()" @click="send" :aria-label="$t ? $t('send') : 'Send'">
              {{ loading ? '…' : '↑' }}
            </button>
          </div>
        </div>
        <div v-if="error" class="comp-error">{{ error }}</div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { API_BASE_URL } from '../config'
import { authFetch } from '../lib/authFetch'

// Minimal icon set for citations
import icFile from '../assets/icons/file.svg'
import icWeb from '../assets/icons/web.svg'
import icS3 from '../assets/icons/S3.svg'
import icGdrive from '../assets/icons/gdrive.svg'
import icDropbox from '../assets/icons/dropbox.svg'
import icOnedrive from '../assets/icons/onedrive.svg'
import icBox from '../assets/icons/box.svg'

const router = useRouter()
const route = useRoute()
const { t } = useI18n ? useI18n() : { t: (s)=>s }
const q = ref('')
const loading = ref(false)
const error = ref('')
const messages = ref([])
const chatBody = ref(null)
const threadId = ref(null)
const composerInput = ref(null)
const sendOnEnter = ref(true)

// Basic kind→icon mapping used for rendering citations
const ICONS = { file: icFile, files: icFile, upload: icFile, web: icWeb, s3: icS3, gdrive: icGdrive, dropbox: icDropbox, onedrive: icOnedrive, box: icBox }
const iconForKind = (k) => ICONS[String(k||'').toLowerCase()] || icFile

// Prefer explicit AI URL; fall back to local ai_engine dev port
const AI = (import.meta.env.VITE_AI_URL && import.meta.env.VITE_AI_URL.trim()) || 'http://localhost:8001'

function normalizeCitations(data){
  const out = []
  const arr = data?.sources || data?.citations || data?.matches || data?.chunks || []
  if (Array.isArray(arr)) {
    for (const s of arr) {
      const meta = s.metadata || {}
      const chunkIdx = typeof meta.chunk === 'number' ? (meta.chunk + 1) : undefined
      out.push({
        title: s.title || s.document?.title || meta.title || s.name,
        label: s.label,
        url: s.url || meta.url,
        page: s.page || meta.page || chunkIdx,
        kind: (s.kind || meta.kind || s.source || '').toString().toLowerCase(),
        documentId: s.document_id || s.documentId || s.doc_id || s.id,
        score: s.score,
      })
    }
  } else if (data?.source) {
    out.push({ title: data.source, label: data.source })
  }
  // Deduplicate by documentId (fallback to title)
  const seen = new Set()
  const uniq = []
  for (const c of out) {
    const key = c.documentId || c.title || c.label || c.url || c.name || ''
    if (seen.has(key)) continue
    seen.add(key)
    uniq.push(c)
  }
  // Sort by score descending if present
  uniq.sort((a,b) => (b.score||0) - (a.score||0))
  return uniq
}

function linkForCitation(s, m){
  const id = s?.documentId || s?.document_id || ''
  const tid = threadId.value || route.params?.id
  const mid = (m && typeof m.id === 'string') ? m.id.replace(/^db-/, '') : ''
  const params = []
  if (tid) params.push(`fromThread=${encodeURIComponent(String(tid))}`)
  if (mid) params.push(`fromMessage=${encodeURIComponent(String(mid))}`)
  const baseQS = params.length ? ('?' + params.join('&')) : ''
  if (id) return `/documents/${encodeURIComponent(id)}${baseQS}`
  const label = s?.title || s?.label || ''
  if (label) return `/documents${baseQS ? (baseQS + '&') : '?'}q=${encodeURIComponent(label)}`
  return `/documents${baseQS}`
}

function scrollToMessage(dbId){
  try{
    const el = chatBody.value?.querySelector(`[data-mid="${CSS.escape(dbId)}"]`)
    if (el && typeof el.scrollIntoView === 'function') el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }catch(_){ /* ignore */ }
}

function scrollToBottom(){
  nextTick(() => {
    try { chatBody.value?.scrollTo({ top: chatBody.value.scrollHeight, behavior: 'smooth' }) } catch(_) {}
  })
}

function useExample(text){
  q.value = text
  send()
}

function goDocuments(){ router.push('/documents') }

async function send(){
  const text = (q.value||'').trim()
  if (!text || loading.value) return
  error.value = ''
  // Starting a brand new chat in root view: clear any stale messages
  if (!threadId.value && messages.value.length) {
    resetChat()
  }
  const id = Date.now() + '-' + Math.random().toString(36).slice(2)
  messages.value.push({ id, role:'user', content: text })
  q.value = ''
  scrollToBottom()
  loading.value = true
  // Show thinking placeholder
  const waitId = id + '-t'
  messages.value.push({ id: waitId, role:'assistant', thinking: true })
  scrollToBottom()
  try{
    // Ensure thread exists
    if (!threadId.value) {
      const title = text.split(/\s+/).slice(0, 8).join(' ')
      const r = await authFetch(`${API_BASE_URL}/api/chats/threads/`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title })
      })
      if (r.ok) {
        const data = await r.json()
        threadId.value = data?.id
        // Navigate to thread URL
        if (threadId.value) router.push(`/analysis/${threadId.value}`)
      }
    }
    // Save user message
    if (threadId.value) {
      try{
        await authFetch(`${API_BASE_URL}/api/chats/threads/${threadId.value}/messages/`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ role: 'user', content: text })
        })
      }catch(_){ /* ignore */ }
    }
    const res = await fetch(`${AI}/ask`, {
      method:'POST', headers:{ 'Content-Type':'application/json' },
      body: JSON.stringify({ question: text, top_k: 5, with_sources: true })
    })
    const textBody = await res.text()
    let data = {}
    try { data = textBody ? JSON.parse(textBody) : {} } catch { data = {} }
    if(!res.ok){
      const msg = data?.detail || data?.error || textBody || `HTTP ${res.status}`
      throw new Error(msg)
    }
    let output = data?.answer || data?.output || data?.result || ''
    let cites = normalizeCitations(data)
    const irefs = data?.inline_refs || {}
    if(!output && Array.isArray(data?.matches)){
      output = data.matches.slice(0,3).map(m => m.text || m.chunk || m.content || '').filter(Boolean).join('\n\n')
    }
    // Replace thinking placeholder with real answer
    const idxWait = messages.value.findIndex(x => x.id === waitId)
    const finalMsg = { id: id+'-a', role:'assistant', content: output || (data?.source ? `Source: ${data.source}` : '—'), citations: cites, inlineRefs: irefs }
    if (idxWait !== -1) messages.value.splice(idxWait, 1, finalMsg)
    else messages.value.push(finalMsg)
    // Save assistant message
    if (threadId.value) {
      try{
        await authFetch(`${API_BASE_URL}/api/chats/threads/${threadId.value}/messages/`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ role: 'assistant', content: output, citations: cites })
        })
      }catch(_){ /* ignore */ }
    }
  }catch(e){
    const msg = e?.message || 'Something went wrong'
    if (/Failed to fetch|NetworkError|TypeError: fetch/i.test(String(msg))) {
      error.value = `Cannot reach AI service at ${AI}/ask. Set VITE_AI_URL or start the AI engine.`
    } else {
      error.value = msg
    }
  }finally{
    // Remove thinking if still present
    const idxWait = messages.value.findIndex(x => x.id === waitId)
    if (idxWait !== -1 && messages.value[idxWait]?.thinking) messages.value.splice(idxWait, 1)
    loading.value = false
    scrollToBottom()
  }
}

// Load existing thread if route has :id
async function loadThread(id){
  if (!id) return
  try{
    const r = await authFetch(`${API_BASE_URL}/api/chats/threads/${id}/messages/`)
    if (r.ok) {
      const arr = await r.json()
      const serverMsgs = (arr || []).map(m => ({ id: 'db-'+m.id, role: m.role, content: m.content, citations: Array.isArray(m.citations) ? m.citations : [] }))
      // Build signatures for server messages to dedupe local optimistic ones
      const sig = (m) => `${m.role}|${(m.content||'').trim()}`
      const serverSigs = new Set(serverMsgs.map(sig))
      const localHasUser = (messages.value || []).some(y => typeof y?.id === 'string' && !y.id.startsWith('db-') && y.role==='user')
      const localMsgs = (messages.value || []).filter(x => {
        if (!(typeof x?.id === 'string' && !x.id.startsWith('db-'))) return false
        if (x.thinking) return localHasUser
        // drop local if same role+content exists on server
        return !serverSigs.has(sig(x))
      })
      messages.value = [...localMsgs, ...serverMsgs]
      threadId.value = id
      nextTick(() => scrollToBottom())
    }
  }catch(_){ /* ignore */ }
}

function hasAnyUserMessage(){
  try { return (messages.value||[]).some(m => m && m.role==='user') } catch { return false }
}

function resetChat(){
  messages.value = []
  threadId.value = null
  error.value = ''
}

onMounted(() => {
  // init send preference
  try { const v = localStorage.getItem('sendOnEnter'); if (v!==null) sendOnEnter.value = JSON.parse(v) } catch(_) {}
  // ensure composer grows to fit content
  nextTick(() => autoGrow())
  const tid = route.params?.id
  const mid = route.query?.m
  if (tid) {
    loadThread(String(tid)).then(() => { if (mid) scrollToMessage('db-'+String(mid)) })
  }
  else resetChat()
})

watch(() => route.params?.id, (n) => {
  if (n) {
    loadThread(String(n)).then(() => { const mid = route.query?.m; if (mid) scrollToMessage('db-'+String(mid)) })
  }
  else resetChat()
})

watch(() => route.query?.m, (n) => { if (n) scrollToMessage('db-'+String(n)) })

function autoGrow(){
  try{
    const el = composerInput.value
    if (!el) return
    el.style.height = 'auto'
    const max = 280
    el.style.height = Math.min(max, el.scrollHeight) + 'px'
  }catch(_){ /* ignore */ }
}

function onKeydown(e){
  if (e.key !== 'Enter') return
  // Allow Shift+Enter to insert newline
  if (e.shiftKey) return
  // If pref is Enter to send, send on Enter
  if (sendOnEnter.value && !e.ctrlKey && !e.metaKey) { e.preventDefault(); send(); return }
  // If pref is not Enter to send, require Ctrl/Cmd+Enter to send
  if (!sendOnEnter.value && (e.ctrlKey || e.metaKey)) { e.preventDefault(); send(); return }
}

const sendPrefLabel = computed(() => sendOnEnter.value ? (t('enterToSend') || 'Enter to send') : (t('ctrlEnterToSend') || 'Ctrl/Cmd+Enter to send'))
const sendPrefTitle  = computed(() => sendOnEnter.value ? (t('enterToSendHint') || 'Press Enter to send. Shift+Enter for newline.') : (t('ctrlEnterToSendHint') || 'Press Ctrl/Cmd+Enter to send. Enter for newline.'))
function saveSendPref(){ try { localStorage.setItem('sendOnEnter', JSON.stringify(!!sendOnEnter.value)) } catch(_) {} }

function htmlEscape(s){
  return String(s||'')
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
}

function renderAnswer(m){
  const raw = String(m?.content || '')
  const text = htmlEscape(raw).replace(/\n/g,'<br/>')
  const refs = m?.inlineRefs || {}
  // Replace [n] with Source buttons using inline refs when available
  const tid = threadId.value || route.params?.id || ''
  const mid = (m && typeof m.id === 'string') ? m.id.replace(/^db-/, '') : ''
  // If the answer indicates uncertainty, do not render sources and strip markers
  const low = raw.trim().toLowerCase()
  if (/i\s*(do\s*not|don't|dont)\s*know|not\s+sure|cannot\s+(determine|find)|no\s+(information|data)\s+(found|available)/.test(low)){
    return text.replace(/\[(\d+)\]/g, '')
  }
  return text.replace(/(?:\[(\d+)\]\s*)+/g, (full) => {
    const nums = Array.from(full.matchAll(/\[(\d+)\]/g)).map(x => x[1])
    if (!nums.length) return full

    const candidates = []
    for (const n of nums){
      const r = refs[String(n)] || {}
      if (r && r.document_id){
        candidates.push({ url: '', doc: r.document_id || '', page: r.page, title: r.title })
      } else if (Array.isArray(m?.citations)){
        const idx = Math.max(0, parseInt(n,10)-1)
        const c = m.citations[idx]
        if (c && (c.documentId || c.document_id)){
          candidates.push({ url: '', doc: c.documentId || c.document_id || '', page: c.page, title: c.title || c.label })
        }
      }
    }
    const seen = new Set(); const uniq = []
    for (const c of candidates){
      const key = `${c.url || c.doc}|${c.page || ''}`
      if (seen.has(key)) continue
      seen.add(key)
      uniq.push(c)
    }
    if (!uniq.length) return ''

    const one = uniq[0]
    const multi = uniq.length > 1
    const qparts = []
    if (tid) qparts.push(`fromThread=${encodeURIComponent(String(tid))}`)
    if (mid) qparts.push(`fromMessage=${encodeURIComponent(String(mid))}`)
    if (one.page) qparts.push(`p=${encodeURIComponent(String(one.page))}`)
    if (one.title) qparts.push(`t=${encodeURIComponent(String(one.title))}`)
    const qs = qparts.length ? ('?' + qparts.join('&')) : ''
    const label = multi ? `Sources (${uniq.length})` : `Source${one.page ? ` p. ${one.page}` : ''}`
    return `<a class="src-inline" href="/documents/${encodeURIComponent(String(one.doc))}${qs}">${label}</a>`
  })
}

function hasInlineMarkers(m){
  try { return /\[(\d+)\]/.test(String(m?.content || '')) } catch { return false }
}

// Consider an answer invalid if it's empty or explicitly uncertain.
function isValidAnswer(m){
  try{
    const raw = String(m?.content || '').trim()
    if (!raw) return false
    const low = raw.toLowerCase()
    const denies = [
      /i\s*(do\s*not|don't|dont)\s*know/,
      /not\s+sure/,
      /cannot\s+(determine|find)/,
      /no\s+(information|data)\s+(found|available)/,
    ]
    return !denies.some(rx => rx.test(low))
  }catch{ return true }
}

function fallbackInline(m){
  const out = []
  const refs = m?.inlineRefs || {}
  const list = Object.values(refs)
  const tid = threadId.value || route.params?.id || ''
  const mid = (m && typeof m.id === 'string') ? m.id.replace(/^db-/, '') : ''
  const params = []
  if (tid) params.push(`fromThread=${encodeURIComponent(String(tid))}`)
  if (mid) params.push(`fromMessage=${encodeURIComponent(String(mid))}`)
  const qs = params.length ? ('?' + params.join('&')) : ''
  for (const r of list.slice(0, 3)){
    if (r && r.document_id){
      const href = `/documents/${encodeURIComponent(String(r.document_id))}${qs}${qs ? '&' : '?'}${r.page ? ('p='+encodeURIComponent(String(r.page))) : ''}`.replace(/\?&$/, '').replace(/\?$/, '')
      out.push({ type:'doc', href, page: r.page })
    }
  }
  if (!out.length && Array.isArray(m?.citations)){
    for (const c of m.citations.slice(0,3)){
      if (c.documentId || c.document_id){
        const did = c.documentId || c.document_id
        const href = `/documents/${encodeURIComponent(String(did))}${qs}${qs ? '&' : '?'}${c.page ? ('p='+encodeURIComponent(String(c.page))) : ''}`.replace(/\?&$/, '').replace(/\?$/, '')
        out.push({ type:'doc', href, page: c.page })
      }
    }
  }
  return out
}
</script>

<style scoped>
:root{
  --bg:#f6f8ff; --card:#ffffff; --line:#e6ecf7; --txt:#25324a; --muted:#6e7b90; --blue:#1d4ed8;
  --md-shadow-1: 0 1px 3px rgba(16,24,40,.08), 0 1px 2px rgba(16,24,40,.06);
  --md-shadow-2: 0 2px 6px rgba(16,24,40,.10), 0 4px 12px rgba(16,24,40,.08);
}
.page{ background:var(--bg); min-height:100vh; padding: 0 12px; }
.page-head{ width:100%; margin:16px 0 10px; display:flex; align-items:center; justify-content:space-between; gap:12px; }
.page-head h1{ margin:0; font-size:22px; color:var(--txt); font-weight:800; letter-spacing:.2px; }
.left{ display:flex; align-items:center; gap:12px; }
.right{ display:flex; gap:8px; }
.ghost{ border:1px solid var(--line); background:var(--card); color:var(--blue); border-radius:10px; padding:8px 10px; font-weight:800; cursor:pointer; text-decoration:none; }

/* Chat */
.chat{ max-width: 900px; margin: 0 auto; display:grid; grid-template-rows: 1fr auto; gap: 10px; min-height: calc(100vh - 108px); }
.chat-body{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px; box-shadow: var(--md-shadow-1); overflow:auto; }
.welcome{ text-align:center; color:var(--muted); padding:28px 8px; }
.w-title{ font-weight:900; color:var(--txt); margin-bottom:4px; }
.w-sub{ font-size:14px; color:var(--muted); }
.w-examples{ margin-top:12px; display:flex; flex-wrap:wrap; gap:8px; justify-content:center; }
.example{ border:1px solid var(--line); background:var(--card); color:var(--txt); border-radius:999px; padding:7px 10px; cursor:pointer; font-weight:700; }

.msg{ display:flex; gap:10px; align-items:flex-start; }
.msg + .msg{ margin-top:10px; }
.msg.user{ justify-content:flex-end; }
.bubble{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:10px 12px; color:var(--txt); max-width:82%; flex: 0 1 auto; }
.msg.user .bubble{ background:var(--card); }
.content{ white-space:pre-wrap; line-height:1.4; }
.typing{ display:inline-flex; gap:6px; align-items:center; height:18px; }
.typing .dot{ width:6px; height:6px; border-radius:999px; background: var(--muted); animation: think-bounce 1s infinite ease-in-out; }
.typing .dot:nth-child(2){ animation-delay: .15s }
.typing .dot:nth-child(3){ animation-delay: .3s }
@keyframes think-bounce{ 0%, 80%, 100%{ transform: translateY(0); opacity:.5 } 40%{ transform: translateY(-3px); opacity:1 } }
.inline-fallback{ margin-top:6px; }
.inline-fallback .src-inline{ margin-right:6px; }
.content .src-inline{ display:inline-block; margin-left:6px; border:1px solid var(--line); background:var(--card); color:var(--blue); border-radius:999px; padding:1px 8px; font-size:12px; font-weight:800; text-decoration:none; }
.content .src-inline:hover{ background: var(--bg); }
.content .src-inline.disabled{ color: var(--muted); border-color: var(--line); cursor:default; }
.sources-list{ display:grid; gap:8px; margin-top:8px; }
.src-chip{ display:flex; align-items:center; flex-wrap:wrap; gap:8px; background:var(--card); border:1px solid var(--line); border-radius:10px; padding:6px 8px; }
.src-ico-comp{ display:inline-flex; font-size:16px; line-height:1; }
.src-ico-img{ width:1em; height:1em; display:inline-block; object-fit:contain; }
.src-title{ font-weight:800; color:var(--txt); }
.src-meta{ color:var(--muted); }
.link{ background:transparent; border:none; color:var(--blue); font-weight:800; cursor:pointer; padding:0; text-decoration:none; }
.link:hover{ text-decoration:underline; }

.composer{ position:sticky; bottom:8px; }
.comp-inner{ display:flex; gap:8px; align-items:flex-end; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:10px; box-shadow: var(--md-shadow-1); }
.comp-input{ flex:1; resize:none; border:none; outline:none; font-size:15px; line-height:1.4; max-height: 280px; overflow:hidden; padding:6px 2px; background: var(--card); color: var(--txt); }
.comp-input::placeholder{ color: var(--muted); }
.comp-actions{ display:flex; gap:8px; align-items:center; }
.send-pref{ display:flex; align-items:center; gap:6px; color:var(--muted); font-size:12.5px; }
.send-pref input{ margin:0; }
.send{ width:40px; height:40px; border:none; background:var(--blue); color:#fff; border-radius:999px; display:inline-grid; place-items:center; font-size:18px; font-weight:900; line-height:1; cursor:pointer; box-shadow: var(--md-shadow-1); transition: transform .12s ease, box-shadow .12s ease; }
.send:hover{ transform: translateY(-1px); box-shadow: var(--md-shadow-2); }
.send:active{ transform: translateY(0); }
.send[disabled]{ opacity:.6; cursor:not-allowed; transform:none; box-shadow: var(--md-shadow-1); }
.comp-error{ color:#b42318; margin-top:6px; font-weight:700; }

@media (max-width: 640px){
  .chat{ min-height: calc(100vh - 96px); }
}
</style>
