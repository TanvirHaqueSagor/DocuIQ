# ============================================
# src/components/dashboard/StatsCard.vue
# ============================================
<template>
  <div class="stat-card">
    <div class="left">
      <div class="icon" aria-hidden="true">{{ icon }}</div>
      <div>
        <div class="title">{{ title }}</div>
        <div class="value">{{ value ?? '—' }}</div>
      </div>
    </div>
    <div class="delta" :class="deltaClass">
      <span v-if="delta !== undefined && delta !== null">{{ signedDelta }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ icon?: string; title: string; value: string | number | null; delta?: number | string | null; isGoodDown?: boolean }>()

const parsedDelta = computed(() => {
  if (typeof props.delta === 'number') {
    return Number.isFinite(props.delta) ? props.delta : null
  }
  if (typeof props.delta === 'string') {
    const numericPart = props.delta.match(/-?\d+(\.\d+)?/)
    if (!numericPart) return null
    const parsed = parseFloat(numericPart[0])
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
})

const isUp = computed(() => {
  if (parsedDelta.value === null) return true
  return parsedDelta.value >= 0
})

const formatNumeric = (value: number) => {
  const abs = Math.abs(value)
  return Number.isInteger(abs) ? abs.toString() : abs.toFixed(2).replace(/\.?0+$/, '')
}

const signedDelta = computed(() => {
  if (typeof props.delta === 'string') {
    const trimmed = props.delta.trim()
    if (!trimmed) return ''
    const hasSign = /^[+-]/.test(trimmed)
    return hasSign ? trimmed : `${isUp.value ? '+' : ''}${trimmed}`
  }
  if (parsedDelta.value === null) return ''
  return `${parsedDelta.value >= 0 ? '+' : '-'}${formatNumeric(parsedDelta.value)}%`
})

const deltaClass = computed(() => ({
  up: isUp.value && !props.isGoodDown,
  down: !isUp.value && !props.isGoodDown,
  goodDown: !isUp.value && props.isGoodDown,
  goodUp: isUp.value && props.isGoodDown,
}))
</script>

<style scoped>
.stat-card{
  display:flex; align-items:center; justify-content:space-between; padding:16px;
  background:linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01));
  border:1px solid rgba(124,92,255,.18); border-radius:14px; color:var(--txt);
  transition: transform .15s ease, box-shadow .15s ease;
}
.stat-card:hover{ transform: translateY(-2px); box-shadow:0 10px 28px rgba(2,6,23,0.18); }
.left{ display:flex; gap:12px; align-items:center; }
.icon{ font-size:22px; filter: drop-shadow(0 6px 14px rgba(124,92,255,.35)); }
.title{ font-size:12px; color:var(--muted); }
.value{ font-size:22px; font-weight:800; letter-spacing:.2px; }
.delta{ font-weight:700; }
.up .delta{ color:#16a34a; }
.down .delta{ color:#dc2626; }
.goodDown .delta{ color:#16a34a; }
.goodUp .delta{ color:#2563eb; }
</style>
