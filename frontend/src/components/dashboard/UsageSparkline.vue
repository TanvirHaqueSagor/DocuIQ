<template>
  <div class="usage-card" role="img" :aria-label="chartAriaLabel">
    <header class="usage-head">
      <div class="usage-summary">
        <p class="usage-title">{{ t('usageActivitySpan', { days: seriesLength }) }}</p>
      </div>
      <div class="usage-metrics">
        <span class="metric-pill">
          {{ t('usagePeak') }}: <strong>{{ peakValueDisplay }}</strong>
        </span>
        <span class="metric-pill">
          {{ t('usageTotal') }}: <strong>{{ totalValueDisplay }}</strong>
        </span>
      </div>
    </header>

    <div v-if="seriesLength" class="chart-wrap">
      <div class="chart-canvas" ref="canvasEl">
        <svg
          :viewBox="`0 0 ${width} ${height}`"
          preserveAspectRatio="none"
          class="chart-svg"
          @mousemove="onPointerMove"
          @mouseleave="resetActive"
        >
          <defs>
            <linearGradient id="usageAreaGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="rgba(59, 130, 246, 0.35)" />
              <stop offset="100%" stop-color="rgba(59, 130, 246, 0)" />
            </linearGradient>
            <linearGradient id="usageLineGradient" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stop-color="#2563eb" />
              <stop offset="100%" stop-color="#0ea5e9" />
            </linearGradient>
          </defs>

          <g class="grid-lines">
            <line
              v-for="line in yGrid"
              :key="line.label"
              :x1="leftPad"
              :x2="width - rightPad"
              :y1="line.y"
              :y2="line.y"
            />
            <text
              v-for="line in yGrid"
              :key="`label-${line.label}`"
              :x="leftPad - 8"
              :y="line.y + 4"
              text-anchor="end"
            >
              {{ line.label }}
            </text>
          </g>

          <path
            v-if="areaPath"
            class="area-path"
            :d="areaPath"
            fill="url(#usageAreaGradient)"
          />

          <path
            v-if="linePath"
            class="line-path"
            :d="linePath"
            stroke="url(#usageLineGradient)"
          />

          <g class="point-dots">
            <circle
              v-for="(point, index) in points"
              :key="index"
              :cx="point.x"
              :cy="point.y"
              r="2.4"
              :class="{ active: currentIndex === index }"
            />
          </g>

          <g class="x-axis">
            <line
              :x1="leftPad"
              :x2="width - rightPad"
              :y1="height - bottomPad"
              :y2="height - bottomPad"
              class="axis-base"
            />
            <g v-for="tick in xTicks" :key="tick.label">
              <line
                :x1="tick.x"
                :x2="tick.x"
                :y1="height - bottomPad"
                :y2="height - bottomPad + 8"
                class="axis-tick"
              />
              <text
                :x="tick.x"
                :y="height - bottomPad + 22"
                text-anchor="middle"
                class="axis-label"
              >
                {{ tick.label }}
              </text>
            </g>
          </g>
        </svg>

        <div
          v-if="currentIndex >= 0"
          class="tooltip"
          :style="tooltipStyle"
        >
          <div class="tooltip-date">{{ currentEntry.dateLabel }}</div>
          <div class="tooltip-value">{{ currentEntry.valueLabel }}</div>
        </div>
      </div>
    </div>

    <div v-else class="empty">
      <span>{{ t('usageEmpty') }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps<{ series: number[]; labels: string[] }>()

const { t } = useI18n()

const width = 640
const height = 260
const rightPad = 18
const leftPad = 26
const topPad = 26
const bottomPad = 56
const chartWidth = width - leftPad - rightPad
const chartHeight = height - topPad - bottomPad

function niceNumber(value: number, round: boolean) {
  if (!isFinite(value) || value === 0) return 0
  const exponent = Math.floor(Math.log10(Math.abs(value)))
  const fraction = value / Math.pow(10, exponent)
  let niceFraction: number
  if (round) {
    if (fraction < 1.5) niceFraction = 1
    else if (fraction < 3) niceFraction = 2
    else if (fraction < 7) niceFraction = 5
    else niceFraction = 10
  } else {
    if (fraction <= 1) niceFraction = 1
    else if (fraction <= 2) niceFraction = 2
    else if (fraction <= 5) niceFraction = 5
    else niceFraction = 10
  }
  return niceFraction * Math.pow(10, exponent)
}

function computeScale(maxValue: number, desiredSteps: number) {
  if (!isFinite(maxValue) || maxValue <= 0) {
    return { max: 1, step: 1 }
  }
  const rawStep = maxValue / Math.max(1, desiredSteps - 1)
  let niceStep = niceNumber(rawStep, true)
  if (!isFinite(niceStep) || niceStep <= 0) {
    niceStep = rawStep || 1
  }
  niceStep = Math.max(1, Math.round(niceStep))
  const niceMax = Math.max(niceStep, Math.ceil(maxValue / niceStep) * niceStep)
  return { max: niceMax, step: niceStep }
}

function formatValue(value: number) {
  if (!isFinite(value)) return '0'
  return Math.round(value).toLocaleString()
}

function formatLabel(raw: string) {
  const date = new Date(raw)
  if (Number.isNaN(date.getTime())) return raw
  const today = new Date()
  const showYear = date.getFullYear() !== today.getFullYear()
  const opts: Intl.DateTimeFormatOptions = showYear
    ? { month: 'short', day: 'numeric', year: 'numeric' }
    : { month: 'short', day: 'numeric' }
  try {
    return new Intl.DateTimeFormat(undefined, opts).format(date)
  } catch {
    return raw
  }
}

const seriesLength = computed(() => props.series.length)

const rawData = computed(() =>
  props.series.map((value, index) => {
    const numeric = Math.max(0, Number(value) || 0)
    const iso = props.labels[index] || ''
    const label = formatLabel(iso) || iso || `Day ${index + 1}`
    return { numeric, iso, label }
  }),
)

const actualMax = computed(() =>
  rawData.value.reduce((acc, item) => Math.max(acc, item.numeric), 0),
)

const totalValue = computed(() =>
  rawData.value.reduce((sum, item) => sum + item.numeric, 0),
)

const scale = computed(() => computeScale(actualMax.value, 5))
const chartMax = computed(() => (scale.value.max > 0 ? scale.value.max : 1))

const points = computed(() => {
  if (!seriesLength.value) return []
  const stepX =
    seriesLength.value > 1 ? chartWidth / (seriesLength.value - 1) : chartWidth / 2
  return rawData.value.map((item, index) => {
    const ratio = chartMax.value === 0 ? 0 : item.numeric / chartMax.value
    const x = leftPad + index * stepX
    const y = topPad + chartHeight * (1 - ratio)
    return {
      ...item,
      x,
      y,
    }
  })
})

const linePath = computed(() => {
  if (!points.value.length) return ''
  return points.value
    .map((p, index) => `${index === 0 ? 'M' : 'L'} ${p.x} ${p.y}`)
    .join(' ')
})

const areaPath = computed(() => {
  if (!points.value.length) return ''
  const startX = points.value[0].x
  const endX = points.value[points.value.length - 1].x
  const baseY = height - bottomPad
  const segments = points.value
    .map((p, index) => `${index === 0 ? 'M' : 'L'} ${p.x} ${p.y}`)
    .join(' ')
  return `${segments} L ${endX} ${baseY} L ${startX} ${baseY} Z`
})

const yGrid = computed(() => {
  const { step, max } = scale.value
  const lines: { y: number; label: string }[] = []
  if (!step || step <= 0) return lines
  for (let value = 0; value <= max; value += step) {
    const ratio = max === 0 ? 0 : value / max
    const y = topPad + chartHeight * (1 - ratio)
    const label = formatValue(value)
    if (!lines.length || lines[lines.length - 1].label !== label) {
      lines.push({ y, label })
    }
  }
  return lines
})

const xTicks = computed(() => {
  if (!points.value.length) return []
  const desired = Math.min(4, seriesLength.value)
  const indexes = new Set<number>([0, seriesLength.value - 1])
  if (seriesLength.value > 4) {
    const step = Math.max(2, Math.ceil((seriesLength.value - 1) / (desired - 1)))
    for (let i = step; i < seriesLength.value - 1; i += step) {
      indexes.add(i)
    }
  }
  const sorted = Array.from(indexes).sort((a, b) => a - b)
  const filtered: number[] = []
  for (const idx of sorted) {
    if (!filtered.length || idx - filtered[filtered.length - 1] >= 2) {
      filtered.push(idx)
    } else {
      filtered[filtered.length - 1] = idx
    }
  }
  return filtered.map((index) => {
    const point = points.value[index]
    return { x: point.x, label: point.label }
  })
})

const peakValueDisplay = computed(() => formatValue(actualMax.value))
const totalValueDisplay = computed(() => totalValue.value.toLocaleString())

const canvasEl = ref<HTMLElement | null>(null)
const activeIndex = ref(-1)
const pointerPosition = ref<{ left: number; top: number } | null>(null)

const currentIndex = computed(() => {
  if (!seriesLength.value) return -1
  return activeIndex.value >= 0 ? activeIndex.value : seriesLength.value - 1
})

const currentEntry = computed(() => {
  if (currentIndex.value < 0 || !points.value.length) {
    return {
      valueLabel: '0',
      dateLabel: '',
    }
  }
  const point = points.value[currentIndex.value]
  const valueLabel = formatValue(point.numeric)
  const dateLabel = point.label
  return {
    valueLabel,
    dateLabel,
  }
})

const tooltipStyle = computed(() => {
  if (currentIndex.value < 0 || !points.value.length) return {}
  const canvas = canvasEl.value
  const canvasWidth = canvas?.clientWidth ?? width
  const canvasHeight = canvas?.clientHeight ?? height
  const scaleX = canvasWidth / width
  const scaleY = canvasHeight / height
  const point = points.value[currentIndex.value]
  const fallbackLeft = point.x * scaleX
  const fallbackTop = point.y * scaleY
  const baseLeft = pointerPosition.value?.left ?? fallbackLeft
  const baseTop = pointerPosition.value?.top ?? fallbackTop
  const left = Math.min(canvasWidth - 60, Math.max(60, baseLeft))
  const top = Math.min(canvasHeight - 20, Math.max(24, baseTop - 48))
  return {
    left: `${left}px`,
    top: `${top}px`,
  }
})

const chartAriaLabel = computed(() => {
  if (!seriesLength.value) return t('usageAriaEmpty')
  const startLabel = points.value[0]?.label || '—'
  const endLabel = points.value[points.value.length - 1]?.label || '—'
  return t('usageAria', {
    start: startLabel,
    end: endLabel,
    value: currentEntry.valueLabel,
  })
})

function findNearestIndex(clientX: number, target: HTMLElement) {
  if (!seriesLength.value) return -1
  const rect = target.getBoundingClientRect()
  const padLeftPx = (leftPad / width) * rect.width
  const padRightPx = (rightPad / width) * rect.width
  const usableWidth = Math.max(1, rect.width - padLeftPx - padRightPx)
  const x = clientX - rect.left
  const relative = Math.min(1, Math.max(0, (x - padLeftPx) / usableWidth))
  const index = Math.round(relative * (seriesLength.value - 1))
  return Math.min(seriesLength.value - 1, Math.max(0, index))
}

function onPointerMove(event: MouseEvent) {
  const target = event.currentTarget as HTMLElement | null
  if (!target) return
  const index = findNearestIndex(event.clientX, target)
  activeIndex.value = index

  const rect = canvasEl.value?.getBoundingClientRect() ?? target.getBoundingClientRect()
  pointerPosition.value = {
    left: event.clientX - rect.left,
    top: event.clientY - rect.top,
  }
}

function resetActive() {
  activeIndex.value = -1
  pointerPosition.value = null
}
</script>

<style scoped>
.usage-card {
  display: grid;
  gap: 16px;
}

.usage-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.usage-summary {
  display: grid;
  gap: 6px;
}

.usage-title {
  margin: 0;
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--muted);
}

