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
            <div v-if="m.role==='assistant' && !m.thinking" class="bubble-actions">
              <button class="ghost-btn" type="button" @click="copyAnswer(m)" :aria-label="$t ? $t('copy') : 'Copy answer'">
                {{ $t ? ($t('copy') || 'Copy') : 'Copy' }}
              </button>
              <button class="ghost-btn" type="button" @click="downloadAnswer(m)" :aria-label="$t ? $t('download') : 'Download answer'">
                {{ $t ? ($t('download') || 'Download') : 'Download' }}
              </button>
            </div>
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
              <div v-if="hasSources(m)" class="sources-list" role="list">
                <RouterLink
                  v-for="(source, idx) in sourcesForMessage(m)"
                  :key="`src-${idx}-${source.documentId || source.document_id || source.url || source.title || source.label || 'doc'}`"
                  class="src-chip"
                  :to="sourceHref(source, m)"
                >
                  <span class="src-ico-comp">
                    <img :src="iconForKind(guessSourceKind(source))" class="src-ico-img" alt="" />
                  </span>
                  <div class="src-text">
                    <div class="src-title">{{ sourceTitle(source, idx) }}</div>
                    <div class="src-meta">
                      <span class="badge">{{ sourceKindLabel(source) }}</span>
                      <span v-if="source.page" class="src-page">{{ pageLabel }} {{ source.page }}</span>
                    </div>
                  </div>
                </RouterLink>
              </div>
              <div v-if="Array.isArray(m.structuredTables) && m.structuredTables.length" class="table-stack">
                <article v-for="(table, tIdx) in m.structuredTables" :key="tableKey(table, tIdx)" class="answer-table">
                  <div class="table-toolbar">
                    <div class="table-title">{{ tableTitle(table, tIdx) }}</div>
                    <div class="table-actions">
                      <button class="link sm" type="button" @click="copyTable(table)">
                        {{ $t ? ($t('copy') || 'Copy') : 'Copy' }}
                      </button>
                      <button class="link sm" type="button" @click="downloadTable(table)">
                        {{ $t ? ($t('download') || 'Download CSV') : 'Download CSV' }}
                      </button>
                      <button class="link sm" type="button" @click="downloadTableExcel(table)">
                        {{ $t ? ($t('downloadExcel') || 'Download Excel') : 'Download Excel' }}
                      </button>
                    </div>
                  </div>
                  <div class="table-scroll" role="region" tabindex="0">
                    <table>
                      <thead>
                        <tr>
                          <th v-for="(header, hIdx) in table.headers" :key="`h-${tIdx}-${hIdx}`">{{ header }}</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-if="!table.rows.length">
                          <td :colspan="Math.max(table.headers.length, 1)" class="muted">No data available</td>
                        </tr>
                        <tr v-for="(row, rIdx) in table.rows" :key="`r-${tIdx}-${rIdx}`">
                          <td v-for="(cell, cIdx) in row" :key="`c-${tIdx}-${rIdx}-${cIdx}`">{{ cell }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </article>
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
  messages.value.push(decorateMessage({ id, role:'user', content: text }))
  q.value = ''
  nextTick(() => autoGrow())
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
    const finalMsg = decorateMessage({
      id: id+'-a',
      role:'assistant',
      content: output || (data?.source ? `Source: ${data.source}` : '—'),
      citations: cites,
      inlineRefs: irefs,
    })
    if (idxWait !== -1) messages.value.splice(idxWait, 1, finalMsg)
    else messages.value.push(finalMsg)
    // Save assistant message
    if (threadId.value) {
      try{
        await authFetch(`${API_BASE_URL}/api/chats/threads/${threadId.value}/messages/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ role: 'assistant', content: output, citations: cites, inline_refs: irefs })
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
      const serverMsgs = (arr || []).map(m => decorateMessage({
        id: 'db-'+m.id,
        role: m.role,
        content: m.content,
        citations: Array.isArray(m.citations) ? m.citations : [],
        inlineRefs: normalizeInlineRefs(m.inline_refs)
      }))
      // Build signatures for server messages to dedupe local optimistic ones
      const sig = (m) => `${m.role}|${(m.content||'').trim()}`
      const serverSigs = new Set(serverMsgs.map(sig))
      const localHasUser = (messages.value || []).some(y => typeof y?.id === 'string' && !y.id.startsWith('db-') && y.role==='user')
      const localMsgsRaw = (messages.value || []).filter(x => {
        if (!(typeof x?.id === 'string' && !x.id.startsWith('db-'))) return false
        if (x.thinking) return localHasUser
        // drop local if same role+content exists on server
        return !serverSigs.has(sig(x))
      })
      const localMsgs = localMsgsRaw.map(decorateMessage)
      messages.value = [...serverMsgs, ...localMsgs]
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
    const next = Math.min(max, el.scrollHeight)
    el.style.height = next + 'px'
    el.style.overflowY = el.scrollHeight > max ? 'auto' : 'hidden'
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
const pageLabel = computed(() => t('page') || 'Page')
function saveSendPref(){ try { localStorage.setItem('sendOnEnter', JSON.stringify(!!sendOnEnter.value)) } catch(_) {} }

function htmlEscape(s){
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function markdownToHtml(raw){
  const text = String(raw || '')
  if (!text.trim()) return ''
  if (looksLikeHtml(text)) {
    return sanitizeHtml(text)
  }
  const normalized = text.replace(/\r\n/g, '\n')
  const lines = normalized.split('\n')
  const parts = []
  let i = 0
  while (i < lines.length) {
    const line = lines[i]
    if (/^\s*$/.test(line)) {
      parts.push('<br/>')
      i++
      continue
    }
    if (/^\s*```/.test(line.trim())) {
      const codeLines = []
      i++
      while (i < lines.length && !/^\s*```/.test(lines[i].trim())) {
        codeLines.push(lines[i])
        i++
      }
      if (i < lines.length && /^\s*```/.test(lines[i].trim())) i++
      parts.push(`<pre><code>${htmlEscape(codeLines.join('\n'))}</code></pre>`)
      continue
    }
    const nextLine = lines[i + 1]
    if (isTableHeader(line, nextLine)) {
      const { html, nextIndex } = buildTable(lines, i)
      parts.push(html)
      i = nextIndex
      continue
    }
    parts.push(`<p>${formatInline(htmlEscape(line))}</p>`)
    i++
  }
  return parts.join('').replace(/(<br\/>){2,}/g, '<br/>')
}

function looksLikeHtml(text){
  return /<\s*(table|tr|td|th|thead|tbody|ul|ol|li|p|br|div|span|code|pre)\b/i.test(text)
}

function sanitizeHtml(html){
  if (typeof window === 'undefined' || typeof document === 'undefined') return html
  const template = document.createElement('template')
  template.innerHTML = html
  template.content.querySelectorAll('script,style,iframe,object,embed,link,meta').forEach(el => el.remove())
  template.content.querySelectorAll('*').forEach((el) => {
    Array.from(el.attributes || []).forEach(attr => {
      if (/^on/i.test(attr.name) || attr.name === 'srcdoc') {
        el.removeAttribute(attr.name)
      }
    })
  })
  return template.innerHTML
}

function formatInline(text){
  return text
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/__(.+?)__/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/_(.+?)_/g, '<em>$1</em>')
}

