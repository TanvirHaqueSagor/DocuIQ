<template>
  <button
    class="citation-chip"
    type="button"
    :title="citation.snippet || ''"
    @click="onClick"
  >
    <div class="chip-icon" :aria-label="sourceLabel">
      <span>{{ icon }}</span>
    </div>
    <div class="chip-content">
      <div class="chip-header">
        <span class="chip-title">{{ titleLabel }}</span>
        <span class="chip-id" v-if="displayId">[{{ displayId }}]</span>
      </div>
      <div class="chip-meta" v-if="metaLabel">{{ metaLabel }}</div>
      <div class="chip-snippet" v-if="citation.snippet">{{ citation.snippet }}</div>
    </div>
  </button>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  citation: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['open'])

const sourceType = computed(() => (props.citation?.sourceType || props.citation?.source_type || props.citation?.kind || 'document').toLowerCase())
const displayId = computed(() => props.citation?.citationId || props.citation?.citation_id || props.citation?.id || '')
const baseTitle = computed(() => props.citation?.docTitle || props.citation?.doc_title || props.citation?.title || props.citation?.label || props.citation?.document || 'Source')

const icon = computed(() => {
  const map = {
    pdf: '📄',
    web: '🌐',
    gdrive: '📁',
    drive: '📁',
    sharepoint: '📁',
    onedrive: '📁',
    email: '✉️',
    slack: '💬',
    teams: '💬',
    db: '🗄️'
  }
  return map[sourceType.value] || '📎'
})

const sourceLabel = computed(() => {
  if (sourceType.value === 'web') return 'Website'
  if (sourceType.value === 'pdf') return 'PDF'
  if (sourceType.value === 'email') return 'Email'
  if (sourceType.value === 'slack' || sourceType.value === 'teams') return 'Chat'
  if (sourceType.value === 'db') return 'Database'
  return 'Document'
})

const titleLabel = computed(() => {
  const title = baseTitle.value
  switch (sourceType.value) {
    case 'pdf':
      return `${title}${props.citation?.page ? ` (p.${props.citation.page})` : ''}`
    case 'web':
      return `Website – ${title}`
    case 'email':
      return `Email – ${title}`
    case 'slack':
      return `Slack – ${props.citation?.extra?.channel || props.citation?.channel || title}`
    case 'teams':
      return `Teams – ${props.citation?.extra?.channel || props.citation?.channel || title}`
    case 'db':
      return `Database – ${props.citation?.table || title}`
    default:
      return title
  }
})

const metaLabel = computed(() => {
  if (sourceType.value === 'pdf' && props.citation?.page) return `Page ${props.citation.page}`
  if (sourceType.value === 'web' && props.citation?.url) return props.citation.url
  if (sourceType.value === 'gdrive' || sourceType.value === 'sharepoint' || sourceType.value === 'onedrive') {
    return props.citation?.url || ''
  }
  if (sourceType.value === 'email') {
    if (props.citation?.ts) return `Sent ${props.citation.ts}`
    if (props.citation?.message_id) return `Message ${props.citation.message_id}`
    return ''
  }
  if (sourceType.value === 'slack' || sourceType.value === 'teams') {
    const channel = props.citation?.extra?.channel || props.citation?.channel
    if (channel && props.citation?.ts) return `#${channel} · ${props.citation.ts}`
    if (channel) return `#${channel}`
    return props.citation?.ts || ''
  }
  if (sourceType.value === 'db') {
    const parts = []
    if (props.citation?.table) parts.push(props.citation.table)
    if (props.citation?.row_id || props.citation?.rowId) parts.push(`row ${props.citation.row_id || props.citation.rowId}`)
    if (props.citation?.column) parts.push(`column ${props.citation.column}`)
    return parts.join(' · ')
  }
  return props.citation?.url || ''
})

const targetHref = computed(() => {
  const url = props.citation?.url || props.citation?.origin_url
  const docId = props.citation?.docId || props.citation?.doc_id
  const page = props.citation?.page
  if (url) return url
  if (sourceType.value === 'pdf' && docId) {
    return page ? `/documents/${docId}?p=${page}` : `/documents/${docId}`
  }
  if (docId) return `/documents/${docId}`
  return ''
})

function onClick() {
  emit('open', { citation: props.citation, href: targetHref.value })
}
</script>

<style scoped>
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
  max-width: 340px;
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
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: rgba(65, 105, 225, 0.12);
  color: #4169e1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.chip-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chip-header {
  display: flex;
  align-items: center;
  gap: 6px;
}

.chip-title {
  font-size: 13px;
  font-weight: 600;
  color: #1b2c48;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chip-id {
  font-size: 11px;
  color: #5b6b88;
  border: 1px solid rgba(65, 105, 225, 0.2);
  border-radius: 6px;
  padding: 2px 5px;
}

.chip-meta {
  font-size: 11px;
  color: #5b6b88;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chip-snippet {
  font-size: 12px;
  color: #1b2c48;
  opacity: 0.9;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
