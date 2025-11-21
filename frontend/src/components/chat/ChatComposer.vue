<template>
  <div class="composer">
    <textarea
      ref="inputRef"
      class="composer-input"
      :placeholder="placeholder"
      :value="modelValue"
      :disabled="disabled || loading"
      rows="1"
      @input="onInput"
      @keydown="onKeydown"
    ></textarea>
    <button
      class="composer-send"
      type="button"
      :disabled="!canSend && !loading"
      @click="emitSubmit"
      :aria-label="loading ? 'Generating response' : 'Send message'"
    >
      <div v-if="loading" class="spinner"></div>
      <svg v-else viewBox="0 0 24 24" aria-hidden="true">
        <path fill="currentColor" d="M2 3.5 22 12 2 20.5l5-7-5-7.5Zm5.5 7.5L4.8 7.7 15 12 4.8 16.3 7.5 11Z" />
      </svg>
    </button>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  disabled: Boolean,
  loading: Boolean,
  placeholder: {
    type: String,
    default: 'Ask something...'
  }
})

const emit = defineEmits(['update:modelValue', 'submit'])
const inputRef = ref(null)

const canSend = computed(() => {
  const text = props.modelValue || ''
  return !!text.trim() && !props.loading && !props.disabled
})

function onInput(event) {
  emit('update:modelValue', event.target.value)
  autoSize()
}

function onKeydown(event) {
  if (event.key !== 'Enter') return
  if (event.shiftKey) return
  event.preventDefault()
  emitSubmit()
}

function emitSubmit() {
  if (!canSend.value) return
  emit('submit')
}

function autoSize() {
  nextTick(() => {
    const el = inputRef.value
    if (!el) return
    el.style.height = 'auto'
    const next = Math.min(el.scrollHeight, 220)
    el.style.height = `${next}px`
    el.style.overflowY = el.scrollHeight > 220 ? 'auto' : 'hidden'
  })
}

watch(() => props.modelValue, () => autoSize())
onMounted(() => autoSize())
</script>

<style scoped>
.composer {
  position: relative;
  background: #f6f8ff;
  border: 1px solid rgba(65, 105, 225, 0.2);
  border-radius: 999px;
  padding: 10px 56px 10px 20px;
  display: flex;
  align-items: center;
  box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.05);
}

.composer-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 16px;
  color: #1b2c48;
  resize: none;
  line-height: 1.4;
  min-height: 28px;
}

.composer-input:focus {
  outline: none;
}

.composer-send {
  position: absolute;
  right: 8px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: #4169e1;
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 10px 25px rgba(65, 105, 225, 0.35);
  transition: transform 0.15s ease, opacity 0.2s ease;
}

.composer-send:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}

.composer-send svg {
  width: 18px;
  height: 18px;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
