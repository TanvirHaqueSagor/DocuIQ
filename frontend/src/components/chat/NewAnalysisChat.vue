<template>
  <div class="analysis-page">
    <section class="chat-stage">
      <div class="chat-card">
        <div ref="messagesWrap" class="messages-pane">
          <div v-if="!messages.length" class="empty-state">
            <h2>Start a new analysis</h2>
            <p>Ask DocuIQ anything about your reports, policies, ESG or finance data.</p>
            <div class="pill-group">
              <button
                v-for="prompt in suggestedPrompts"
                :key="`empty-${prompt}`"
                type="button"
                class="pill"
                :disabled="loading"
                @click="usePrompt(prompt)"
              >
                {{ prompt }}
              </button>
            </div>
          </div>

          <div v-else>
            <ChatMessage
              v-for="message in messages"
              :key="message.id"
              :message="message"
              @open-citation="handleCitation"
            />
          </div>
        </div>

        <div class="composer-block">
          <ChatComposer
            v-model="draft"
            :loading="loading"
            :disabled="false"
            :placeholder="t('askSomething') || 'Ask something...'"
            @submit="send"
          />
          <div class="composer-meta">
            <span>Enter to send · Shift+Enter for newline</span>
          </div>
          <p v-if="error" class="error">{{ error }}</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import ChatComposer from './ChatComposer.vue'
import ChatMessage from './ChatMessage.vue'
import { API_BASE_URL } from '../../config'
import { authFetch } from '../../lib/authFetch'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()

const draft = ref('')
const loading = ref(false)
const error = ref('')
const messages = ref([])
const messagesWrap = ref(null)
const threadId = ref(null)
const skipNextThreadLoad = ref(false)

const suggestedPrompts = [
  t('ex1') || 'Summarize the latest policy changes and list key points.',
  t('ex2') || 'What are the onboarding steps and who approves them?',
  t('ex3') || 'Compare Q2 revenue growth across product lines with sources.'
]

const AI = (import.meta.env.VITE_AI_URL && import.meta.env.VITE_AI_URL.trim()) || 'http://localhost:8001'

function usePrompt(prompt) {
  draft.value = prompt
  send()
}

