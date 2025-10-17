<template>
  <div class="setup-wrap">
    <header class="head">
      <div class="title">
        <span class="ico">{{ schema.emoji }}</span>
        <div class="tt">
          <h1>{{ schema.title }}</h1>
          <p class="sub">{{ schema.description }}</p>
        </div>
      </div>
      <button class="ghost" @click="goBack">{{ t('sourceSetup.actions.back') }}</button>
    </header>

    <section class="card">
      <div v-if="isFileKind" class="pane">
        <div class="row">
          <label>{{ t('sourceSetup.files.labels.files') }}</label>
          <input type="file" multiple @change="onPickFiles" />
          <ul class="picked" v-if="pickedFiles.length">
            <li v-for="f in pickedFiles" :key="f.name">{{ formatPickedFile(f) }}</li>
          </ul>
        </div>
        <div class="row">
          <label>{{ t('sourceSetup.files.labels.title') }} <span class="muted">({{ t('sourceSetup.optional') }})</span></label>
          <input v-model="filesForm.title" :placeholder="t('sourceSetup.files.placeholders.title', { example: schema.title })" />
        </div>
        <div class="row">
          <label>{{ t('sourceSetup.files.labels.tags') }} <span class="muted">({{ t('sourceSetup.optional') }})</span></label>
          <input v-model="filesForm.tags" :placeholder="t('sourceSetup.files.placeholders.tags')" />
        </div>
        <div class="row">
          <label>{{ t('sourceSetup.files.labels.language') }} <span class="muted">({{ t('sourceSetup.optional') }})</span></label>
          <input v-model="filesForm.language" :placeholder="t('sourceSetup.files.placeholders.language')" />
        </div>
        <div class="actions">
          <button class="primary" :disabled="!pickedFiles.length || loading" @click="startFileImport">
            {{ loading ? t('sourceSetup.status.importing') : t('sourceSetup.buttons.startImport') }}
          </button>
        </div>
        <div class="status" v-if="statusMsg">{{ statusMsg }}</div>
      </div>

      <div v-else class="pane">
        <div class="row">
          <label>{{ t('sourceSetup.labels.connectionName') }}</label>
          <input v-model="name" :placeholder="t('sourceSetup.placeholders.connectionName', { source: schema.title })" />
        </div>

        <div v-for="field in schema.fields" :key="field.key" class="row">
          <label>
            {{ field.label }}
            <span v-if="!field.required" class="muted">({{ t('sourceSetup.optional') }})</span>
          </label>

          <template v-if="['text','url','password','number'].includes(field.type)">
            <input
              :type="field.type === 'password' ? 'password' : field.type === 'number' ? 'number' : 'text'"
              v-model="config[field.key]"
              :placeholder="field.placeholder || ''"
            />
          </template>

          <template v-else-if="field.type === 'textarea'">
            <textarea v-model="config[field.key]" :placeholder="field.placeholder || ''" rows="4"></textarea>
          </template>

          <template v-else-if="field.type === 'select'">
            <select v-model="config[field.key]">
              <option v-for="opt in field.options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
          </template>

          <template v-else-if="field.type === 'multi'">
            <input v-model="config[field.key]" :placeholder="field.placeholder || t('sourceSetup.hints.commaSeparated')" />
            <small class="hint">{{ t('sourceSetup.hints.commaSeparated') }}</small>
          </template>

          <template v-else-if="field.type === 'checkbox'">
            <label class="inline">
              <input type="checkbox" v-model="config[field.key]" />
              {{ field.help || '' }}
            </label>
          </template>

          <template v-else-if="field.type === 'date'">
            <input type="date" v-model="config[field.key]" />
          </template>

          <template v-else-if="field.type === 'json'">
            <textarea v-model="config[field.key]" :placeholder="field.placeholder || jsonExample" rows="5"></textarea>
            <small class="hint">{{ t('sourceSetup.hints.jsonValidation') }}</small>
          </template>

          <template v-else-if="field.type === 'oauth'">
            <div class="oauth-box">
              <button class="btn" @click="fakeOauth(field.provider)">
                {{ oauthConnected ? t('sourceSetup.oauth.reconnect', { provider: field.provider }) : t('sourceSetup.oauth.connect', { provider: field.provider }) }}
              </button>
              <span class="muted" v-if="oauthConnected">{{ t('sourceSetup.oauth.connected') }}</span>
            </div>
          </template>
        </div>

        <div class="actions">
          <button class="ghost" :disabled="loading" @click="saveSource(false)">{{ t('sourceSetup.buttons.saveSource') }}</button>
          <button class="primary" :disabled="loading || !name" @click="saveSource(true)">
            {{ loading ? t('sourceSetup.status.saving') : t('sourceSetup.buttons.saveAndRun') }}
          </button>
        </div>
        <div class="status" v-if="statusMsg">{{ statusMsg }}</div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { API_BASE_URL } from '../config'
