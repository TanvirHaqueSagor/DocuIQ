<template>
  <div v-if="bus.open" class="iw-overlay" @click.self="onClose">
    <div class="iw-modal">
      <header class="iw-head">
        <h3>{{ t('importWizard.title') }}</h3>
        <button class="x" @click="onClose" aria-label="Close">✕</button>
      </header>

      <nav class="iw-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="['tab', { active: activeTab === tab.key }]"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </nav>

      <section class="iw-body">
        <!-- Files -->
        <div v-if="activeTab === 'files'" class="pane">
          <h4>{{ t('importWizard.files.heading') }}</h4>
          <input type="file" multiple @change="onPickFiles" />
          <p class="hint">{{ t('importWizard.files.hint') }}</p>
          <ul class="picked" v-if="pickedFiles.length">
            <li v-for="f in pickedFiles" :key="f.name">{{ formatPickedFile(f) }}</li>
          </ul>
          <div class="row">
            <label>{{ t('importWizard.files.collectionLabel') }}</label>
            <input
              v-model="meta.collection"
              :placeholder="t('importWizard.files.collectionPlaceholder')"
            />
          </div>
          <div class="row">
            <label>{{ t('importWizard.files.tagsLabel') }} <span class="muted">({{ t('importWizard.optional') }})</span></label>
            <input
              v-model="meta.tags"
              :placeholder="t('importWizard.files.tagsPlaceholder')"
            />
          </div>
          <div class="row">
            <label>{{ t('importWizard.files.languageLabel') }} <span class="muted">({{ t('importWizard.optional') }})</span></label>
            <input
              v-model="meta.language"
              :placeholder="t('importWizard.files.languagePlaceholder')"
            />
          </div>
          <div class="actions">
            <button class="btn" :disabled="uploading || !pickedFiles.length" @click="startUpload">
              {{ uploading ? t('importWizard.status.uploading') : t('importWizard.buttons.startImport') }}
            </button>
          </div>
        </div>

        <!-- Web -->
        <div v-else-if="activeTab === 'web'" class="pane">
          <h4>{{ t('importWizard.web.heading') }}</h4>
          <div class="row">
            <label>{{ t('importWizard.web.labels.url') }}</label>
            <input v-model="web.url" :placeholder="t('importWizard.web.placeholders.url')" />
          </div>
          <div class="row checkbox">
            <label>
              <input type="checkbox" v-model="web.crawl" />
              {{ t('importWizard.web.labels.crawl') }}
            </label>
          </div>
          <div class="row" v-if="web.crawl">
            <label>{{ t('importWizard.web.labels.depth') }}</label>
            <input type="number" v-model.number="web.depth" min="1" max="3" />
          </div>
          <div class="actions">
            <button class="btn" :disabled="!validWeb" @click="createWebJob">
              {{ t('importWizard.buttons.startImport') }}
            </button>
          </div>
        </div>

        <!-- S3 -->
        <div v-else-if="activeTab === 's3'" class="pane">
          <h4>{{ t('importWizard.s3.heading') }}</h4>
          <div class="row">
            <label>{{ t('importWizard.s3.labels.name') }}</label>
            <input v-model="s3.name" :placeholder="t('importWizard.s3.placeholders.name')" />
          </div>
          <div class="row">
            <label>{{ t('importWizard.s3.labels.bucket') }}</label>
            <input v-model="s3.bucket" :placeholder="t('importWizard.s3.placeholders.bucket')" />
          </div>
          <div class="row">
            <label>{{ t('importWizard.s3.labels.prefix') }} <span class="muted">({{ t('importWizard.optional') }})</span></label>
            <input v-model="s3.prefix" :placeholder="t('importWizard.s3.placeholders.prefix')" />
          </div>
          <div class="row checkbox">
            <label>
              <input type="checkbox" v-model="s3.sync" />
              {{ t('importWizard.s3.labels.sync') }}
            </label>
          </div>
          <div class="actions">
            <button class="btn" :disabled="!validS3" @click="createS3Job">
              {{ t('importWizard.s3.button') }}
            </button>
          </div>
          <p class="hint">{{ t('importWizard.s3.hint') }}</p>
        </div>

        <!-- Generic connectors -->
        <div v-else class="pane">
          <h4>{{ t('importWizard.generic.heading', { tab: currentTabLabel }) }}</h4>
          <p class="hint">{{ t('importWizard.generic.message') }}</p>
          <div class="row">
            <label>{{ t('importWizard.generic.nameLabel') }}</label>
            <input v-model="generic.name" :placeholder="t('importWizard.generic.namePlaceholder', { tab: currentTabLabel })" />
          </div>
          <div class="actions">
            <button class="btn" :disabled="!generic.name" @click="createGenericSource">
              {{ t('importWizard.generic.button') }}
            </button>
          </div>
        </div>
      </section>

      <footer class="iw-foot">
        <div class="status" v-if="statusMsg">{{ statusMsg }}</div>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { API_BASE_URL } from '../config'