function isTableHeader(line, nextLine){
  if (!line || !nextLine) return false
  if (!line.includes('|') || !nextLine.includes('|')) return false
  return isTableSeparator(nextLine)
}

function isTableSeparator(line){
  if (!line) return false
  const trimmed = line.trim()
  if (!trimmed) return false
  return /^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(trimmed)
}

function splitTableLine(line){
  const cleaned = line.trim().replace(/^\|/, '').replace(/\|$/, '')
  if (!cleaned) return []
  return cleaned.split('|').map(cell => cell.trim())
}

function buildTable(lines, startIndex){
  const headers = splitTableLine(lines[startIndex])
  let idx = startIndex + 2 // skip header + separator
  const rows = []
  while (idx < lines.length) {
    const current = lines[idx]
    if (!current || !current.includes('|') || /^\s*$/.test(current)) break
    if (isTableSeparator(current)) {
      idx++
      continue
    }
    rows.push(splitTableLine(current))
    idx++
  }
  const headerHtml = headers.map(cell => `<th>${htmlEscape(cell)}</th>`).join('')
  const bodyHtml = rows.length
    ? rows.map(row => `<tr>${row.map(cell => `<td>${htmlEscape(cell)}</td>`).join('')}</tr>`).join('')
    : `<tr><td colspan="${Math.max(headers.length, 1)}"></td></tr>`
  return {
    html: `<table><thead><tr>${headerHtml}</tr></thead><tbody>${bodyHtml}</tbody></table>`,
    nextIndex: idx
  }
}

