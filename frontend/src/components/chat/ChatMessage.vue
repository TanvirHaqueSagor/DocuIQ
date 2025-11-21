<template>
  <div :class="['docuiq-message', message.role, { loading: isLoading }]">
    <div v-if="message.role === 'assistant'" class="avatar" aria-hidden="true">
      <span>IQ</span>
    </div>
    <div class="bubble">
      <div v-if="isLoading" class="loading-wrapper">
        <LoadingBubble />
      </div>
      <StructuredBlocks
        v-else
        :blocks="displayBlocks"
        @open-citation="onOpenCitation"
      />
      <div class="meta">
        <span class="author">{{ senderLabel }}</span>
        <span class="time">{{ timestampLabel }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import StructuredBlocks from './StructuredBlocks.vue'
import LoadingBubble from './LoadingBubble.vue'

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['open-citation'])

const isLoading = computed(() => props.message?.status === 'loading')
const displayBlocks = computed(() => {
  if (Array.isArray(props.message?.blocks) && props.message.blocks.length) {
    return props.message.blocks
  }
  if (props.message?.content) {
    return [{ type: 'text', content: props.message.content }]
  }
  return []
})

const senderLabel = computed(() => (props.message?.role === 'user' ? 'You' : 'DocuIQ'))
const timestampLabel = computed(() => {
  const raw = props.message?.timestamp
  if (!raw) return ''
  try {
    const date = new Date(raw)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch {
    return raw
  }
})

function onOpenCitation(payload) {
  emit('open-citation', payload)
}
</script>

<style scoped>
.docuiq-message {
  display: flex;
  gap: 14px;
  margin-bottom: 20px;
}

.docuiq-message.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 38px;
  height: 38px;
  border-radius: 14px;
  background: linear-gradient(140deg, #4169e1, #7ba3ff);
  color: #fff;
  font-weight: 700;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 25px rgba(65, 105, 225, 0.35);
}

.bubble {
  flex: 1;
  border-radius: 20px;
  padding: 18px;
  position: relative;
  background: #ffffff;
  border: 1px solid rgba(65, 105, 225, 0.15);
  box-shadow: 0 24px 45px rgba(15, 23, 42, 0.08);
}

.docuiq-message.user .bubble {
  background: #4169e1;
  color: #fff;
  border: none;
  box-shadow: none;
}

.docuiq-message.user .bubble :deep(p),
.docuiq-message.user .bubble :deep(li),
.docuiq-message.user .bubble :deep(table),
.docuiq-message.user .bubble :deep(td),
.docuiq-message.user .bubble :deep(th),
.docuiq-message.user .bubble :deep(.citation-chip) {
  color: #fff;
}

.docuiq-message.user .bubble :deep(.citation-chip) {
  background: rgba(255, 255, 255, 0.2);
  border-color: transparent;
}

.docuiq-message.user .bubble :deep(.citation-ref) {
  color: #fff;
  text-decoration: underline;
}

.docuiq-message.user .bubble :deep(.chip-title),
.docuiq-message.user .bubble :deep(.chip-details),
.docuiq-message.user .bubble :deep(.chip-snippet),
.docuiq-message.user .bubble :deep(.chip-page) {
  color: #fff;
}

.docuiq-message.user .bubble :deep(.chip-details) {
  opacity: 0.9;
}

.docuiq-message.user .bubble :deep(.chip-icon) {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.loading-wrapper {
  padding: 8px 0;
}

.meta {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  font-size: 12px;
  margin-top: 12px;
  color: #5b6b88;
}

.docuiq-message.user .meta {
  color: rgba(255, 255, 255, 0.8);
}

.author {
  font-weight: 600;
}
</style>