import { importWizardBus as bus, closeImportWizard } from '../stores/importWizardBus'

const { t } = useI18n()

const tabs = computed(() => [
  { key: 'files', label: t('importWizard.tabs.files') },
  { key: 'web', label: t('importWizard.tabs.web') },
  { key: 's3', label: t('importWizard.tabs.s3') },
  { key: 'gdrive', label: t('importWizard.tabs.gdrive') },
  { key: 'email', label: t('importWizard.tabs.email') },
  { key: 'slack', label: t('importWizard.tabs.slack') },
  { key: 'github', label: t('importWizard.tabs.github') },
  { key: 'db', label: t('importWizard.tabs.db') },
  { key: 'api', label: t('importWizard.tabs.api') },
  { key: 'media', label: t('importWizard.tabs.media') },
])

const activeTab = ref('files')
watch(() => bus.preset, (preset) => {
  if (preset?.tab) activeTab.value = preset.tab
})

const token = () => localStorage.getItem('token') || localStorage.getItem('access')
const authHeaders = () => ({ Authorization: `Bearer ${token()}` })

const pickedFiles = ref([])
const meta = reactive({ collection: '', tags: '', language: '' })
const uploading = ref(false)
const statusMsg = ref('')

const web = reactive({ url: '', crawl: false, depth: 1 })
const validWeb = computed(() => /^https?:\/\//i.test(web.url || ''))

const s3 = reactive({ name: '', bucket: '', prefix: '', sync: true })
const validS3 = computed(() => Boolean(s3.name && s3.bucket))

const generic = reactive({ name: '' })

const currentTabLabel = computed(() => {
  return tabs.value.find((tab) => tab.key === activeTab.value)?.label || t('importWizard.generic.fallbackTab')
})

const onPickFiles = (event) => {
  pickedFiles.value = Array.from(event.target.files || [])
}

const formatBytes = (size) => {
  if (!size && size !== 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let idx = 0
  let value = size
  while (value >= 1024 && idx < units.length - 1) {
    value /= 1024
    idx += 1
  }
  return `${value.toFixed(value >= 10 || idx === 0 ? 0 : 1)} ${units[idx]}`
}

const formatPickedFile = (file) => t('importWizard.files.fileItem', {
  name: file.name,
  size: formatBytes(file.size || 0),
})

const startUpload = async () => {
  if (!pickedFiles.value.length) return
  uploading.value = true
  statusMsg.value = ''
  try {
    const fd = new FormData()
    for (const file of pickedFiles.value) fd.append('files', file)
    const response = await fetch(`${API_BASE_URL}/api/ingest/upload/`, {
      method: 'POST',
      headers: authHeaders(),
      body: fd,
    })
    const files = await response.json()
    if (!response.ok) throw new Error(files?.detail || t('importWizard.errors.uploadFailed'))
    const fileIds = Array.isArray(files) ? files.map((x) => x.id) : []
    if (!fileIds.length) throw new Error(t('importWizard.errors.noFileIds'))

    const jobRes = await fetch(`${API_BASE_URL}/api/ingest/jobs/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({
        mode: 'upload',
        payload: {
          file_ids: fileIds,
          collection: meta.collection,
          tags: meta.tags,
          language: meta.language,
        },
      }),
    })
    const job = await jobRes.json()
    if (!jobRes.ok) throw new Error(job?.detail || t('importWizard.errors.jobCreateFailed'))

    statusMsg.value = t('importWizard.status.importStarted')
    setTimeout(onClose, 900)
  } catch (error) {
    statusMsg.value = t('importWizard.status.error', { error: error.message || error })
  } finally {
    uploading.value = false
  }
}

const createWebJob = async () => {
  statusMsg.value = ''
  try {
    const res = await fetch(`${API_BASE_URL}/api/ingest/jobs/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({
        mode: 'web',
        payload: { url: web.url, crawl: web.crawl, depth: web.depth },
      }),
    })
    const job = await res.json()
    if (!res.ok) throw new Error(job?.detail || t('importWizard.errors.jobCreateFailed'))
    statusMsg.value = t('importWizard.status.webQueued')
    setTimeout(onClose, 900)
  } catch (error) {
    statusMsg.value = t('importWizard.status.error', { error: error.message || error })
  }
}

const createS3Job = async () => {
  statusMsg.value = ''
  try {
    const sourceRes = await fetch(`${API_BASE_URL}/api/ingest/sources/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({
        kind: 's3',
        name: s3.name,
        config: { bucket: s3.bucket, prefix: s3.prefix, sync: s3.sync },
      }),
    })
    const source = await sourceRes.json()
    if (!sourceRes.ok) throw new Error(source?.detail || t('importWizard.errors.sourceCreateFailed'))

    const jobRes = await fetch(`${API_BASE_URL}/api/ingest/jobs/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({
        mode: 's3',
        source: source.id,
        payload: { bucket: s3.bucket, prefix: s3.prefix, sync: s3.sync },
      }),
    })
    const job = await jobRes.json()
    if (!jobRes.ok) throw new Error(job?.detail || t('importWizard.errors.jobCreateFailed'))
    statusMsg.value = t('importWizard.status.s3Queued')
    setTimeout(onClose, 900)
  } catch (error) {
    statusMsg.value = t('importWizard.status.error', { error: error.message || error })
  }
}