function renderAnswer(m){
  const raw = String(m?.content || '')
  const html = markdownToHtml(raw)
  if (!html) return ''
  const refs = m?.inlineRefs || {}
  // Replace [n] with Source buttons using inline refs when available
  const tid = threadId.value || route.params?.id || ''
  const mid = (m && typeof m.id === 'string') ? m.id.replace(/^db-/, '') : ''
  // If the answer indicates uncertainty, do not render sources and strip markers
  const low = raw.trim().toLowerCase()
  if (/i\s*(do\s*not|don't|dont)\s*know|not\s+sure|cannot\s+(determine|find)|no\s+(information|data)\s+(found|available)/.test(low)){
    return html.replace(/\[(\d+)\]/g, '')
  }
  return html.replace(/(?:\[(\d+)\]\s*)+/g, (full) => {
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

function hasSources(m){
  try{
    return isValidAnswer(m) && Array.isArray(m?.citations) && m.citations.length > 0
  }catch{
    return false
  }
}

function sourcesForMessage(m){
  if (!hasSources(m)) return []
  return (m.citations || []).slice(0, 4)
}

function sourceTitle(source, idx){
  return source?.title || source?.label || source?.name || `Source ${idx + 1}`
}

function sourceHref(source, message){
  return linkForCitation(source, message) || '/documents'
}

function guessSourceKind(source){
  const k = String(source?.kind || source?.source || '').trim().toLowerCase()
  if (k) return k
  const title = String(source?.title || source?.label || '').trim().toLowerCase()
  if (/\.(ppt|pptx)$/.test(title)) return 'ppt'
  if (/\.(doc|docx)$/.test(title)) return 'doc'
  if (/\.(xls|xlsx|csv)$/.test(title)) return 'sheet'
  if (/\.(pdf)$/.test(title)) return 'file'
  return 'file'
}

function sourceKindLabel(source){
  const kind = guessSourceKind(source)
  const map = {
    ppt: 'PPT', pptx: 'PPT',
    doc: 'DOC', docx: 'DOC',
    file: 'DOC', files: 'DOC',
    pdf: 'PDF',
    sheet: 'Sheet', xls: 'Sheet', xlsx: 'Sheet', csv: 'CSV',
    web: 'Web',
    s3: 'S3',
    gdrive: 'Drive',
    dropbox: 'Dropbox',
    onedrive: 'OneDrive',
    box: 'Box'
  }
  return map[kind] || (kind ? kind.toUpperCase() : 'DOC')
}

function decorateMessage(msg){
  if (!msg || typeof msg !== 'object' || msg.thinking) return msg
  const next = { ...msg }
  next.inlineRefs = normalizeInlineRefs(next.inlineRefs)
  if (next.role === 'assistant') {
    next.structuredTables = Array.isArray(next.structuredTables)
      ? next.structuredTables
      : extractStructuredTables(next.content)
  } else {
    next.structuredTables = []
  }
  return next
}

function normalizeInlineRefs(raw){
  if (!raw || typeof raw !== 'object') return {}
  const out = {}
  for (const [key, value] of Object.entries(raw)){
    if (!value || typeof value !== 'object') continue
    out[String(key)] = {
      title: value.title || value.label || value.name,
      document_id: value.document_id || value.documentId || value.doc_id || value.id,
      documentId: value.documentId || value.document_id || value.doc_id || value.id,
      page: typeof value.page === 'number' ? value.page : undefined,
      url: value.url || ''
    }
  }
  return out
}

function extractStructuredTables(raw){
  const tables = []
  const text = typeof raw === 'string' ? raw.trim() : ''
  if (!text) return tables
  const entire = tryParseJsonTable(text)
  if (entire) tables.push(entire)
  const blockRx = /```(?:json|table|csv)?([\s\S]*?)```/gi
  let match
  while ((match = blockRx.exec(raw || ''))) {
    const block = (match[1] || '').trim()
    if (!block) continue
    const jsonTable = tryParseJsonTable(block)
    if (jsonTable) {
      tables.push(jsonTable)
      continue
    }
    const csvTable = parseDelimitedBlock(block)
    if (csvTable) tables.push(csvTable)
  }
  if (!tables.length) {
    const fallback = parseDelimitedBlock(text)
    if (fallback) tables.push(fallback)
  }
  return tables
}

function tryParseJsonTable(text){
  const trimmed = typeof text === 'string' ? text.trim() : ''
  if (!trimmed) return null
  const looksJson = trimmed.startsWith('{') || trimmed.startsWith('[')
  if (!looksJson) return null
  try{
    const parsed = JSON.parse(trimmed)
    return convertJsonToTable(parsed)
  }catch(_){
    return null
  }
}

function convertJsonToTable(data){
  if (Array.isArray(data)) {
    if (!data.length) return null
    if (data.every(item => item && typeof item === 'object' && !Array.isArray(item))) {
      const headers = Array.from(new Set(data.flatMap(item => Object.keys(item || {}))))
      if (!headers.length) return null
      const rows = data.map(item => headers.map(key => formatCell(item?.[key])))
      return { headers, rows }
    }
    if (data.every(item => Array.isArray(item))) {
      const headers = (data[0] || []).map((cell, idx) => formatHeader(cell, idx))
      const rows = data.slice(1).map(row => headers.map((_, idx) => formatCell(row?.[idx])))
      return { headers, rows }
    }
    return null
  }
  if (data && typeof data === 'object') {
    if (Array.isArray(data.headers) && Array.isArray(data.rows)) {
      const headers = data.headers.map((cell, idx) => formatHeader(cell, idx))
      const rows = data.rows.map(row => normalizeRow(row, headers))
      return { headers, rows, title: data.title || data.name || data.caption }
    }
    if (Array.isArray(data.data)) {
      return convertJsonToTable(data.data)
    }
  }
  return null
}

function normalizeRow(row, headers){
  if (Array.isArray(row)) {
    return headers.map((_, idx) => formatCell(row[idx]))
  }
  if (row && typeof row === 'object') {
    return headers.map(key => formatCell(row?.[key]))
  }
  return headers.map(() => formatCell(row))
}

function parseDelimitedBlock(block){
  const lines = (block || '').split(/\r?\n/).map(line => line.trim()).filter(Boolean)
  if (lines.length < 2) return null
  const delimiter = detectDelimiter(lines)
  if (!delimiter) return null
  if (delimiter === '|' && lines.length >= 2 && isTableSeparator(lines[1])) return null
  const rows = lines.map(line => splitDelimitedLine(line, delimiter))
  if (!rows.length || rows[0].length < 2) return null
  const headers = rows[0].map((cell, idx) => formatHeader(cell, idx))
  const body = rows.slice(1).map(row => headers.map((_, idx) => formatCell(row[idx])))
  return { headers, rows: body }
}

function detectDelimiter(lines){
  const firstLine = lines[0] || ''
  const candidates = [
    { char: '\t', score: (firstLine.match(/\t/g) || []).length },
    { char: ',', score: (firstLine.match(/,/g) || []).length },
    { char: ';', score: (firstLine.match(/;/g) || []).length },
    { char: '|', score: (firstLine.match(/\|/g) || []).length },
  ]
  candidates.sort((a, b) => b.score - a.score)
  return candidates[0] && candidates[0].score >= 1 ? candidates[0].char : null
}

function splitDelimitedLine(line, delimiter){
  if (delimiter === '|') {
    const cleaned = line.replace(/^\|/, '').replace(/\|$/, '')
    return cleaned.split('|').map(cell => cell.trim())
  }
  if (delimiter === '\t') {
    return line.split('\t').map(cell => cell.trim())
  }
  return splitCsvLine(line, delimiter)
}

function splitCsvLine(line, delimiter=','){
  const cells = []
  let current = ''
  let inQuotes = false
  for (let i = 0; i < line.length; i++){
    const ch = line[i]
    if (ch === '"'){
      if (inQuotes && line[i + 1] === '"'){
        current += '"'
        i++
      } else {
        inQuotes = !inQuotes
      }
      continue
    }
    if (ch === delimiter && !inQuotes){
      cells.push(current.trim())
      current = ''
      continue
    }
    current += ch
  }
  cells.push(current.trim())
  return cells.map(cell => cell.replace(/^"|"$/g, ''))
}

function formatHeader(value, idx){
  const text = formatCell(value)
  return text || `Column ${idx + 1}`
}

function formatCell(value){
  if (value === null || value === undefined) return ''
  if (typeof value === 'object') {
    try { return JSON.stringify(value) } catch { return '' }
  }
  return String(value)
}

function tableTitle(table, idx){
  return table?.title || table?.name || table?.caption || `Table ${idx + 1}`
}

function tableKey(table, idx){
  return table?.id || table?.name || `table-${idx}`
}

async function copyAnswer(m){
  const text = buildPlainText(m)
  if (!text) return
  await copyToClipboard(text)
}

function downloadAnswer(m){
  const tables = Array.isArray(m?.structuredTables) ? m.structuredTables : []
  if (tables.length) {
    const csv = formatTableForExport(tables[0], ',')
    downloadBlob(csv, buildFilename('table', 'csv'), 'text/csv')
    return
  }
  const text = buildPlainText(m)
  downloadBlob(text, buildFilename('answer', 'txt'), 'text/plain')
}

async function copyTable(table){
  const text = formatTableForExport(table, '\t')
  await copyToClipboard(text)
}

function downloadTable(table){
  const csv = formatTableForExport(table, ',')
  downloadBlob(csv, buildFilename('table', 'csv'), 'text/csv')
}

function downloadTableExcel(table){
  const workbook = buildExcelWorkbook(table)
  downloadBlob(workbook, buildFilename('table', 'xls'), 'application/vnd.ms-excel')
}

function buildPlainText(m){
  const chunks = []
  if (m?.content) chunks.push(String(m.content))
  const tables = Array.isArray(m?.structuredTables) ? m.structuredTables : []
  tables.forEach((table, idx) => {
    chunks.push(`${tableTitle(table, idx)}\n${formatTableForExport(table, '\t')}`)
  })
  return chunks.filter(Boolean).join('\n\n')
}

function formatTableForExport(table, delimiter=','){
  const headers = (table?.headers || []).map(cell => formatCell(cell))
  const rows = (table?.rows || []).map(row => row.map(cell => formatCell(cell)))
  const encode = (value) => {
    if (delimiter === ',') {
      const needsQuote = /["\n,]/.test(value)
      const escaped = value.replace(/"/g, '""')
      return needsQuote ? `"${escaped}"` : escaped
    }
    return value
  }
  const joinRow = (row) => row.map(val => encode(val || '')).join(delimiter === ',' ? ',' : '\t')
  const lines = []
  if (headers.length) lines.push(joinRow(headers))
  rows.forEach(row => lines.push(joinRow(row)))
  return lines.join('\n')
}

function buildExcelWorkbook(table){
  const headers = (table?.headers || []).map(cell => formatCell(cell))
  const rows = (table?.rows || []).map(row => row.map(cell => formatCell(cell)))
  const headerXml = headers.length ? `<Row>${headers.map(excelCell).join('')}</Row>` : ''
  const bodyXml = rows.length
    ? rows.map(row => `<Row>${row.map(excelCell).join('')}</Row>`).join('')
    : '<Row><Cell><Data ss:Type="String"></Data></Cell></Row>'
  return `<?xml version="1.0" encoding="UTF-8"?><?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:x="urn:schemas-microsoft-com:office:excel"
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
 <Worksheet ss:Name="Sheet1">
  <Table>
   ${headerXml}${bodyXml}
  </Table>
 </Worksheet>
</Workbook>`
}

function excelCell(value){
  const text = formatCell(value)
  const numeric = /^-?\d+(\.\d+)?$/.test(text.replace(/,/g, ''))
  const safe = escapeXml(numeric ? text.replace(/,/g, '') : text)
  const type = numeric ? 'Number' : 'String'
  return `<Cell><Data ss:Type="${type}">${safe}</Data></Cell>`
}

async function copyToClipboard(text){
  if (!text) return
  try{
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
      return
    }
  }catch(_){ /* ignore */ }
  try{
    const ta = document.createElement('textarea')
    ta.value = text
    ta.style.position = 'fixed'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.focus()
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
  }catch(_){ /* ignore */ }
}

function downloadBlob(content, filename, mime){
  try{
    const blob = content instanceof Blob ? content : new Blob([content], { type: mime || 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename || 'download.txt'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    setTimeout(() => URL.revokeObjectURL(url), 300)
  }catch(_){ /* ignore */ }
}

function buildFilename(kind, ext){
  const tid = threadId.value || 'analysis'
  const stamp = new Date().toISOString().replace(/[:.]/g, '-')
  return `${kind}-${tid}-${stamp}.${ext}`
}

function escapeXml(value){
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}
</script>

<style scoped>
:root{
  --bg:#f6f8ff; --card:#ffffff; --line:#e6ecf7; --txt:#25324a; --muted:#6e7b90; --blue:#1d4ed8;
  --md-shadow-1: 0 1px 3px rgba(16,24,40,.08), 0 1px 2px rgba(16,24,40,.06);
  --md-shadow-2: 0 2px 6px rgba(16,24,40,.10), 0 4px 12px rgba(16,24,40,.08);
}
.page{ background:var(--bg); min-height:100vh; padding: 0 clamp(12px, 3vw, 32px); }
.page-head{ width:100%; margin:16px 0 10px; display:flex; align-items:center; justify-content:space-between; gap:12px; }
.page-head h1{ margin:0; font-size:22px; color:var(--txt); font-weight:800; letter-spacing:.2px; }
.left{ display:flex; align-items:center; gap:12px; }
.right{ display:flex; gap:8px; }
.ghost{ border:1px solid var(--line); background:var(--card); color:var(--blue); border-radius:10px; padding:8px 10px; font-weight:800; cursor:pointer; text-decoration:none; }

/* Chat */
.chat{ width:min(100%, 1100px); margin: 0 auto; display:grid; grid-template-rows: 1fr auto; gap: 10px; min-height: calc(100vh - 108px); }
.chat-body{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px; box-shadow: var(--md-shadow-1); overflow:auto; }
.welcome{ text-align:center; color:var(--muted); padding:28px 8px; }
.w-title{ font-weight:900; color:var(--txt); margin-bottom:4px; }
.w-sub{ font-size:14px; color:var(--muted); }
.w-examples{ margin-top:12px; display:flex; flex-wrap:wrap; gap:8px; justify-content:center; }
.example{ border:1px solid var(--line); background:var(--card); color:var(--txt); border-radius:999px; padding:7px 10px; cursor:pointer; font-weight:700; }

.msg{ display:flex; gap:10px; align-items:flex-start; }
.msg + .msg{ margin-top:10px; }
.msg.assistant{ justify-content:flex-start; }
.msg.user{ justify-content:flex-end; }
.bubble{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px 16px; color:var(--txt); max-width:min(80%, 720px); box-shadow: var(--md-shadow-1); position:relative; }
.msg.assistant .bubble{ margin-right:auto; }
.msg.user .bubble{ margin-left:auto; background:var(--card); box-shadow:none; border-color:rgba(148,163,184,.5); }
.msg.assistant .bubble{ background:#f9fbff; border-color:rgba(99,102,241,.3); }
.bubble-actions{ display:flex; justify-content:flex-end; gap:6px; margin-bottom:10px; }
.ghost-btn{ border:1px solid rgba(148,163,184,.5); background:transparent; color:var(--muted); border-radius:999px; padding:4px 12px; font-size:12px; cursor:pointer; }
.ghost-btn:hover{ color:var(--blue); border-color:var(--blue); }
.content{ line-height:1.5; font-size:15px; word-break:break-word; }
.content table{ width:100%; border-collapse:collapse; margin-top:12px; font-size:14px; }
.content th, .content td{ border:1px solid var(--line); padding:6px 8px; text-align:left; }
.content thead tr{ background:rgba(29,78,216,.06); }
.content tbody tr:nth-child(even){ background:rgba(29,78,216,.03); }
.content pre{ background:#0f172a; color:#f8fafc; padding:10px; border-radius:8px; overflow:auto; font-size:13px; }
.content code{ background:rgba(15,23,42,.08); padding:2px 6px; border-radius:6px; font-size:13px; }
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
.sources-list{ display:grid; gap:8px; margin-top:10px; }
.src-chip{ display:flex; align-items:center; flex-wrap:wrap; gap:10px; background:var(--card); border:1px solid var(--line); border-radius:10px; padding:8px 10px; text-decoration:none; color:var(--txt); transition: border-color .15s ease, transform .15s ease; }
.src-chip:hover{ border-color: var(--blue); transform: translateY(-1px); }
.src-ico-comp{ display:inline-flex; font-size:16px; line-height:1; }
.src-ico-img{ width:1.2em; height:1.2em; display:inline-block; object-fit:contain; }
.src-text{ display:flex; flex-direction:column; gap:2px; }
.src-title{ font-weight:800; color:var(--txt); }
.src-meta{ color:var(--muted); display:flex; gap:8px; font-size:13px; align-items:center; }
.badge{ background:rgba(29,78,216,.09); color:var(--blue); border-radius:999px; padding:2px 8px; font-size:11px; font-weight:700; text-transform:uppercase; }
.src-page{ font-weight:700; }
.link{ background:transparent; border:none; color:var(--blue); font-weight:800; cursor:pointer; padding:0; text-decoration:none; }
.link.sm{ font-size:12px; }
.link:hover{ text-decoration:underline; }
.table-stack{ display:flex; flex-direction:column; gap:12px; margin-top:14px; }
.answer-table{ border:1px solid var(--line); border-radius:12px; background:#fff; box-shadow:var(--md-shadow-1); padding:12px; }
.table-toolbar{ display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:8px; flex-wrap:wrap; }
.table-title{ font-weight:700; color:var(--txt); }
.table-actions{ display:flex; gap:10px; }
.table-scroll{ overflow:auto; border:1px solid var(--line); border-radius:12px; box-shadow: inset 0 1px 0 rgba(255,255,255,.6); }
.table-scroll table{ width:100%; border-collapse:separate; border-spacing:0; min-width:420px; }
.table-scroll th, .table-scroll td{ padding:11px 14px; font-size:14px; text-align:left; border-bottom:1px solid rgba(148,163,184,.4); }
.table-scroll th{ background:linear-gradient(135deg, rgba(59,130,246,.15), rgba(99,102,241,.08)); color:#1e293b; font-weight:700; position:sticky; top:0; z-index:1; }
.table-scroll tbody tr:nth-child(even){ background:rgba(226,232,240,.6); }
.table-scroll tbody tr:hover{ background:rgba(59,130,246,.12); transition:background .2s ease; }
.table-scroll table tr:first-child th:first-child{ border-top-left-radius:12px; }
.table-scroll table tr:first-child th:last-child{ border-top-right-radius:12px; }
.table-scroll table tr:last-child td:first-child{ border-bottom-left-radius:12px; }
.table-scroll table tr:last-child td:last-child{ border-bottom-right-radius:12px; border-bottom:none; }
.muted{ color:var(--muted); font-style:italic; }

.composer{ position:sticky; bottom:8px; }
.comp-inner{ display:flex; gap:8px; align-items:flex-end; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:10px; box-shadow: var(--md-shadow-1); }
.comp-input{ flex:1; resize:none; border:none; outline:none; font-size:15px; line-height:1.4; max-height: 280px; overflow-y:hidden; padding:6px 2px; background: var(--card); color: var(--txt); }
.comp-input::placeholder{ color: var(--muted); }
.comp-actions{ display:flex; gap:8px; align-items:center; }
.send-pref{ display:flex; align-items:center; gap:6px; color:var(--muted); font-size:12.5px; }
.send-pref input{ margin:0; }
.send{ width:40px; height:40px; border:none; background:var(--blue); color:#fff; border-radius:999px; display:inline-grid; place-items:center; font-size:18px; font-weight:900; line-height:1; cursor:pointer; box-shadow: var(--md-shadow-1); transition: transform .12s ease, box-shadow .12s ease; }
.send:hover{ transform: translateY(-1px); box-shadow: var(--md-shadow-2); }
.send:active{ transform: translateY(0); }
.send[disabled]{ opacity:.6; cursor:not-allowed; transform:none; box-shadow: var(--md-shadow-1); }
.comp-error{ color:#b42318; margin-top:6px; font-weight:700; }

@media (max-width: 768px){
  .chat{ min-height: calc(100vh - 96px); width:100%; }
  .bubble{ padding:12px 10px; max-width:100%; }
  .table-scroll table{ min-width:320px; }
  .table-toolbar{ flex-direction:column; align-items:flex-start; }
}
</style>