import { authFetch } from '../lib/authFetch'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const translate = (key, fallback) => {
  const value = t(key)
  return value === key ? fallback : value
}

const jsonExample = '{\n  "param": "value"\n}'

const kind = computed(() => String(route.params.kind || 'files').toLowerCase())
const isFileKind = computed(() => kind.value === 'files' || ['video', 'audio', 'image'].includes(kind.value))

const pickedFiles = ref([])
const filesForm = reactive({ title: '', tags: '', language: '' })
const name = ref('')
const config = reactive({})
const loading = ref(false)
const statusMsg = ref('')
const oauthConnected = ref(false)

const onPickFiles = (event) => {
  pickedFiles.value = Array.from(event.target.files || [])
}

const formatPickedFile = (file) => {
  const size = Intl.NumberFormat(undefined, { maximumFractionDigits: 1 }).format(file.size || 0)
  return t('sourceSetup.files.fileItem', { name: file.name, size })
}

const ensureAuth = () => {
  const token = localStorage.getItem('token') || localStorage.getItem('access')
  if (!token || token.indexOf('.') === -1) {
    const redirect = encodeURIComponent(route.fullPath)
    router.replace(`/login?redirect=${redirect}`)
    throw new Error(t('sourceSetup.errors.authRequired'))
  }
  return token
}

const authHeaders = () => ({ Authorization: `Bearer ${ensureAuth()}` })

const goBack = () => router.back()

const fakeOauth = () => {
  oauthConnected.value = true
}

