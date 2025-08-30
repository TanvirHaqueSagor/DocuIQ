<template>
  <div class="page">
    

    <!-- Chat area -->
    <section class="chat">
      <div ref="chatBody" class="chat-body">
        <div v-if="!messages.length" class="welcome">
          <div class="w-title">{{ $t ? $t('welcomeAsk') : 'Ask anything from your data' }}</div>
          <div class="w-sub">{{ $t ? $t('welcomeHint') : 'Your files and connected sources are indexed in a vector database. Ask questions and get referenced answers.' }}</div>
          <div class="w-examples">
            <button class="example" @click="useExample('Summarize the latest policy changes and list key points.')">Summarize the latest policy changes and list key points.</button>
            <button class="example" @click="useExample('What are the onboarding steps and who approves them?')">What are the onboarding steps and who approves them?</button>
            <button class="example" @click="useExample('Compare Q2 revenue growth across product lines with sources.')">Compare Q2 revenue growth across product lines with sources.</button>
          </div>
        </div>

        <div v-for="m in messages" :key="m.id" class="msg" :class="m.role">
          <div class="avatar" aria-hidden="true">{{ m.role==='assistant' ? '🤖' : '🧑' }}</div>
          <div class="bubble">
            <div class="content">{{ m.content }}</div>
            <div v-if="m.citations && m.citations.length" class="sources-list">
              <div v-for="(s, i) in m.citations" :key="i" class="src-chip">
                <span class="src-ico-comp" v-if="s.kind"><img class="src-ico-img" :src="iconForKind(s.kind)" :alt="s.kind" /></span>
                <span class="src-title">{{ s.title || s.label || s.name || ('Source #' + (i+1)) }}</span>
                <span v-if="s.page" class="src-meta">· p. {{ s.page }}</span>
                <RouterLink v-if="s.documentId" class="link" :to="`/documents/${s.documentId}`">{{ $t ? $t('view') : 'View' }}</RouterLink>
                <a v-else-if="s.url" class="link" :href="s.url" target="_blank" rel="noopener">{{ $t ? $t('open') : 'Open' }}</a>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Composer (ChatGPT-like) -->
      <div class="composer">
        <div class="comp-inner">
          <textarea
            v-model="q"
            class="comp-input"
            rows="1"
            :placeholder="$t ? $t('askSomething') : 'Ask across your documents and sources…'"
            @keydown.enter.exact.prevent="send"
            @keydown.enter.shift.stop
          ></textarea>
          <div class="comp-actions">
            <button class="ghost" @click="goDocuments">{{ $t ? $t('documents') : 'Documents' }}</button>
            <button class="send" :disabled="loading || !q.trim()" @click="send">
              {{ loading ? ($t ? $t('sending') : 'Sending…') : ($t ? $t('send') : 'Send') }}
            </button>
          </div>
        </div>
        <div v-if="error" class="comp-error">{{ error }}</div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'
// no API import needed here

// Minimal icon set for citations
import icFile from '../assets/icons/file.svg'
import icWeb from '../assets/icons/web.svg'
import icS3 from '../assets/icons/S3.svg'
import icGdrive from '../assets/icons/gdrive.svg'
import icDropbox from '../assets/icons/dropbox.svg'
import icOnedrive from '../assets/icons/onedrive.svg'
import icBox from '../assets/icons/box.svg'

