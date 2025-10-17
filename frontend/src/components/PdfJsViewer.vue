<template>
  <div class="pdfjs-wrap" ref="wrap">
    <div v-show="!error" class="pages" ref="pagesWrap"></div>
    <div class="error" v-if="error">
      <div class="err-box">
        <strong>Unable to load PDF</strong>
        <div class="err-sub">{{ error }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import * as pdfjsLib from 'pdfjs-dist/build/pdf'
import workerSrc from 'pdfjs-dist/build/pdf.worker.min.js?url'

const props = defineProps({
  src: { type: String, required: true },
  page: { type: Number, default: 1 },
  query: { type: String, default: '' },
  scale: { type: Number, default: 1.2 },
  highlightColor: { type: String, default: '#ff4d4f' },
  highlightOpacity: { type: Number, default: 0.25 },
})

const wrap = ref(null)
const pagesWrap = ref(null)
const error = ref('')

let destroyed = false
let renderToken = 0
let activeTask = null

try { pdfjsLib.GlobalWorkerOptions.workerSrc = workerSrc } catch (_) {}

async function destroyActiveTask() {
  if (activeTask && typeof activeTask.destroy === 'function') {
    try { await activeTask.destroy() } catch (_) {}
  }
  activeTask = null
}

function scrollToPageNumber(pageNumber, behavior = 'auto') {
  const num = Number(pageNumber)
  if (!wrap.value || !Number.isFinite(num) || num <= 0) return
  requestAnimationFrame(() => {
    const target = wrap.value?.querySelector(`.pdf-page[data-page="${num}"]`)
    if (target && wrap.value) {
      const top = target.offsetTop
      wrap.value.scrollTo({ top: Math.max(0, top - 12), behavior })
    }
  })
}

async function renderDocument() {
  const token = ++renderToken
  error.value = ''

  if (!props.src || !pagesWrap.value) {
    if (pagesWrap.value) pagesWrap.value.innerHTML = ''
    await destroyActiveTask()
    return
  }

  await destroyActiveTask()

  try {
    activeTask = pdfjsLib.getDocument({ url: props.src, withCredentials: false })
    const pdf = await activeTask.promise
    if (destroyed || token !== renderToken) return

    const container = pagesWrap.value
    container.innerHTML = ''

    const highlightTerm = (props.query || '').trim().toLowerCase()
    let highlightedPage = null

    for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
      if (destroyed || token !== renderToken) break

      const page = await pdf.getPage(pageNumber)
      if (destroyed || token !== renderToken) break

      const viewport = page.getViewport({ scale: props.scale })
      const pageEl = document.createElement('div')
      pageEl.className = 'pdf-page'
      pageEl.dataset.page = String(pageNumber)

      const canvas = document.createElement('canvas')
      canvas.className = 'pdf-canvas'
      canvas.width = viewport.width
      canvas.height = viewport.height
      canvas.style.width = '100%'
      canvas.style.height = 'auto'

      const overlay = document.createElement('div')
      overlay.className = 'overlay'

      pageEl.appendChild(canvas)
      pageEl.appendChild(overlay)
      container.appendChild(pageEl)

      const ctx = canvas.getContext('2d')
      await page.render({ canvasContext: ctx, viewport }).promise

      if (highlightTerm && !highlightedPage) {
        try {
          const q = highlightTerm
          const text = await page.getTextContent()
          const Util = pdfjsLib.Util
          const groups = {}
          for (const item of text.items || []) {
            const tx = Util && Util.transform ? Util.transform(viewport.transform, item.transform) : item.transform
            const y = tx[5]
            const key = Math.round(y)
            if (!groups[key]) groups[key] = { y, str: '' }
            groups[key].str += (item.str || '') + ' '
          }
          const lines = Object.values(groups).sort((a, b) => a.y - b.y)
          let hit = null
          for (const line of lines) {
            if ((line.str || '').toLowerCase().includes(q)) {
              hit = line
              break
            }
          }
          if (hit) {
            const lineH = Math.max(18, Math.round(16 * props.scale))
            const topUnits = (canvas.height - hit.y) - Math.round(lineH * 0.6)
            const clampedTop = Math.max(0, Math.min(canvas.height - lineH, topUnits))
            const highlight = document.createElement('div')
            highlight.className = 'hl'
            highlight.style.backgroundColor = props.highlightColor
            highlight.style.opacity = String(props.highlightOpacity)
            highlight.style.top = `${(clampedTop / canvas.height) * 100}%`
            highlight.style.height = `${(lineH / canvas.height) * 100}%`
            overlay.appendChild(highlight)
            highlightedPage = pageNumber
          }
        } catch (_) {
          // Ignore highlight issues; viewer should keep working
        }
      }
    }

    if (!destroyed && token === renderToken) {
      if (highlightedPage) {
        scrollToPageNumber(highlightedPage, 'smooth')
      } else if (props.page) {
        scrollToPageNumber(props.page, 'auto')
      } else if (wrap.value) {
        wrap.value.scrollTop = 0
      }
    }
  } catch (e) {
    if (!destroyed && token === renderToken) {
      error.value = (e && e.message) ? String(e.message) : 'Unable to load PDF'
    }
  }
}

onMounted(() => { renderDocument() })
onBeforeUnmount(() => {
  destroyed = true
  renderToken += 1
  destroyActiveTask()
})

watch(() => props.src, () => { renderDocument() })
watch(
  () => [props.query, props.scale, props.highlightColor, props.highlightOpacity],
  () => { renderDocument() }
)
watch(() => props.page, (val, oldVal) => {
  if (val && val !== oldVal) scrollToPageNumber(val, 'smooth')
})
</script>

<style scoped>
.pdfjs-wrap{
  position:relative;
  width:100%;
  height:auto;
  display:block;
  overflow:auto;
  background:#0b1022;
  border-radius:10px;
  padding:12px;
  box-sizing:border-box;
}
.pages{
  display:flex;
  flex-direction:column;
  gap:16px;
  width:100%;
}
.pdf-page{
  position:relative;
  width:100%;
}
.pdf-canvas{
  width:100%;
  height:auto;
  display:block;
  background:#111;
  border-radius:8px;
  box-shadow:0 12px 28px rgba(0,0,0,0.35);
}
.overlay{
  position:absolute;
  top:0;
  left:0;
  width:100%;
  height:100%;
  pointer-events:none;
  border-radius:8px;
}
.hl{
  position:absolute;
  left:0;
  width:100%;
  border-radius:4px;
}
.error{
  position:absolute;
  inset:0;
  display:flex;
  align-items:center;
  justify-content:center;
  background:#0b1022;
  color:#fff;
  border-radius:10px;
}
.err-box{
  background:rgba(220, 38, 38, 0.15);
  border:1px solid rgba(220, 38, 38, 0.45);
  color:#fecaca;
  padding:12px 14px;
  border-radius:8px;
  max-width:80%;
  text-align:center;
}
</style>