const startFileImport = async () => {
  ensureAuth()
  if (!pickedFiles.value.length) return
  loading.value = true
  statusMsg.value = ''
  try {
    const fd = new FormData()
    for (const file of pickedFiles.value) fd.append('files', file)
    const upload = await authFetch(`${API_BASE_URL}/api/ingest/upload/`, {
      method: 'POST',
      headers: { ...authHeaders() },
      body: fd,
    })
    const text = await upload.text()
    let list = []
    try { list = JSON.parse(text) } catch { throw new Error(text.slice(0, 180)) }
    if (!upload.ok) throw new Error(list?.detail || t('sourceSetup.errors.uploadFailed'))

    const fileIds = Array.isArray(list) ? list.map((item) => item.id) : []
    const filenames = Array.isArray(list) ? list.map((item) => item.name) : []
    if (!fileIds.length) throw new Error(t('sourceSetup.errors.noFileIds'))

    const payload = {
      file_ids: fileIds,
      filenames,
      title: filesForm.title,
      tags: filesForm.tags,
      language: filesForm.language,
    }

    const job = await authFetch(`${API_BASE_URL}/api/ingest/jobs/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ mode: 'upload', payload }),
    })
    const jobData = await job.json()
    if (!job.ok) throw new Error(jobData?.detail || t('sourceSetup.errors.jobCreateFailed'))

    statusMsg.value = t('sourceSetup.status.importQueued')
    setTimeout(() => router.replace('/documents'), 900)
  } catch (error) {
    statusMsg.value = t('sourceSetup.status.error', { error: error.message || error })
  } finally {
    loading.value = false
  }
}

const saveSource = async (runAfter) => {
  ensureAuth()
  loading.value = true
  statusMsg.value = ''
  try {
    const configOut = {}
    for (const [key, value] of Object.entries(config)) {
      if (typeof value === 'string' && value.trim().startsWith('{')) {
        try {
          configOut[key] = JSON.parse(value)
        } catch {
          configOut[key] = value
        }
      } else {
        configOut[key] = value
      }
    }

    const response = await authFetch(`${API_BASE_URL}/api/ingest/sources/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ kind: kind.value, name: name.value || schema.value.title, config: configOut }),
    })
    const source = await response.json()
    if (!response.ok) throw new Error(source?.detail || t('sourceSetup.errors.sourceCreateFailed'))

    if (runAfter) {
      const jobRes = await authFetch(`${API_BASE_URL}/api/ingest/jobs/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ mode: kind.value, source: source.id, payload: configOut }),
      })
      const jobData = await jobRes.json()
      if (!jobRes.ok) throw new Error(jobData?.detail || t('sourceSetup.errors.jobCreateFailed'))
    }

    statusMsg.value = runAfter ? t('sourceSetup.status.savedAndQueued') : t('sourceSetup.status.sourceSaved')
    setTimeout(() => router.replace('/documents'), 900)
  } catch (error) {
    statusMsg.value = t('sourceSetup.status.error', { error: error.message || error })
  } finally {
    loading.value = false
  }
}

const schemaFor = (key) => {
  const base = (titleKey, fallbackTitle, emoji, descKey, fallbackDesc, fields = []) => ({
    title: translate(titleKey, fallbackTitle),
    emoji,
    description: translate(descKey, fallbackDesc),
    fields,
  })

  switch (key) {
    case 'web':
      return base(
        'sourceSetup.schemas.web.title',
        'Website',
        '🌐',
        'sourceSetup.schemas.web.description',
        'Scrape or crawl a website',
        [
          { key: 'url', label: translate('sourceSetup.schemas.web.fields.url.label', 'URL'), type: 'url', required: true, placeholder: translate('sourceSetup.schemas.web.fields.url.placeholder', 'https://example.com') },
          { key: 'crawl', label: translate('sourceSetup.schemas.web.fields.crawl.label', 'Enable crawl'), type: 'checkbox', help: translate('sourceSetup.schemas.web.fields.crawl.help', 'Follow links') },
          { key: 'depth', label: translate('sourceSetup.schemas.web.fields.depth.label', 'Crawl depth'), type: 'number', placeholder: '1' },
          {
            key: 'frequency',
            label: translate('sourceSetup.schemas.web.fields.frequency.label', 'Frequency'),
            type: 'select',
            options: [
              { value: 'once', label: translate('sourceSetup.schemas.web.fields.frequency.options.once', 'One-time') },
              { value: 'daily', label: translate('sourceSetup.schemas.web.fields.frequency.options.daily', 'Daily') },
              { value: 'weekly', label: translate('sourceSetup.schemas.web.fields.frequency.options.weekly', 'Weekly') },
            ],
          },
        ],
      )
    case 's3':
      return base(
        'sourceSetup.schemas.s3.title',
        'AWS S3',
        '🟦',
        'sourceSetup.schemas.s3.description',
        'Connect an S3 bucket/prefix',
        [
          { key: 'bucket', label: translate('sourceSetup.schemas.s3.fields.bucket.label', 'Bucket'), type: 'text', required: true },
          { key: 'prefix', label: translate('sourceSetup.schemas.s3.fields.prefix.label', 'Prefix'), type: 'text', placeholder: translate('sourceSetup.schemas.s3.fields.prefix.placeholder', 'folder/path/') },
          { key: 'sync', label: translate('sourceSetup.schemas.s3.fields.sync.label', 'Keep in sync'), type: 'checkbox', help: translate('sourceSetup.schemas.s3.fields.sync.help', 'Auto-sync folder') },
        ],
      )
    default:
      return base(`sourceSetup.schemas.${key}.title`, key.toUpperCase(), '🔗', `sourceSetup.schemas.${key}.description`, 'Configure your source', [])
  }
}

const schema = computed(() => schemaFor(kind.value))

onMounted(() => {
  try {
    const qp = route.query || {}
    if (qp.name) name.value = String(qp.name)
  } catch (_) {}
})

watch(kind, () => {
  name.value = ''
  statusMsg.value = ''
  oauthConnected.value = false
  pickedFiles.value = []
  Object.keys(config).forEach((key) => { delete config[key] })
})
</script>

<style scoped>
.setup-wrap { display: grid; gap: 18px; padding: 16px 0 32px; }
.head { display:flex; justify-content:space-between; align-items:center; gap:12px; }
.title { display:flex; gap:12px; align-items:center; }
.ico { font-size:32px; }
.tt h1 { margin:0; font-size:24px; font-weight:800; color:var(--txt); }
.tt .sub { margin:4px 0 0; color:var(--muted); }
.ghost { border:1px solid var(--line); background:var(--card); border-radius:8px; padding:8px 12px; cursor:pointer; font-weight:600; }
.card { background:var(--card); border:1px solid var(--line); border-radius:14px; padding:18px; display:grid; gap:14px; box-shadow:var(--md-shadow-1); }
.pane { display:grid; gap:12px; }
.row { display:grid; gap:6px; }
.row.inline { grid-auto-flow: column; justify-content: start; align-items: center; }
.row input[type="text"], .row input[type="number"], .row input[type="url"], .row input:not([type]), .row textarea, .row select { border:1px solid #d5def1; border-radius:8px; padding:9px 12px; background:#f8faff; font-size:.95rem; }
.row textarea { resize:vertical; }
.muted { color:#94a3b8; font-size:.85rem; }
.actions { display:flex; gap:10px; justify-content:flex-end; margin-top:6px; }
.primary, .ghost { font-weight:700; }
.primary { background:#2563eb; color:#fff; border:1px solid #2563eb; border-radius:8px; padding:9px 12px; cursor:pointer; }
.primary:disabled { opacity:.6; cursor:not-allowed; }
.ghost:disabled { opacity:.6; cursor:not-allowed; }
.status { padding:10px 12px; font-weight:600; }
.hint { color:#607d8b; font-size:.85rem; }
.picked { list-style:disc; padding-left:20px; margin:0; color:#2f3b52; }
.oauth-box { display:flex; gap:10px; align-items:center; }
.btn { border:1px solid var(--line); background:var(--card); color:var(--blue); border-radius:8px; padding:8px 12px; cursor:pointer; font-weight:600; }
</style>