const router = useRouter()
const q = ref('')
const loading = ref(false)
const error = ref('')
const messages = ref([])
const chatBody = ref(null)

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
      out.push({
        title: s.title || s.document?.title || s.metadata?.title || s.name,
        label: s.label,
        url: s.url || s.metadata?.url,
        page: s.page || s.metadata?.page,
        kind: (s.kind || s.metadata?.kind || s.source || '').toString().toLowerCase(),
        documentId: s.document_id || s.documentId || s.doc_id || s.id,
        score: s.score,
      })
    }
  } else if (data?.source) {
    out.push({ title: data.source, label: data.source })
  }
  return out
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
  const id = Date.now() + '-' + Math.random().toString(36).slice(2)
  messages.value.push({ id, role:'user', content: text })
  q.value = ''
  scrollToBottom()
  loading.value = true
  try{
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
    if(!output && Array.isArray(data?.matches)){
      output = data.matches.slice(0,3).map(m => m.text || m.chunk || m.content || '').filter(Boolean).join('\n\n')
    }
    messages.value.push({ id: id+'-a', role:'assistant', content: output || (data?.source ? `Source: ${data.source}` : '—'), citations: cites })
  }catch(e){
    const msg = e?.message || 'Something went wrong'
    if (/Failed to fetch|NetworkError|TypeError: fetch/i.test(String(msg))) {
      error.value = `Cannot reach AI service at ${AI}/ask. Set VITE_AI_URL or start the AI engine.`
    } else {
      error.value = msg
    }
  }finally{
    loading.value = false
    scrollToBottom()
  }
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
.ghost{ border:1px solid #dbe3f3; background:#fff; color:#1f47c5; border-radius:10px; padding:8px 10px; font-weight:800; cursor:pointer; text-decoration:none; }

/* Chat */
.chat{ max-width: 900px; margin: 0 auto; display:grid; grid-template-rows: 1fr auto; gap: 10px; min-height: calc(100vh - 108px); }
.chat-body{ background:#fff; border:1px solid #e8eef8; border-radius:12px; padding:14px; box-shadow: var(--md-shadow-1); overflow:auto; }
.welcome{ text-align:center; color:#546179; padding:28px 8px; }
.w-title{ font-weight:900; color:#1f2a44; margin-bottom:4px; }
.w-sub{ font-size:14px; color:#6e7b90; }
.w-examples{ margin-top:12px; display:flex; flex-wrap:wrap; gap:8px; justify-content:center; }
.example{ border:1px solid #dbe3f3; background:#fff; color:#1e2a44; border-radius:999px; padding:7px 10px; cursor:pointer; font-weight:700; }

.msg{ display:flex; gap:10px; align-items:flex-start; }
.msg + .msg{ margin-top:10px; }
.msg .avatar{ width:28px; height:28px; display:grid; place-items:center; border-radius:999px; background:#eef2ff; }
.msg.user .avatar{ background:#e8f7ee; }
.bubble{ background:#f8fbff; border:1px solid #e6ecf7; border-radius:12px; padding:10px 12px; flex:1; color:#2a3342; }
.msg.user .bubble{ background:#fff; }
.content{ white-space:pre-wrap; line-height:1.4; }
.sources-list{ display:grid; gap:8px; margin-top:8px; }
.src-chip{ display:flex; align-items:center; flex-wrap:wrap; gap:8px; background:#fff; border:1px solid #e6ecf7; border-radius:10px; padding:6px 8px; }
.src-ico-comp{ display:inline-flex; font-size:16px; line-height:1; }
.src-ico-img{ width:1em; height:1em; display:inline-block; object-fit:contain; }
.src-title{ font-weight:800; color:#2a3342; }
.src-meta{ color:#6e7b90; }
.link{ background:transparent; border:none; color:#1d4ed8; font-weight:800; cursor:pointer; padding:0; text-decoration:none; }
.link:hover{ text-decoration:underline; }

.composer{ position:sticky; bottom:8px; }
.comp-inner{ display:flex; gap:8px; align-items:flex-end; background:#fff; border:1px solid #e8eef8; border-radius:12px; padding:10px; box-shadow: var(--md-shadow-1); }
.comp-input{ flex:1; resize:none; border:none; outline:none; font-size:15px; max-height: 180px; }
.comp-actions{ display:flex; gap:8px; }
.send{ border:none; background:#1f47c5; color:#fff; border-radius:10px; padding:8px 12px; font-weight:800; cursor:pointer; }
.send[disabled]{ opacity:.6; cursor:not-allowed; }
.comp-error{ color:#b42318; margin-top:6px; font-weight:700; }

@media (max-width: 640px){
  .chat{ min-height: calc(100vh - 96px); }
}
</style>
