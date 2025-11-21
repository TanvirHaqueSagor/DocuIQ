<template>
  <div class="structured-blocks">
    <template v-for="(block, idx) in blocks" :key="`block-${idx}-${block.type}`">
      <div v-if="block.type === 'text'" class="block block-text">
        <p v-for="(paragraph, pIdx) in toParagraphs(block.content)" :key="`p-${pIdx}`">
          <template v-for="(segment, sIdx) in parseWithCitations(paragraph)" :key="`s-${sIdx}`">
            <span v-if="segment.text">{{ segment.text }}</span>
            <button
              v-else-if="segment.ref && getCitation(segment.ref)"
              class="citation-ref"
              @click="openCitationRef(segment.ref)"
            >[S{{ segment.ref }}]</button>
          </template>
        </p>
      </div>

      <ul v-else-if="block.type === 'bullets'" class="block block-bullets">
        <li v-for="(item, bIdx) in block.items" :key="`b-${bIdx}`">{{ item }}</li>
      </ul>

      <div v-else-if="block.type === 'table'" class="block block-table">
        <div class="table-title" v-if="block.caption">{{ block.caption }}</div>
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th v-for="(header, hIdx) in block.headers" :key="`h-${hIdx}`">{{ header }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!block.rows.length">
                <td :colspan="Math.max(block.headers.length, 1)" class="muted">No data available</td>
              </tr>
              <tr v-for="(row, rIdx) in block.rows" :key="`r-${rIdx}`">
                <td v-for="(cell, cIdx) in row" :key="`c-${rIdx}-${cIdx}`">{{ cell }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-else-if="block.type === 'kpis'" class="block block-kpi">
        <div
          class="kpi-card"
          v-for="(card, kIdx) in block.cards"
          :key="`kpi-${kIdx}`"
        >
          <div class="kpi-label">{{ card.label }}</div>
          <div class="kpi-value">{{ card.value }}</div>
          <div class="kpi-trend" :class="card.trend">
            <span class="trend-icon">
              <svg v-if="card.trend === 'up'" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M2 10.5 6.5 6l3 3L14 4.5V8h2V1h-7v2h3.5L9.5 6.5l-3-3L0 10.5z"/></svg>
              <svg v-else-if="card.trend === 'down'" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="m2 5.5 4.5 4.5 3-3L14 11.5V8h2v7h-7v-2h3.5L9.5 9.5l-3 3L0 5.5z"/></svg>
              <svg v-else viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M0 7h16v2H0z"/></svg>
            </span>
            <span>{{ trendLabel(card.trend, card.delta) }}</span>
          </div>
        </div>
      </div>

      <div v-else-if="block.type === 'citations'" class="block block-citations">
        <button
          class="citation-chip"
          v-for="(citation, cIdx) in block.items"
          :key="`citation-${cIdx}`"
          type="button"
          @click="emitCitation(citation)"
        >
          <div class="chip-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <line x1="10" y1="9" x2="8" y2="9"></line>
            </svg>
          </div>
          <div class="chip-content">
            <span class="chip-title">{{ citationLabel(citation) }}</span>
            <div class="chip-details" v-if="citation.page || citation.snippet">
              <span class="chip-page" v-if="citation.page">p. {{ citation.page }}</span>
              <span class="chip-snippet" v-if="citation.snippet">{{ citation.snippet }}</span>
            </div>
          </div>
        </button>
      </div>

      <div v-else-if="block.type === 'download'" class="block block-download">
        <a
          class="download-link"
          :href="block.href"
          target="_blank"
          rel="noopener"
        >
          {{ block.label || 'Download file' }}
          <span v-if="block.format" class="format">{{ block.format }}</span>
        </a>
      </div>

      <div v-else-if="block.type === 'json'" class="block block-json">
        <div class="json-header">
          <span>{{ block.label || 'JSON' }}</span>
          <button type="button" class="json-toggle" @click="toggleJson(idx)">
            {{ isJsonOpen(idx) ? 'Hide' : 'Show' }}
          </button>
        </div>
        <pre v-if="isJsonOpen(idx)"><code>{{ prettyJson(block.code) }}</code></pre>
      </div>

      <div v-else class="block block-text">
        <p>{{ block.content }}</p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { reactive, computed } from 'vue'

const props = defineProps({
  blocks: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['open-citation'])
const openState = reactive({})
const blocks = computed(() => props.blocks || [])

function toParagraphs(text) {
  if (!text) return []
  return text.split(/\n+/).map(p => p.trim()).filter(Boolean)
}

function emitCitation(citation) {
  emit('open-citation', citation)
}

function citationLabel(citation) {
  return citation?.docTitle || citation?.title || citation?.label || citation?.document || 'Source'
}

function trendLabel(trend, delta) {
  if (delta) return delta
  if (trend === 'up') return 'Higher'
  if (trend === 'down') return 'Lower'
  return 'Flat'
}

function isJsonOpen(idx) {
  return !!openState[idx]
}

function toggleJson(idx) {
  openState[idx] = !openState[idx]
}

function prettyJson(code) {
  if (typeof code === 'string') return code
  try {
    return JSON.stringify(code, null, 2)
  } catch {
    return ''
  }
}

const allCitations = computed(() => {
  const citations = []
  if (!props.blocks) return citations
  for (const block of props.blocks) {
    if (block.type === 'citations' && Array.isArray(block.items)) {
      citations.push(...block.items)
    }
  }
  return citations
})

function parseWithCitations(text) {
  if (!text) return []
  const regex = /\[S(\d+)\]/g
  const segments = []
  let lastIndex = 0
  let match

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      segments.push({ text: text.slice(lastIndex, match.index) })
    }
    const ref = parseInt(match[1], 10)
    segments.push({ ref })
    lastIndex = regex.lastIndex
  }

  if (lastIndex < text.length) {
    segments.push({ text: text.slice(lastIndex) })
  }
  return segments
}

function getCitation(ref) {
  const refStr = String(ref)
  // 1. Try to find by exact ID match
  let citation = allCitations.value.find(c => String(c.citationId) === refStr || String(c.id) === refStr)
  
  // 2. Fallback: treat ref as 1-based index
  if (!citation) {
    const idx = parseInt(ref, 10)
    if (Number.isFinite(idx) && idx > 0) {
      citation = allCitations.value[idx - 1]
    }
  }
  return citation
}

function openCitationRef(ref) {
  const citation = getCitation(ref)
  if (citation) {
    emit('open-citation', citation)
  }
}
</script>

<style scoped>
.structured-blocks {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.block {
  width: 100%;
}

.block-text p {
  margin: 0 0 10px;
  line-height: 1.5;
  color: #1b2c48;
}

.block-bullets {
  list-style: disc;
  padding-left: 20px;
  margin: 0;
  color: #1b2c48;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.block-table {
  border: 1px solid rgba(65, 105, 225, 0.2);
  border-radius: 12px;
  padding: 12px;
  background: #fff;
  box-shadow: inset 0 0 0 1px rgba(99, 102, 241, 0.04);
}

.table-title {
  font-weight: 700;
  color: #1b2c48;
  margin-bottom: 8px;
}

.table-scroll {
  max-height: 320px;
  overflow: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

thead th {
  position: sticky;
  top: 0;
  background: #f3f6ff;
  text-align: left;
  padding: 8px;
  font-weight: 600;
  color: #1b2c48;
  border-bottom: 1px solid rgba(65, 105, 225, 0.2);
}

tbody td {
  padding: 8px;
  border-bottom: 1px solid rgba(65, 105, 225, 0.1);
  color: #1b2c48;
}

.block-kpi {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
}

.kpi-card {
  background: linear-gradient(145deg, #f4f7ff, #ffffff);
  border: 1px solid rgba(65, 105, 225, 0.15);
  border-radius: 16px;
  padding: 12px;
  box-shadow: 0 8px 20px rgba(37, 50, 74, 0.08);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.kpi-label {
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #5b6b88;
}

.kpi-value {
  font-size: 24px;
  font-weight: 700;
  color: #1b2c48;
}

.kpi-trend {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.kpi-trend.up {
  color: #0f9d58;
}

.kpi-trend.down {
  color: #e14c4c;
}

.kpi-trend.flat {
  color: #5b6b88;
}

.trend-icon {
  width: 16px;
  height: 16px;
  display: inline-flex;
}

.block-citations {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.citation-chip {
  border: 1px solid rgba(65, 105, 225, 0.15);
  background: #fff;
  color: #1b2c48;
  border-radius: 12px;
  padding: 10px 12px;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  width: 100%;
  max-width: 300px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.03);
}

.citation-chip:hover {
  border-color: #4169e1;
  background: #f8fbff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(65, 105, 225, 0.15);
}

.chip-icon {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(65, 105, 225, 0.1);
  color: #4169e1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chip-icon svg {
  width: 18px;
  height: 18px;
}

.chip-content {
  flex: 1;
  min-width: 0; /* text truncation */
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.chip-title {
  font-size: 13px;
  font-weight: 600;
  color: #1b2c48;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chip-details {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #5b6b88;
}

.chip-page {
  background: rgba(0,0,0,0.05);
  padding: 1px 4px;
  border-radius: 4px;
  font-weight: 500;
  white-space: nowrap;
}

.chip-snippet {
  opacity: 0.85;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.block-download {
  display: flex;
  justify-content: flex-start;
}

.download-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 999px;
  background: #4169e1;
  color: #fff;
  font-weight: 600;
  text-decoration: none;
  box-shadow: 0 8px 20px rgba(65, 105, 225, 0.35);
}

.download-link .format {
  font-size: 12px;
  opacity: 0.8;
}

.block-json {
  border: 1px solid rgba(65, 105, 225, 0.2);
  border-radius: 12px;
  background: #f8fbff;
}

.json-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  font-weight: 600;
  color: #1b2c48;
}

.json-toggle {
  border: none;
  background: transparent;
  color: #4169e1;
  font-weight: 600;
  cursor: pointer;
}

.block-json pre {
  margin: 0;
  padding: 14px;
  background: #111827;
  color: #e5e7eb;
  border-radius: 0 0 12px 12px;
  overflow-x: auto;
}

.muted {
  color: #94a3b8;
  text-align: center;
}

.citation-ref {
  display: inline;
  background: none;
  border: none;
  padding: 0;
  margin: 0 1px;
  color: #4169e1;
  font-weight: 600;
  cursor: pointer;
  font-size: inherit;
  font-family: inherit;
}

.citation-ref:hover {
  text-decoration: underline;
}
</style>
