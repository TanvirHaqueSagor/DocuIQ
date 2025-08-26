# ==================================================
# src/components/dashboard/UsageSparkline.vue
# ==================================================
<template>
  <div class="sparkline-wrap" role="img" :aria-label="`Usage for ${labels.length} days`">
    <svg :viewBox="`0 0 ${width} ${height}`" preserveAspectRatio="none" class="sparkline">
      <polyline :points="points" fill="none" stroke="#111827" stroke-width="2" stroke-linecap="round" />
      <template v-for="(p, i) in dots" :key="i">
        <circle :cx="p.x" :cy="p.y" r="3" fill="#111827" />
      </template>
    </svg>
    <div class="legend">
      <span v-for="(l,i) in labels" :key="i">{{ l }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ series: number[]; labels: string[] }>()

const width = 600, height = 160, pad = 12

const maxVal = computed(() => Math.max(1, ...props.series))
const stepX = computed(() => props.series.length > 1 ? (width - pad*2) / (props.series.length - 1) : width)

const coords = computed(() => props.series.map((v, i) => ({
  x: pad + i * stepX.value,
  y: pad + (height - pad*2) * (1 - (v / maxVal.value)),
})))

const points = computed(() => coords.value.map(p => `${p.x},${p.y}`).join(' '))
const dots = computed(() => coords.value)
</script>

<style scoped>
.sparkline-wrap{ width:100%; }
.sparkline{
  width:100%; height:200px; border-radius:14px;
  background:
    radial-gradient(1200px 300px at -10% -40%, rgba(124,92,255,.12), transparent),
    radial-gradient(800px 300px at 120% 120%, rgba(34,211,238,.12), transparent);
}
</style>