const createGenericSource = async () => {
  statusMsg.value = ''
  try {
    const response = await fetch(`${API_BASE_URL}/api/ingest/sources/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ kind: activeTab.value, name: generic.name, config: {} }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data?.detail || t('importWizard.errors.sourceCreateFailed'))
    statusMsg.value = t('importWizard.status.genericCreated')
    setTimeout(onClose, 900)
  } catch (error) {
    statusMsg.value = t('importWizard.status.error', { error: error.message || error })
  }
}

const onClose = () => {
  closeImportWizard()
}

onMounted(() => {
  if (bus.preset?.tab) activeTab.value = bus.preset.tab
})
</script>

<style scoped>
.iw-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: grid;
  place-items: center;
  z-index: 9999;
}

.iw-modal {
  width: min(860px, 96vw);
  background: var(--card);
  border-radius: 14px;
  border: 1px solid var(--line);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.25);
  overflow: hidden;
}

.iw-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  border-bottom: 1px solid var(--line);
}

.iw-head h3 {
  margin: 0;
  font-size: 1.1rem;
  color: var(--txt);
}

.iw-head .x {
  border: 1px solid var(--line);
  background: var(--card);
  border-radius: 8px;
  padding: 4px 8px;
  cursor: pointer;
}

.iw-tabs {
  display: flex;
  gap: 6px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--line);
  overflow-x: auto;
}

.tab {
  border: 1px solid var(--line);
  background: var(--card);
  padding: 6px 10px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  color: var(--txt);
}

.tab.active {
  background: rgba(96, 165, 250, 0.15);
  color: var(--blue);
  border-color: #c7dafb;
}

.iw-body {
  padding: 14px;
}

.pane {
  display: grid;
  gap: 10px;
}

.hint {
  color: #607d8b;
  font-size: 0.9rem;
}

.row {
  display: grid;
  gap: 6px;
}

.row.checkbox {
  align-items: center;
  grid-auto-flow: column;
  justify-content: start;
}

.row input[type='text'],
.row input[type='number'],
.row input[type='url'],
.row input:not([type]),
.row textarea,
.row select {
  border: 1px solid #d6e0f5;
  border-radius: 8px;
  padding: 9px 12px;
  background: #f7faff;
  font-size: 0.95rem;
}

.row textarea {
  resize: vertical;
}

.muted {
  color: #94a3b8;
  font-size: 0.85rem;
}

.actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 6px;
}

.btn {
  border: 1px solid var(--line);
  background: var(--card);
  color: var(--blue);
  font-weight: 700;
  border-radius: 8px;
  padding: 9px 12px;
  cursor: pointer;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.status {
  padding: 10px 14px;
  color: var(--txt);
}

.iw-foot {
  border-top: 1px solid var(--line);
}

.picked {
  list-style: disc;
  margin: 0 0 0 20px;
  padding: 0;
  color: #2f3b52;
}
</style>