async function send() {
  const text = (draft.value || '').trim()
  if (!text || loading.value) return
  error.value = ''
  const userMsg = createUserMessage(text)
  messages.value.push(userMsg)
  draft.value = ''
  scrollToBottom()
  const waitId = pushAssistantPlaceholder()
  loading.value = true
  try {
    if (!threadId.value) {
      await createThread(text)
    }
    if (threadId.value) {
      await persistMessage(threadId.value, { role: 'user', content: text })
    }
    const payload = await askAI(text)
    const assistantMsg = createAssistantMessage(userMsg.id, payload)
    replaceMessage(waitId, assistantMsg)
    if (threadId.value) {
      await persistMessage(threadId.value, {
        role: 'assistant',
        content: assistantMsg.content,
        citations: assistantMsg.citations,
        structured_blocks: assistantMsg.blocks,
        inline_refs: assistantMsg.inlineRefs || {}
      })
    }
  } catch (err) {
    error.value = err?.message || 'Unable to send message'
    removeMessage(waitId)
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

function createUserMessage(content) {
  return {
    id: `user-${Date.now()}-${Math.random().toString(36).slice(2)}`,
    role: 'user',
    content,
    timestamp: new Date().toISOString(),
    blocks: [{ type: 'text', content }]
  }
}

function pushAssistantPlaceholder() {
  const id = `assistant-${Date.now()}-${Math.random().toString(36).slice(2)}`
  messages.value.push({
    id,
    role: 'assistant',
    status: 'loading',
    timestamp: new Date().toISOString(),
    blocks: []
  })
  return id
}

function replaceMessage(id, nextMessage) {
  const idx = messages.value.findIndex(m => m.id === id)
  if (idx !== -1) {
    messages.value.splice(idx, 1, nextMessage)
  }
}

function removeMessage(id) {
  const idx = messages.value.findIndex(m => m.id === id)
  if (idx !== -1) messages.value.splice(idx, 1)
}

async function createThread(initialText) {
  try {
    const title = initialText.split(/\s+/).slice(0, 8).join(' ')
    const res = await authFetch(`${API_BASE_URL}/api/chats/threads/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title })
    })
    if (res.ok) {
      const data = await res.json()
      threadId.value = data?.id
      if (threadId.value) {
        skipNextThreadLoad.value = true
        router.push(`/analysis/${threadId.value}`)
      }
    } else {
      throw new Error('Unable to create thread')
    }
  } catch (err) {
    throw new Error(err?.message || 'Unable to create thread')
  }
}

async function persistMessage(id, payload) {
  try {
    await authFetch(`${API_BASE_URL}/api/chats/threads/${id}/messages/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
  } catch (_) {
    // Ignore persistence errors to avoid blocking UX
  }
}

async function askAI(question) {
  const res = await fetch(`${AI}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, top_k: 5, with_sources: true })
  })
  const text = await res.text()
  let data = {}
  try {
    data = text ? JSON.parse(text) : {}
  } catch {
    data = {}
  }
  if (!res.ok) {
    const msg = data?.detail || data?.error || text || `HTTP ${res.status}`
    throw new Error(msg)
  }
  return data
}

function createAssistantMessage(baseId, payload) {
  const answer = payload?.answer || payload?.output || payload?.result || payload?.content || ''
  const citations = normalizeCitations(payload)
  const inlineRefs = payload?.inline_refs || {}
  const blocks = buildBlocks(answer, payload, citations)
  return {
    id: `${baseId}-assistant`,
    role: 'assistant',
    content: answer,
    blocks,
    citations,
    inlineRefs,
    status: 'ready',
    timestamp: new Date().toISOString()
  }
}

function buildBlocks(answer, payload, citations) {
  const blocks = []
  const normalizedText = (answer || '').trim()
  if (normalizedText) {
    blocks.push(...parseTextBlocks(normalizedText))
  }
  const payloadBlocks = Array.isArray(payload?.blocks) ? payload.blocks : []
  payloadBlocks.forEach(block => blocks.push(normalizeBlock(block)))

  const tables = collectTables(payload, answer)
  tables.forEach(table => blocks.push({
    type: 'table',
    headers: table.headers || [],
    rows: table.rows || [],
    caption: table.title || table.caption || null
  }))

  const kpis = collectKpis(payload)
  if (kpis.length) blocks.push({ type: 'kpis', cards: kpis })

  if (citations.length) blocks.push({ type: 'citations', items: citations })

  const download = collectDownload(payload)
  if (download) blocks.push(download)

  const jsonBlocks = collectJsonBlocks(payload)
  jsonBlocks.forEach(block => blocks.push(block))

  return blocks.length ? blocks : [{ type: 'text', content: '—' }]
}

function normalizeBlock(block) {
  if (!block || typeof block !== 'object') return { type: 'text', content: '' }
  if (block.type === 'text') return { type: 'text', content: block.content || '' }
  if (block.type === 'bullets') return { type: 'bullets', items: block.items || [] }
  if (block.type === 'table') return {
    type: 'table',
    headers: block.headers || [],
    rows: block.rows || [],
    caption: block.caption || block.title || ''
  }
  if (block.type === 'kpis') return { type: 'kpis', cards: block.cards || [] }
  if (block.type === 'json') return { type: 'json', code: block.code || block.data, label: block.label }
  if (block.type === 'download') return block
  return block
}

function parseTextBlocks(text) {
  const segments = []
  const lines = text.split(/\r?\n/)
  let buffer = []
  let bullets = []

  const flushParagraph = () => {
    if (buffer.length) {
      segments.push({ type: 'text', content: buffer.join('\n').trim() })
      buffer = []
    }
  }
  const flushBullets = () => {
    if (bullets.length) {
      segments.push({ type: 'bullets', items: bullets.slice() })
      bullets = []
    }
  }

  for (const rawLine of lines) {
    const line = rawLine.trim()
    if (!line) {
      flushBullets()
      flushParagraph()
      continue
    }
    if (/^[-*•]\s+/.test(line)) {
      flushParagraph()
      bullets.push(line.replace(/^[-*•]\s+/, '').trim())
      continue
    }
    flushBullets()
    buffer.push(rawLine)
  }
  flushBullets()
  flushParagraph()
  return segments
}

function collectTables(payload, answer) {
  const tables = []
  if (Array.isArray(payload?.tables)) tables.push(...payload.tables)
  if (Array.isArray(payload?.structured_tables)) tables.push(...payload.structured_tables)
  if (Array.isArray(payload?.structuredTables)) tables.push(...payload.structuredTables)
  if (!tables.length) {
    tables.push(...extractStructuredTables(answer))
  }
  return tables
}

function collectKpis(payload) {
  const cards = []
  const raw = payload?.kpis || payload?.metrics || []
  for (const item of raw) {
    if (!item) continue
    cards.push({
      label: item.label || item.name || 'Metric',
      value: item.value ?? item.score ?? '—',
      trend: (item.trend || 'flat').toLowerCase(),
      delta: item.delta || item.change || ''
    })
  }
  return cards
}

function collectDownload(payload) {
  const url = payload?.download_url || payload?.download?.url
  if (!url) return null
  return {
    type: 'download',
    label: payload?.download_label || payload?.download?.label || 'Download report',
    href: url,
    format: payload?.download?.format || payload?.download_format || ''
  }
}

function collectJsonBlocks(payload) {
  const blocks = []
  const possible = [
    { key: 'json', label: 'JSON' },
    { key: 'debug', label: 'Debug data' },
    { key: 'plan', label: 'Plan' },
    { key: 'raw_json', label: 'Raw JSON' },
    { key: 'outline', label: 'Outline' }
  ]
  possible.forEach(({ key, label }) => {
    if (payload?.[key]) {
      blocks.push({
        type: 'json',
        label,
        code: payload[key]
      })
    }
  })
  return blocks
}

function normalizeCitations(data) {
  const arr = Array.isArray(data?.citations)
    ? data.citations
    : Array.isArray(data?.all_citations)
      ? data.all_citations
      : Array.isArray(data?.sources)
        ? data.sources
        : []
  const seen = new Set()
  const normalized = []
  
  arr.forEach((entry, idx) => {
    if (!entry) return
    const docId = entry.doc_id || entry.documentId || entry.document_id || entry.id || ''
    // Use provided citation ID or fallback to index+1
    const citationId = String(entry.citation_id || entry.citationId || entry.id || (idx + 1))
    
    if (seen.has(citationId)) return
    seen.add(citationId)
    
    const page = typeof entry.page === 'number' && entry.page > 0 ? entry.page : undefined
    normalized.push({
      citationId,
      docId,
      docTitle: entry.doc_title || entry.title || entry.label || docId || 'Source',
      page,
      snippet: entry.snippet || entry.excerpt || '',
      url: entry.url || buildDocumentUrl(docId, page),
      sourceType: entry.source_type || entry.kind || '',
      score: typeof entry.score === 'number' ? entry.score : null
    })
  })
  return normalized
}

function buildDocumentUrl(docId, page) {
  if (!docId) return ''
  const base = `/documents/${docId}`
  return page ? `${base}?p=${page}` : base
}

function extractStructuredTables(raw) {
  const tables = []
  if (!raw) return tables
  const codeBlocks = Array.from(String(raw).matchAll(/```(?:json|table|csv)?([\s\S]*?)```/gi))
  for (const match of codeBlocks) {
    const block = match[1] ? match[1].trim() : ''
    if (!block) continue
    const jsonTable = tryParseJsonTable(block)
    if (jsonTable) {
      tables.push(jsonTable)
      continue
    }
    const delimited = parseDelimitedBlock(block)
    if (delimited) tables.push(delimited)
  }
  if (!tables.length) {
    const fallback = parseDelimitedBlock(raw)
    if (fallback) tables.push(fallback)
  }
  return tables
}

function tryParseJsonTable(text) {
  const trimmed = text?.trim()
  if (!trimmed) return null
  if (!trimmed.startsWith('{') && !trimmed.startsWith('[')) return null
  try {
    const parsed = JSON.parse(trimmed)
    return convertJsonToTable(parsed)
  } catch {
    return null
  }
}

function convertJsonToTable(data) {
  if (Array.isArray(data)) {
    if (!data.length) return null
    if (data.every(item => item && typeof item === 'object' && !Array.isArray(item))) {
      const headers = Array.from(new Set(data.flatMap(item => Object.keys(item || {}))))
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
      return { headers, rows, title: data.title || data.caption }
    }
    if (Array.isArray(data.data)) {
      return convertJsonToTable(data.data)
    }
  }
  return null
}

function normalizeRow(row, headers) {
  if (Array.isArray(row)) return headers.map((_, idx) => formatCell(row[idx]))
  if (row && typeof row === 'object') return headers.map(key => formatCell(row?.[key]))
  return headers.map(() => formatCell(row))
}

function parseDelimitedBlock(text) {
  if (!text) return null
  const lines = String(text).split(/\r?\n/).map(line => line.trim()).filter(Boolean)
  if (lines.length < 2) return null
  const delimiter = detectDelimiter(lines)
  if (!delimiter) return null
  const rows = lines.map(line => splitDelimitedLine(line, delimiter))
  if (!rows.length || rows[0].length < 2) return null
  const headers = rows[0].map((cell, idx) => formatHeader(cell, idx))
  const body = rows.slice(1).map(row => headers.map((_, idx) => formatCell(row[idx])))
  return { headers, rows: body }
}

function detectDelimiter(lines) {
  const firstLine = lines[0] || ''
  const candidates = [
    { char: '\t', score: (firstLine.match(/\t/g) || []).length },
    { char: ',', score: (firstLine.match(/,/g) || []).length },
    { char: ';', score: (firstLine.match(/;/g) || []).length },
    { char: '|', score: (firstLine.match(/\|/g) || []).length }
  ]
  candidates.sort((a, b) => b.score - a.score)
  return candidates[0] && candidates[0].score >= 1 ? candidates[0].char : null
}

function splitDelimitedLine(line, delimiter) {
  if (delimiter === '|') {
    const cleaned = line.replace(/^\|/, '').replace(/\|$/, '')
    return cleaned.split('|').map(cell => cell.trim())
  }
  if (delimiter === '\t') return line.split('\t').map(cell => cell.trim())
  return splitCsvLine(line, delimiter)
}

function splitCsvLine(line, delimiter = ',') {
  const cells = []
  let current = ''
  let inQuotes = false
  for (let i = 0; i < line.length; i++) {
    const ch = line[i]
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"'
        i++
      } else {
        inQuotes = !inQuotes
      }
      continue
    }
    if (ch === delimiter && !inQuotes) {
      cells.push(current.trim())
      current = ''
      continue
    }
    current += ch
  }
  cells.push(current.trim())
  return cells.map(cell => cell.replace(/^"|"$/g, ''))
}

function formatHeader(value, idx) {
  const text = formatCell(value)
  return text || `Column ${idx + 1}`
}

function formatCell(value) {
  if (value === null || value === undefined) return ''
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value)
    } catch {
      return ''
    }
  }
  return String(value)
}

function scrollToBottom() {
  nextTick(() => {
    try {
      const el = messagesWrap.value
      if (!el) return
      el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
    } catch (_) {
      // ignore
    }
  })
}

async function loadThread(id) {
  if (!id) return
  try {
    const res = await authFetch(`${API_BASE_URL}/api/chats/threads/${id}/messages/`)
    if (!res.ok) return
    const arr = await res.json()
    const serverMessages = (arr || []).map(item => hydrateServerMessage(item))
    messages.value = serverMessages
    threadId.value = id
    scrollToBottom()
  } catch (_) {
    // ignore load errors
  }
}

function hydrateServerMessage(raw) {
  const citations = Array.isArray(raw?.citations) ? raw.citations : []
  const blocks = buildBlocks(raw?.content || '', { ...raw, citations }, citations)
  return {
    id: `db-${raw?.id || Math.random().toString(36).slice(2)}`,
    role: raw?.role || 'assistant',
    content: raw?.content,
    blocks,
    citations,
    inlineRefs: raw?.inline_refs || {},
    status: 'ready',
    timestamp: raw?.created_at || raw?.updated_at || new Date().toISOString()
  }
}

function resetChat() {
  messages.value = []
  threadId.value = null
  draft.value = ''
}

function handleCitation(payload) {
  const docId = payload?.docId || payload?.documentId || payload?.document_id
  const page = payload?.page
  const detail = {
    page,
    title: payload?.docTitle || payload?.title || payload?.label,
    documentId: docId
  }
  window.dispatchEvent(new CustomEvent('open-citation', { detail }))
  const url = payload?.url || buildDocumentUrl(docId, page)
  if (url && url.startsWith('/')) {
    router.push(url)
    return
  }
  if (url) {
    window.open(url, '_blank', 'noopener')
    return
  }
  if (docId) {
    router.push(`/documents/${docId}`)
  }
}

onMounted(() => {
  const id = route.params?.id
  if (id) {
    loadThread(String(id))
  } else {
    resetChat()
  }
})

watch(() => route.params?.id, (nextId) => {
  if (nextId) {
    const idStr = String(nextId)
    if (skipNextThreadLoad.value && idStr === String(threadId.value || '')) {
      skipNextThreadLoad.value = false
      return
    }
    loadThread(idStr)
  }
  else resetChat()
})
</script>

<style scoped>
.analysis-page {
  min-height: 100vh;
  padding: clamp(16px, 4vw, 48px);
  background: linear-gradient(180deg, #f5f7ff 0%, #eef2ff 70%);
}

.chat-stage {
  display: flex;
  justify-content: center;
}

.chat-card {
  width: min(1100px, 100%);
  background: #fff;
  border-radius: 32px;
  padding: clamp(20px, 3vw, 36px);
  box-shadow: 0 30px 80px rgba(15, 23, 42, 0.1);
  border: 1px solid rgba(65, 105, 225, 0.1);
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-height: calc(100vh - 220px);
}

.prompt-pills,
.pill-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}

.pill {
  border: none;
  background: rgba(65, 105, 225, 0.12);
  color: #1b2c48;
  border-radius: 999px;
  padding: 10px 18px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.2s ease;
}

.pill:hover:not(:disabled) {
  background: rgba(65, 105, 225, 0.2);
  transform: translateY(-1px);
}

.pill:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.messages-pane {
  flex: 1;
  min-height: 320px;
  overflow-y: auto;
  padding-right: 8px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #5b6b88;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.empty-state h2 {
  font-size: 28px;
  color: #1b2c48;
  margin: 0;
}

.composer-block {
  padding-top: 8px;
  border-top: 1px solid rgba(65, 105, 225, 0.1);
}

.composer-meta {
  margin-top: 8px;
  font-size: 13px;
  color: #5b6b88;
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #f97316;
}

.status-dot.online {
  background: #22c55e;
}

.error {
  color: #dc2626;
  margin-top: 8px;
  font-weight: 600;
}

@media (max-width: 768px) {
  .chat-card {
    border-radius: 20px;
    padding: 20px;
  }
}
</style>