.usage-value {
  margin: 0;
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex-wrap: wrap;
}

.usage-count {
  font-size: 1.8rem;
  font-weight: 800;
  color: var(--txt);
}

.usage-day {
  font-size: 0.95rem;
  font-weight: 600;
  color: rgba(59, 130, 246, 0.9);
}

.usage-metrics {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.metric-pill {
  background: rgba(59, 130, 246, 0.12);
  color: #1d4ed8;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: 600;
}

.metric-pill strong {
  font-weight: 700;
}

.chart-wrap {
  position: relative;
  background: linear-gradient(180deg, rgba(59, 130, 246, 0.05), rgba(59, 130, 246, 0));
  border-radius: 18px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  padding: 18px 18px 24px;
}

.chart-canvas {
  position: relative;
  width: 100%;
  aspect-ratio: 640 / 260;
}

.chart-svg {
  width: 100%;
  height: auto;
  overflow: visible;
}

.grid-lines line {
  stroke: rgba(148, 163, 184, 0.25);
  stroke-dasharray: 4 6;
}

.grid-lines text {
  fill: rgba(71, 85, 105, 0.7);
  font-size: 0.5rem;
  font-weight: 600;
}

.area-path {
  stroke: none;
}

.line-path {
  fill: none;
  stroke-width: 2.6;
  stroke-linecap: round;
  stroke-linejoin: round;
  filter: drop-shadow(0 6px 14px rgba(59, 130, 246, 0.25));
}

.point-dots circle {
  fill: rgba(37, 99, 235, 0.92);
  stroke: none;
  filter: drop-shadow(0 1px 4px rgba(37, 99, 235, 0.25));
  transition: r 0.15s ease, stroke-width 0.15s ease;
}

.point-dots circle.active {
  r: 3;
}

.tooltip {
  position: absolute;
  min-width: 120px;
  padding: 8px 12px;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.22);
  border: 1px solid rgba(148, 163, 184, 0.25);
  pointer-events: none;
  transform: translate(-50%, -100%);
  text-align: center;
}

