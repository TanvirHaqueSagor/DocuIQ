<template>
  <div class="structured-blocks">
    <template v-for="(block, idx) in blocks" :key="`block-${idx}-${block.type}`">
      <div v-if="block.type === 'text'" class="block block-text">
        <p v-for="(paragraph, pIdx) in toParagraphs(block.content)" :key="`p-${pIdx}`">{{ paragraph }}</p>
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
          <span class="chip-title">{{ citationLabel(citation) }}</span>
          <span class="chip-meta" v-if="citation.page">Page {{ citation.page }}</span>
          <span class="chip-snippet" v-if="citation.snippet">{{ citation.snippet }}</span>
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
  border: none;
  background: rgba(65, 105, 225, 0.1);
  color: #1b2c48;
  border-radius: 999px;
  padding: 8px 14px;
  font-weight: 600;
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.2s ease;
}

.citation-chip:hover {
  background: rgba(65, 105, 225, 0.2);
  transform: translateY(-1px);
}

.chip-meta {
  font-size: 12px;
  color: #5b6b88;
}

.chip-snippet {
  font-size: 12px;
  color: #1b2c48;
  opacity: 0.85;
  text-align: left;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
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
</style>