.tooltip::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: -8px;
  transform: translateX(-50%);
  border-width: 8px 7px 0 7px;
  border-style: solid;
  border-color: rgba(148, 163, 184, 0.25) transparent transparent transparent;
}

.tooltip-date {
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(59, 130, 246, 0.95);
  margin-bottom: 2px;
}

.tooltip-value {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--txt);
}

.x-axis .axis-base {
  stroke: rgba(148, 163, 184, 0.35);
  stroke-width: 1;
}

.x-axis .axis-tick {
  stroke: rgba(148, 163, 184, 0.5);
  stroke-width: 1;
}

.x-axis .axis-label {
  font-size: 0.54rem;
  fill: rgba(71, 85, 105, 0.75);
  font-weight: 600;
  dominant-baseline: hanging;
}

.empty {
  display: grid;
  place-items: center;
  min-height: 160px;
  border: 1px dashed rgba(148, 163, 184, 0.4);
  border-radius: 14px;
  color: rgba(71, 85, 105, 0.75);
  font-weight: 600;
  background: rgba(241, 245, 249, 0.4);
}

@media (max-width: 768px) {
  .usage-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .usage-count {
    font-size: 1.5rem;
  }

  .usage-metrics {
    width: 100%;
  }

  .metric-pill {
    flex: 1;
    text-align: center;
  }
}
</style>
