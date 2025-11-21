<template>
  <div class="page">
    <!-- Page Header (no brand duplicate) -->
    <header class="page-head">
      <div class="left">
        <h1>{{ t('documents') }}</h1>
        <div class="search">
          <input
            v-model="q"
            type="text"
            :placeholder="t('documentsPage.searchPlaceholder')"
            @keydown.enter.prevent="applySearch"
            :aria-label="t('search')"
          />
          <button class="icon" @click="applySearch" :aria-label="t('search')">🔎</button>
        </div>
      </div>
      <div class="right">
        <button class="ghost" @click="refreshAll" :title="t('refresh')">⟳</button>
      </div>
    </header>

    <!-- Main content grid -->
    <div class="grid">
      <!-- Left: Imports / Documents -->
      <div class="left-col">
        <!-- Drag & Drop hero (click opens file picker) -->
        <section
          class="dropzone"
          :class="{ over: isOver }"
          @dragover.prevent="onDragOver"
          @dragleave.prevent="onDragLeave"
          @drop.prevent="onDrop"
          @click="goFiles"
        >
          <div class="dz-inner">
            <div class="cloud" aria-hidden="true">☁️</div>
            <div class="dz-title">{{ t('dropFiles') }}</div>
            <div class="dz-sub">{{ t('dropHint') }}</div>
          </div>
        </section>

        <section class="panel">
          <!-- Unified list: Imports + Documents -->
          <div class="table-wrap">
            <div class="table-tools">
              <label class="chk">
                <input type="checkbox" v-model="autoRefresh" />
                <span>{{ t('autoRefresh') }}</span>
              </label>
            </div>
            <div class="info-line">{{ t('docsInfo') }}</div>
            <table class="tbl" role="table">
              <thead>
                <tr>
                  <th>{{ t('type') }}</th>
                  <th>{{ t('title') }}</th>
                  <th>{{ t('status') }}</th>
                  <th>{{ t('imported') }}</th>
                  <th>{{ t('actions') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in filteredCombined" :key="row.id">
                  <td class="type-cell">
                    <span class="type-ico"><img class="src-ico-img" :src="rowIconComp(row)" :alt="rowType(row)" /></span>
                    <span>{{ rowType(row) }}</span>
                  </td>
                  <td class="truncate">
                    <template v-if="row.type==='doc'">
                      <RouterLink class="link" :to="`/documents/${row._raw?.id}`">{{ row.title }}</RouterLink>
                    </template>
                    <template v-else>{{ row.title }}</template>
                  </td>
                  <td>
                    <span class="badge" :class="badgeClass(row)">
                      <template v-if="isRowRunning(row)">
                        {{ t('documentsPage.statuses.running') }}<span class="dots" aria-hidden="true"><span>.</span><span>.</span><span>.</span></span>
                      </template>
                      <template v-else>{{ statusLabel(row) }}</template>
                    </span>
                  </td>
                  <td>{{ fmtDate(row.created_at) }}</td>
                  <td>
                    <template v-if="row.type==='doc'">
                      <div class="row-actions">
                        <RouterLink class="link icon-btn" :to="`/documents/${row._raw?.id}`" :title="t('view')" :aria-label="t('view')">
                          <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 5c-7 0-10 7-10 7s3 7 10 7 10-7 10-7-3-7-10-7Zm0 12a5 5 0 1 1 0-10 5 5 0 0 1 0 10Z"/></svg>
                        </RouterLink>
                        <button class="link icon-btn" @click="editRow(row)" :title="t('edit')" :aria-label="t('edit')">
                          <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25ZM20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83Z"/></svg>
                        </button>
                        <button class="link icon-btn" @click="rerunImport(row)" :disabled="isRowRunning(row) || isRowDeleting(row)" :title="t('rerunImport')" :aria-label="t('rerunImport')">
                          <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 5a7 7 0 1 1-6.9 8.2h2.1A5 5 0 1 0 12 7V3l5 4-5 4V9a3 3 0 1 1-3 3H5A7 7 0 0 1 12 5Z"/></svg>
                        </button>
                        <button class="link danger icon-btn" @click="deleteDoc(row)" :disabled="isRowRunning(row) || isRowDeleting(row)" :title="t('delete')" :aria-label="t('delete')">
                          <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M9 3h6l1 2h4v2H4V5h4l1-2Zm-3 6h12l-1 10a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L6 9Zm5 2v8h2v-8h-2Z"/></svg>
                        </button>
                      </div>
                    </template>
                    <template v-else>
                      <div class="row-actions">
                        <button class="link icon-btn" @click="editRow(row)" :title="t('edit')" :aria-label="t('edit')">
                          <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25ZM20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83Z"/></svg>
                        </button>
                        <button class="link icon-btn" @click="rerunImport(row)" :disabled="isRowRunning(row) || isRowDeleting(row)" :title="t('rerunImport')" :aria-label="t('rerunImport')">
                          <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 5a7 7 0 1 1-6.9 8.2h2.1A5 5 0 1 0 12 7V3l5 4-5 4V9a3 3 0 1 1-3 3H5A7 7 0 0 1 12 5Z"/></svg>
                        </button>
                        <button class="link danger icon-btn" @click="deleteJob(row)" :disabled="isRowRunning(row) || isRowDeleting(row)" :title="t('delete')" :aria-label="t('delete')">
                          <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M9 3h6l1 2h4v2H4V5h4l1-2Zm-3 6h12l-1 10a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L6 9Zm5 2v8h2v-8h-2Z"/></svg>
                        </button>
                      </div>
                    </template>
                  </td>
                </tr>
                <tr v-if="!filteredCombined.length">
                  <td colspan="5" class="empty">{{ t('noItems') }}</td>
                </tr>
              </tbody>
            </table>
            <div class="table-footer" v-if="canLoadMore">
              <button class="load-more" type="button" @click="loadMoreDocs" :disabled="docsLoading">
                <span>{{ docsLoading ? translateOr('loading', {}, 'Loading…') : translateOr('loadMore', {}, 'Load more') }}</span>
                <span class="load-remaining" v-if="remainingDocs > 0">({{ remainingDocs }} {{ t('documents') }})</span>
              </button>
            </div>
          </div>
        </section>
      </div>

      <!-- Right: KPIs + source shortcuts -->
      <aside class="side">
        <div class="kpis">
          <div class="kpi">
            <div class="kpi-title">{{ t('documents') }}</div>
            <div class="kpi-val">{{ kpi.documents }}</div>
          </div>
          <div class="kpi">
            <div class="kpi-title">{{ t('runningJobs') }}</div>
            <div class="kpi-val">{{ kpi.running }}</div>
          </div>
          <div class="kpi">
            <div class="kpi-title">{{ t('server') }}</div>
            <div class="kpi-val" :class="kpi.health ? 'ok' : 'bad'">{{ kpi.health ? t('ok') : t('down') }}</div>
          </div>
        </div>

        <div class="sources">
          <div class="sources-head">
            <h3>{{ t('sources') }}</h3>
          </div>

          <div class="src-grid">
            <button v-for="s in srcPalette" :key="s.key" class="src-btn" @click="openWizard(s.key)">
              <span class="src-ico-comp"><img class="src-ico-img" :src="iconForKind(s.key)" :alt="s.name" /></span>
              <div class="src-name">{{ s.name }}</div>
            </button>
          </div>
        </div>
      </aside>
    </div>

    <section class="connected-table card" v-if="filteredSources.length">
      <header class="connected-head">
        <h3>{{ t('connected') }}</h3>
      </header>
      <div class="table-wrap">
        <table class="conn-table">
          <thead>
            <tr>
              <th>{{ t('name') || 'Name' }}</th>
              <th>{{ t('type') }}</th>
              <th>{{ t('created') || 'Added' }}</th>
              <th>{{ t('actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in filteredSources" :key="s.id">
              <td>
                <div class="conn-name">
                  <span class="src-ico-comp"><img class="src-ico-img" :src="iconForKind(s.kind)" :alt="prettyKind(s.kind)" /></span>
                  <div>
                    <div class="nm">{{ s.name }}</div>
                    <div class="kind">· {{ prettyKind(s.kind) }}</div>
                  </div>
                </div>
              </td>
              <td>{{ prettyKind(s.kind) }}</td>
              <td>{{ fmtDate(s.updated_at || s.created_at) }}</td>
              <td class="conn-actions">
                <button class="link icon-btn" @click="runSource(s)" :title="t('run')" :aria-label="t('run')">
                  <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M8 5v14l11-7L8 5Z"/></svg>
                </button>
                <button class="link danger icon-btn" @click="deleteSource(s)" :disabled="isSourceDeleting(s)" :title="t('delete')" :aria-label="t('delete')">
                  <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M9 3h6l1 2h4v2H4V5h4l1-2Zm-3 6h12l-1 10a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L6 9Zm5 2v8h2v-8h-2Z"/></svg>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>

</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import { API_BASE_URL as API } from '../config'
// Icon components (via unplugin-icons)
import { authFetch } from '../lib/authFetch'

import icFile from '../assets/icons/file.svg'
import icWeb from '../assets/icons/web.svg'
import icS3 from '../assets/icons/S3.svg'
import icGdrive from '../assets/icons/gdrive.svg'
import icGmail from '../assets/icons/gmail.svg'
import icDropbox from '../assets/icons/dropbox.svg'
import icOnedrive from '../assets/icons/onedrive.svg'
import icBox from '../assets/icons/box.svg'
// Enterprise / productivity
import icSharepoint from '../assets/icons/sharePoint.svg'
import icConfluence from '../assets/icons/confluence.svg'
import icNotion from '../assets/icons/Notion.svg'
import icAirtable from '../assets/icons/airtable.svg'
// Comms
import icOutlook from '../assets/icons/outlook.svg'
import icSlack from '../assets/icons/slack.svg'
import icTeams from '../assets/icons/teams.svg'
import icZoom from '../assets/icons/zoom.svg'
// Dev/Project
import icGithub from '../assets/icons/github.svg'
import icGitlab from '../assets/icons/gitlab.svg'
import icJira from '../assets/icons/jira.svg'
import icTrello from '../assets/icons/trello.svg'
// Databases/BI/Search
import icPostgres from '../assets/icons/postgresql.svg'
import icMysql from '../assets/icons/mysql.svg'
import icMongodb from '../assets/icons/mongodb.svg'
import icSnowflake from '../assets/icons/snowflake.svg'
import icBigQuery from '../assets/icons/bigquery.svg'
import icElasticsearch from '../assets/icons/elasticsearch.svg'
// Feeds/APIs
import icRss from '../assets/icons/rss.svg'
import icApi from '../assets/icons/api.svg'
import icBloomberg from '../assets/icons/blloomberg.svg'
import icRefinitiv from '../assets/icons/Refintiv.svg'
import icEsg from '../assets/icons/esg.svg'
// Social/Calendar/Design
import icLinkedIn from '../assets/icons/linkedin.svg'
import icTwitterX from '../assets/icons/x.svg'
import icGCal from '../assets/icons/google-calendar.svg'
import icFigma from '../assets/icons/figma.svg'
/* ----- state ----- */
const q = ref('')
const isOver = ref(false); let overTimer=null
const autoRefresh = ref(true)
const jobs = ref([]); const docs = ref([]); const sources = ref([])
const kpi = reactive({ documents: 0, running: 0, health: true })
const DOC_PAGE_SIZE = 20
const docsLimit = ref(DOC_PAGE_SIZE)
const docsTotal = ref(0)
const docsLoading = ref(false)
const fileInput = ref(null)
// Track rows set to re-run; key by row.id
const rerunning = ref({})
// Track rows being deleted; key by row.id
const deletingRows = ref({})
// Track sources being deleted; key by source.id
const deletingSources = ref({})

/* ----- wizard ----- */
const wizard = reactive({ open:false, tab:'' })
const openWizard = (t='gdrive') => { router.push(`/connect/${t}`) }

onMounted(async () => {
  try {
    ensureAuthOrRedirect()   // টোকেন না থাকলে এখানে থেমে /login এ যাবে
    // Seed search from query param (?q=...)
    try { q.value = String(route.query.q || '').trim() } catch (_) { /* ignore */ }
    await refreshAll()
    // Auto-refresh both jobs and documents so statuses update in UI
    poll = setInterval(() => { if (autoRefresh.value) refreshAll() }, 5000)
  } catch (e) {
    // redirected; কিছুই করার নেই
  }
})

/* ----- helpers ----- */
import { useRouter, useRoute } from 'vue-router'
const router = useRouter()
const route  = useRoute()
const { t } = useI18n ? useI18n() : { t: (s)=>s }
const goFiles = () => router.push('/connect/files')

const getAccessToken = () =>
  localStorage.getItem('token') || localStorage.getItem('access') || ''

// শুধুমাত্র টোকেন থাকলে হেডার দিন; না থাকলে খালি অবজেক্ট
const authHeaders = () => {
  const t = getAccessToken()
  // JWT হলে সাধারণত 2টা ডট থাকে (x.y.z) — ধরা সহজ
  return t && t.includes('.') ? { Authorization: `Bearer ${t}` } : {}
}

// টোকেন না থাকলে সাথে সাথে লগইনে পাঠান
const ensureAuthOrRedirect = () => {
  const t = getAccessToken()
  if (!t) {
    router.replace(`/login?redirect=${encodeURIComponent(route.fullPath)}`)
    throw new Error('Auth required')
  }
}
const fmtDate = (iso) => {
  try {
    return new Date(iso).toLocaleDateString()
  } catch {
    return iso ? String(iso).split('T')[0] : ''
  }
}
const translateOr = (key, params, fallback) => {
  const value = t(key, params)
  return value === key ? fallback : value
}
const capitalize = (str = '') => (str ? str.charAt(0).toUpperCase() + str.slice(1) : '')
const firstNonBlank = (...values) => {
  for (const value of values) {
    if (Array.isArray(value)) {
      for (const item of value) {
        const str = (item ?? '').toString().trim()
        if (str) return str
      }
    } else if (value !== undefined && value !== null) {
      const str = value.toString().trim()
      if (str) return str
    }
  }
  return ''
}
const KIND_ALIASES = {
  upload: 'file',
  files: 'file',
  file: 'file',
  job: 'import',
  import: 'import',
  postgres: 'postgres',
  postgresql: 'postgres',
  db: 'database'
}
const KIND_FALLBACKS = {
  import: 'Import',
  file: 'File',
  web: 'Web',
  s3: 'S3',
  gdrive: 'Google Drive',
  dropbox: 'Dropbox',
  onedrive: 'OneDrive',
  box: 'Box',
  sharepoint: 'SharePoint',
  confluence: 'Confluence',
  notion: 'Notion',
  airtable: 'Airtable',
  email: 'Email',
  gmail: 'Gmail',
  outlook: 'Outlook',
  slack: 'Slack',
  teams: 'Microsoft Teams',
  zoom: 'Zoom',
  github: 'GitHub',
  gitlab: 'GitLab',
  jira: 'Jira',
  trello: 'Trello',
  postgres: 'PostgreSQL',
  mysql: 'MySQL',
  mongodb: 'MongoDB',
  snowflake: 'Snowflake',
  bigquery: 'BigQuery',
  elasticsearch: 'Elasticsearch',
  database: 'Database',
  rss: 'RSS',
  api: 'API',
  bloomberg: 'Bloomberg',
  refinitiv: 'Refinitiv',
  esg: 'ESG API',
  linkedin: 'LinkedIn',
  twitter: 'Twitter (X)',
  gcal: 'Google Calendar',
  figma: 'Figma',
  media: 'Media',
  video: 'Video',
  audio: 'Audio'
}
const canonicalKind = (value) => {
  const key = String(value || '').toLowerCase()
  return KIND_ALIASES[key] || key
}
const prettyKind = (value) => {
  const raw = String(value || '').toLowerCase()
  const canonical = canonicalKind(raw)
  const translationKey = `documentsPage.kinds.${canonical}`
  const localized = t(translationKey)
  if (localized !== translationKey) return localized
  if (raw !== canonical) {
    const aliasKey = `documentsPage.kinds.${raw}`
    const aliasLocalized = t(aliasKey)
    if (aliasLocalized !== aliasKey) return aliasLocalized
  }
  return KIND_FALLBACKS[canonical] || KIND_FALLBACKS[raw] || capitalize(canonical || raw)
}
const jobTitle = (j) => {
  const rawMode = String(j.mode || '').toLowerCase()
  const canonical = canonicalKind(rawMode)
  const modeLabel = prettyKind(canonical)
  if (canonical === 'file') {
    const names = j.payload?.filenames || j.payload?.files
    if (Array.isArray(names) && names.length) {
      if (names.length === 1) return names[0]
      return translateOr('documentsPage.jobTitle.uploadMultiple', { first: names[0], extra: names.length - 1 }, `${names[0]} (+${names.length - 1} more)`)
    }
    const count = j.payload?.file_ids?.length || 0
    return translateOr('documentsPage.jobTitle.uploadCount', { mode: modeLabel, count }, `${modeLabel} · ${count} file(s)`)
  }
  if (canonical === 'web') {
    const url = firstNonBlank(
      j.payload?.url,
      j.payload?.start_url,
      j.payload?.source_url,
      j.payload?.target_url,
      j.payload?.domain,
      j.payload?.site,
      (Array.isArray(j.payload?.urls) && j.payload.urls),
      j.payload?.connection_url
    )
    if (url) {
      return translateOr('documentsPage.jobTitle.web', { mode: modeLabel, url }, `${modeLabel} · ${url}`)
    }
    const label = firstNonBlank(j.payload?.name, j.payload?.title, j.source?.name, j.source?.label)
    if (label) {
      return translateOr('documentsPage.jobTitle.webFallback', { mode: modeLabel, name: label }, `${modeLabel} · ${label}`)
    }
    return translateOr('documentsPage.jobTitle.generic', { mode: modeLabel }, modeLabel)
  }
  if (canonical === 's3') {
    const bucket = j.payload?.bucket || ''
    const prefix = j.payload?.prefix || ''
    return translateOr('documentsPage.jobTitle.s3', { mode: modeLabel, bucket, prefix }, `${modeLabel} · ${bucket}/${prefix}`)
  }
  if (modeLabel) {
    return translateOr('documentsPage.jobTitle.generic', { mode: modeLabel }, modeLabel)
  }
  return rawMode.toUpperCase()
}
// Deduplication key for jobs so re-run doesn't show duplicates
const stableStr = (obj) => {
  if (obj === null || obj === undefined) return ''
  if (typeof obj !== 'object') return String(obj)
  const keys = Object.keys(obj).sort()
  return keys.map(k => `${k}:${stableStr(obj[k])}`).join('|')
}
const jobKey = (j) => {
  const mode = String(j.mode||'').toLowerCase()
  if (mode === 'web') return `web|${j.payload?.url||''}`
  if (mode === 's3') return `s3|${j.payload?.bucket||''}|${j.payload?.prefix||''}`
  if (j.source) return `${mode}|src:${j.source}`
  return `${mode}|${stableStr(j.payload||{})}`
}
// Human-friendly type for unified list
const isWebDoc = (row) => {
  try { return !!(row?._raw?.steps_json && row._raw.steps_json.source_url) } catch { return false }
}
const rowType = (row) => {
  if (row?.type === 'job') {
    const rawMode = String(row?._raw?.mode || '').toLowerCase()
    const canonical = rawMode ? canonicalKind(rawMode) : 'import'
    return prettyKind(canonical)
  }
  // Documents: detect web-fetched items via steps_json.source_url
  if (isWebDoc(row)) return prettyKind('web')
  // Default to File; we can refine by extension later
  return prettyKind('file')
}

// Map job statuses to friendly labels
const mapDocStatus = (s) => {
  const v = String(s || '').toUpperCase()
  if (['READY','PARTIAL_READY'].includes(v)) return 'imported'
  if (['FAILED','CANCELLED','DELETED'].includes(v)) return 'failed'
  if (['QUEUED','FETCHING','NORMALIZING','CHUNKING','EMBEDDING','INDEXING'].includes(v)) return 'processing'
  return 'uploaded'
}
const mapUnifiedStatus = (row) => {
  // Desired: Uploaded, Processing, Imported
  if (row?.type === 'job') {
    const v = String(row._raw?.status || '').toLowerCase()
    if (v === 'queued' || v === 'running') return 'processing'
    if (v === 'success') return 'imported'
    if (v === 'failed') return 'failed'
    return 'uploaded'
  }
  // Documents: use backend-provided status if present
  return mapDocStatus(row?._raw?.status)
}
const statusClass = (row) => mapUnifiedStatus(row) || ''
const statusLabel = (row) => {
  const key = mapUnifiedStatus(row)
  if (!key) return ''
  return translateOr(`documentsPage.statuses.${key}`, {}, capitalize(key))
}
const isRowRunning = (row) => !!(rerunning.value || {})[row?.id]
const badgeClass = (row) => isRowRunning(row) ? 'processing' : statusClass(row)
const isRowDeleting = (row) => !!(deletingRows.value || {})[row?.id]
const isSourceDeleting = (s) => !!(deletingSources.value || {})[s?.id]
// Icon URLs for known kinds (fallback to file)
const ICONS = {
  // Storage / generic
  file: icFile, files: icFile, upload: icFile,
  web: icWeb,
  s3: icS3,
  gdrive: icGdrive,
  dropbox: icDropbox,
  onedrive: icOnedrive,
  box: icBox,

  // Enterprise
  sharepoint: icSharepoint,
  confluence: icConfluence,
  notion: icNotion,
  airtable: icAirtable,

  // Comms
  email: icGmail, // generic email → gmail icon
  gmail: icGmail,
  outlook: icOutlook,
  slack: icSlack,
  teams: icTeams,
  zoom: icZoom,

  // Dev/Project
  github: icGithub,
  gitlab: icGitlab,
  jira: icJira,
  trello: icTrello,

  // Databases/BI/Search
  postgres: icPostgres,
  postgresql: icPostgres,
  mysql: icMysql,
  mongodb: icMongodb,
  snowflake: icSnowflake,
  bigquery: icBigQuery,
  elasticsearch: icElasticsearch,
  db: icPostgres,
  database: icPostgres,

  // Feeds/APIs
  rss: icRss,
  api: icApi,
  bloomberg: icBloomberg,
  refinitiv: icRefinitiv,
  esg: icEsg,

  // Social/Calendar/Design
  linkedin: icLinkedIn,
  twitter: icTwitterX,
  gcal: icGCal,
  figma: icFigma,
}
const iconForKind = (k) => {
  const key = canonicalKind(k)
  const raw = String(k || '').toLowerCase()
  return ICONS[key] || ICONS[raw] || icFile
}

// Icon for each row (connector kind or generic file)
const rowIconComp = (row) => {
  if (row?.type === 'job') {
    const k = String(row?._raw?.mode || '').toLowerCase()
    return iconForKind(k)
  }
  return isWebDoc(row) ? iconForKind('web') : iconForKind('file')
}

/* ----- filters ----- */
// Unified list: show documents + non-upload jobs (e.g., Web, S3, etc.)
const combinedRows = computed(() => {
  // Deduplicate non-upload jobs by a stable key; keep the most recent
  // Show web jobs only when they are NOT successful (to surface errors/progress).
  // Hide successful web jobs because the resulting document row is shown separately.
  const nonUpload = (jobs.value || []).filter(j => {
    const m = String(j.mode || '').toLowerCase()
    if (m === 'upload') return false
    if (m === 'web') return String(j.status || '').toLowerCase() !== 'success'
    return true
  })
  const latestByKey = new Map()
  for (const j of nonUpload) {
    const k = jobKey(j)
    const prev = latestByKey.get(k)
    if (!prev) { latestByKey.set(k, j); continue }
    const da = prev.created_at ? new Date(prev.created_at).getTime() : 0
    const db = j.created_at ? new Date(j.created_at).getTime() : 0
    if (db >= da) latestByKey.set(k, j)
  }
  const jobRows = Array.from(latestByKey.values()).map(j => ({
    id: `job-${j.id}`,
    type: 'job',
    title: jobTitle(j),
    status: j.status,
    progress: j.progress || 0,
    created_at: j.created_at,
    _raw: j,
  }))

  const docRows = (docs.value || []).map(d => ({
    id: `doc-${d.id}`,
    type: 'doc',
    title: d.title || d.filename,
    status: d.status || 'QUEUED',
    progress: null,
    created_at: d.status_updated_at || d.created_at,
    _raw: d,
  }))

  const out = [...jobRows, ...docRows]
  out.sort((a,b) => {
    const da = a.created_at ? new Date(a.created_at).getTime() : 0
    const db = b.created_at ? new Date(b.created_at).getTime() : 0
    return db - da
  })
  return out
})
const filteredCombined = computed(() => {
  if (!q.value) return combinedRows.value
  const s = q.value.toLowerCase()
  return combinedRows.value.filter(r =>
    (r.title||'').toLowerCase().includes(s) ||
    (r.status||'').toLowerCase().includes(s) ||
    r.type.includes(s) ||
    statusLabel(r).toLowerCase().includes(s)
  )
})
const uniqueSources = computed(()=>{
  const seen = new Set(); const out = []
  for (const s of (sources.value||[])) {
    const k = `${(s.name||'').toLowerCase()}|${(s.kind||'').toLowerCase()}`
    if (seen.has(k)) continue; seen.add(k); out.push(s)
  }
  return out
})
const filteredSources = computed(()=>{
  if(!q.value) return uniqueSources.value
  const s=q.value.toLowerCase()
  return uniqueSources.value.filter(x => (x.name||'').toLowerCase().includes(s) || (x.kind||'').toLowerCase().includes(s))
})
const remainingDocs = computed(() => Math.max(0, (docsTotal.value || 0) - (docs.value?.length || 0)))
const canLoadMore = computed(() => remainingDocs.value > 0)

const loadMoreDocs = async () => {
  if (!canLoadMore.value) return
  const nextLimit = docsLimit.value + DOC_PAGE_SIZE
  docsLimit.value = docsTotal.value ? Math.min(nextLimit, docsTotal.value) : nextLimit
  await fetchDocs()
}
const applySearch = ()=>{
  const term = (q.value || '').trim()
  const current = String(route.query?.q || '')
  if (term === current) return
  const nextQuery = { ...(route.query || {}) }
  if (term) nextQuery.q = term
  else delete nextQuery.q
  router.replace({ query: nextQuery }).catch(()=>{})
}

/* ----- API ----- */
const fetchJobs = async ()=>{
  const r = await authFetch(`${API}/api/ingest/jobs/`, { headers: { ...authHeaders() } })
  if(r.ok) jobs.value = await r.json()
  kpi.running = jobs.value.filter(j=>['queued','running'].includes(String(j.status||'').toLowerCase())).length
}
const fetchDocs = async ()=>{
  docsLoading.value = true
  try{
    const url = `${API}/api/documents?limit=${docsLimit.value}&sort=-created_at`
    const r = await authFetch(url, { headers: authHeaders() })
    if(r.ok){
      const payload = await r.json()
      const list = Array.isArray(payload?.results) ? payload.results : Array.isArray(payload) ? payload : []
      docs.value = list
      docsTotal.value = typeof payload?.count === 'number' ? payload.count : list.length
      kpi.documents = docsTotal.value || list.length
    }
  }finally{
    docsLoading.value = false
  }
}
const fetchSources = async ()=>{
  const r = await authFetch(`${API}/api/ingest/sources/`, { headers: authHeaders() })
  if(r.ok) sources.value = await r.json()
}
const checkHealth = async ()=>{
  try{ const r=await fetch(`${API}/health/`); kpi.health=r.ok }catch{ kpi.health=false }
}
const refreshAll = async ()=>{ await Promise.all([fetchJobs(), fetchDocs(), fetchSources(), checkHealth()]) }

// Re-run import: for docs -> create upload job with file_ids; for jobs -> clone job
const rerunImport = async (row)=>{
  try{
    // mark as running (animated)
    const setFlag = (v)=>{ rerunning.value = { ...(rerunning.value||{}), [row.id]: v } }
    setFlag(true)
    if (row?.type === 'doc'){
      const d = row._raw
      const payload = { file_ids: [d.id] }
      const r = await authFetch(`${API}/api/ingest/jobs/`, { method:'POST', headers:{ 'Content-Type':'application/json', ...authHeaders() }, body: JSON.stringify({ mode:'upload', payload }) })
      if (r.ok) await fetchJobs()
      return
    }
    if (row?.type === 'job'){
      const j = row._raw
      const body = { mode: j.mode, payload: j.payload || {}, source: j.source || undefined }
      const r = await authFetch(`${API}/api/ingest/jobs/`, { method:'POST', headers:{ 'Content-Type':'application/json', ...authHeaders() }, body: JSON.stringify(body) })
      if (r.ok) await fetchJobs()
    }
  }catch(_){ /* ignore */ }
  finally{
    // clear the flag after a short delay to avoid being stuck
    setTimeout(() => {
      const m = { ...(rerunning.value||{}) }; delete m[row.id]; rerunning.value = m
    }, 6000)
  }
}

/* ----- DnD / File pick ----- */
const onDragOver = (e)=>{ e.dataTransfer.dropEffect='copy'; isOver.value=true }
const onDragLeave = ()=>{ clearTimeout(overTimer); overTimer=setTimeout(()=>isOver.value=false,60) }
const onDrop = async (e)=>{ isOver.value=false; const files=[...(e.dataTransfer?.files||[])]; if(files.length){ router.push('/connect/files') } }

/* ----- Wizard logic removed in favor of /connect/:kind pages ----- */

/* ----- palette ----- */
const SOURCE_PALETTE = [
  { key:'files', emoji:'📁' },
  { key:'web', emoji:'🌐' },
  { key:'gdrive', emoji:'🟩' },
  { key:'dropbox', emoji:'🟦' },
  { key:'onedrive', emoji:'🟦' },
  { key:'box', emoji:'📦' },
  { key:'s3', emoji:'🟦' },
  { key:'sharepoint', emoji:'🏢' },
  { key:'confluence', emoji:'📘' },
  { key:'notion', emoji:'⬛' },
  { key:'airtable', emoji:'📋' },
  { key:'gmail', emoji:'✉️' },
  { key:'outlook', emoji:'✉️' },
  { key:'slack', emoji:'🟩' },
  { key:'teams', emoji:'🟦' },
  { key:'zoom', emoji:'🎥' },
  { key:'github', emoji:'💻' },
  { key:'gitlab', emoji:'💻' },
  { key:'jira', emoji:'🟦' },
  { key:'trello', emoji:'🗂️' },
  { key:'postgres', emoji:'🗄️' },
  { key:'mysql', emoji:'🗄️' },
  { key:'mongodb', emoji:'🍃' },
  { key:'snowflake', emoji:'❄️' },
  { key:'bigquery', emoji:'🟨' },
  { key:'elasticsearch', emoji:'🔍' },
  { key:'rss', emoji:'📰' },
  { key:'api', emoji:'🔗' },
  { key:'bloomberg', emoji:'📈' },
  { key:'refinitiv', emoji:'📈' },
  { key:'esg', emoji:'🌱' },
  { key:'linkedin', emoji:'🔮' },
  { key:'twitter', emoji:'🔮' },
  { key:'gcal', emoji:'📆' },
  { key:'figma', emoji:'🎨' },
]
const srcPalette = computed(() => SOURCE_PALETTE.map(item => ({
  ...item,
  name: prettyKind(item.key),
})))

/* ----- lifecycle ----- */
let poll=null
onBeforeUnmount(()=> clearInterval(poll))

// Run a saved source now
const runSource = async (s)=>{
  try{
    const r = await authFetch(`${API}/api/ingest/jobs/`,{
      method:'POST', headers:{ 'Content-Type':'application/json', ...authHeaders() },
      body: JSON.stringify({ mode: s.kind || 'source', source: s.id, payload: {} })
    })
    if(r.ok){ await fetchJobs(); }
  }catch(_){ /* ignore */ }
}

// Delete a document
const deleteDoc = async (rowOrDoc)=>{
  const d = rowOrDoc?._raw || rowOrDoc
  if (!d || !d.id) return
  const msg = (typeof t === 'function') ? t('confirmDeleteDoc', { name: d.title || d.filename || d.id }) : `Delete "${d.title || d.filename || d.id}"? This cannot be undone.`
  if (!confirm(msg)) return
  try{
    const row = rowOrDoc?._raw ? rowOrDoc : { id: `doc-${d.id}` }
    deletingRows.value = { ...(deletingRows.value||{}), [row.id]: true }
    const r = await authFetch(`${API}/api/documents/${d.id}`, { method:'DELETE', headers: { ...authHeaders() } })
    if (r.ok) { await fetchDocs() }
  }catch(_){ /* noop */ }
  finally{
    const row = rowOrDoc?._raw ? rowOrDoc : { id: `doc-${d.id}` }
    const m = { ...(deletingRows.value||{}) }; delete m[row.id]; deletingRows.value = m
  }
}

// Delete a source
const deleteSource = async (s)=>{
  if (!s || !s.id) return
  const smsg = (typeof t === 'function') ? t('confirmDeleteSource', { name: s.name }) : `Delete source "${s.name}"?`
  if (!confirm(smsg)) return
  try{
    deletingSources.value = { ...(deletingSources.value||{}), [s.id]: true }
    const r = await authFetch(`${API}/api/ingest/sources/${s.id}/`, { method:'DELETE', headers: { ...authHeaders() } })
    if (r.ok) { await fetchSources() }
  }catch(_){ /* noop */ }
  finally{
    const m = { ...(deletingSources.value||{}) }; delete m[s.id]; deletingSources.value = m
  }
}

// Open a job (web → open URL; others → navigate to setup)
const openJob = (row)=>{
  const j = row?._raw || {}
  const mode = String(j.mode || '').toLowerCase()
  if (mode === 'web' && j?.payload?.url) {
    try { window.open(j.payload.url, '_blank', 'noopener') } catch (_) {}
    return
  }
  if (mode) router.push(`/connect/${mode}`)
}

// Edit action: route to appropriate setup UI used for adding sources/uploads
const editRow = (row)=>{
  // Jobs
  if (row?.type === 'job') {
    const j = row._raw || {}
    const mode = String(j.mode || '').toLowerCase()
    if (mode === 'web'){
      const u = j.payload?.url || j.payload?.start_url || ''
      const q = u ? (`?url=${encodeURIComponent(u)}`) : ''
      router.push(`/connect/web${q}`)
      return
    }
    if (mode){ router.push(`/connect/${mode}`); return }
  }
  // Documents
  if (isWebDoc(row)){
    const u = (row?._raw?.steps_json || {}).source_url || ''
    const q = u ? (`?url=${encodeURIComponent(u)}`) : ''
    router.push(`/connect/web${q}`)
    return
  }
  router.push('/connect/files')
}

// Delete a job (owner only)
const deleteJob = async (row)=>{
  const j = row?._raw
  if (!j || !j.id) return
  const jmsg = (typeof t === 'function') ? t('confirmDeleteJob', { name: row.title }) : `Delete job "${row.title}"? This will remove the import record.`
  if (!confirm(jmsg)) return
  try{
    deletingRows.value = { ...(deletingRows.value||{}), [row.id]: true }
    const r = await authFetch(`${API}/api/ingest/jobs/${j.id}/`, { method:'DELETE', headers: { ...authHeaders() } })
    if (r.ok) await fetchJobs()
  }catch(_){ /* ignore */ }
  finally{
    const m = { ...(deletingRows.value||{}) }; delete m[row.id]; deletingRows.value = m
  }
}

// Delete files associated with an upload job row (payload.file_ids)
const deleteUploadFiles = async (row)=>{
  const job = row?._raw
  const ids = job?.payload?.file_ids
  if (!Array.isArray(ids) || !ids.length) return
  const label = row.title || translateOr('documentsPage.filesCount', { count: ids.length }, `${ids.length} file(s)`)
  const umsg = (typeof t === 'function') ? t('confirmDeleteFiles', { name: label }) : `Delete ${label}? This cannot be undone.`
  if (!confirm(umsg)) return
  try {
    for (const id of ids) {
      await authFetch(`${API}/api/documents/${id}`, { method: 'DELETE', headers: { ...authHeaders() } })
    }
    jobs.value = jobs.value.filter(j => j.id !== job.id)
    await fetchDocs()
  } catch (_) { /* ignore */ }
}

</script>

<style scoped>
.page {
  background: var(--bg);
  min-height: 100vh;
  padding: 24px 32px;
  max-width: 1600px;
  margin: 0 auto;
}

/* Header */
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
  flex-wrap: wrap;
  gap: 16px;
}
.left {
  display: flex;
  align-items: center;
  gap: 24px;
  flex: 1;
}
.page-head h1 {
  font-size: 28px;
  font-weight: 800;
  margin: 0;
  letter-spacing: -0.03em;
}
.search {
  position: relative;
  max-width: 400px;
  width: 100%;
}
.search input {
  width: 100%;
  padding: 12px 16px;
  padding-right: 40px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--line);
  background: var(--card);
  box-shadow: var(--shadow-sm);
  transition: all 0.2s;
  font-size: 14px;
}
.search input:focus {
  border-color: var(--primary);
  box-shadow: var(--focus-ring);
}
.search .icon {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  opacity: 0.5;
  padding: 4px;
}
.search .icon:hover { opacity: 1; }

.right { display: flex; gap: 12px; }
.ghost {
  background: var(--card);
  border: 1px solid var(--line);
  color: var(--txt);
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 20px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: var(--shadow-sm);
}
.ghost:hover {
  transform: rotate(180deg);
  background: var(--bg);
  border-color: var(--primary);
  color: var(--primary);
}

/* Left Column Wrapper */
.left-col {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* Dropzone */
.dropzone {
  background: var(--card);
  border: 2px dashed var(--line);
  border-radius: var(--radius);
  padding: 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 0; /* Handled by gap in left-col */
}
.dropzone:hover, .dropzone.over {
  border-color: var(--primary);
  background: var(--primary-light);
}
.dz-inner { pointer-events: none; }
.cloud { font-size: 32px; margin-bottom: 8px; display: block; }
.dz-title { font-size: 16px; font-weight: 700; color: var(--txt); margin-bottom: 4px; }
.dz-sub { color: var(--muted); font-size: 13px; }

/* Grid Layout */
.grid {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 32px;
  align-items: start;
}
@media (max-width: 1024px) {
  .grid { grid-template-columns: 1fr; }
}

/* Panel / Table */
.panel {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  overflow: hidden;
}
.table-wrap { padding: 0; }
.table-tools {
  padding: 16px 24px;
  border-bottom: 1px solid var(--line);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg);
}
.chk {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--muted);
  cursor: pointer;
}
.info-line {
  padding: 12px 24px;
  background: #fffbeb;
  color: #b45309;
  font-size: 13px;
  border-bottom: 1px solid #fcd34d;
  display: none;
}

.tbl {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.tbl th {
  text-align: left;
  padding: 16px 24px;
  color: var(--muted);
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--line);
  background: var(--bg);
}
.tbl td {
  padding: 16px 24px;
  border-bottom: 1px solid var(--line);
  color: var(--txt);
  vertical-align: middle;
}
.tbl tr:last-child td { border-bottom: none; }
.tbl tr:hover td { background: var(--bg); }

.type-cell {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 600;
}
.type-ico {
  width: 36px;
  height: 36px;
  background: var(--bg);
  border-radius: 8px;
  display: grid;
  place-items: center;
  border: 1px solid var(--line);
  box-shadow: var(--shadow-sm);
}
.src-ico-img { width: 22px; height: 22px; object-fit: contain; }

.truncate {
  max-width: 300px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
  font-size: 15px;
}
.truncate a { color: var(--txt); transition: color 0.2s; }
.truncate a:hover { color: var(--primary); }

.badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: var(--radius-pill);
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: 0.02em;
}
.badge.imported { background: #dcfce7; color: #166534; }
.badge.processing { background: #e0f2fe; color: #075985; }
.badge.uploaded { background: #f1f5f9; color: #475569; }
.badge.failed { background: #fee2e2; color: #991b1b; }
.dots span { animation: blink 1.4s infinite both; }
.dots span:nth-child(2) { animation-delay: 0.2s; }
.dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink { 0% { opacity: 0.2; } 20% { opacity: 1; } 100% { opacity: 0.2; } }

/* Action Icons - Improved */
.row-actions {
  display: flex;
  gap: 8px;
  opacity: 0.6;
  transition: opacity 0.2s;
}
.tbl tr:hover .row-actions { opacity: 1; }
.icon-btn {
  width: 36px;
  height: 36px;
  padding: 8px;
  border-radius: 8px;
  border: 1px solid var(--line);
  background: var(--card);
  color: var(--muted);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  cursor: pointer;
}
.icon-btn:hover {
  background: var(--bg);
  color: var(--primary);
  border-color: var(--primary);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}
.icon-btn.danger:hover {
  color: var(--danger);
  background: #fef2f2;
  border-color: var(--danger);
}
.icon-svg { width: 18px; height: 18px; }

.table-footer {
  padding: 16px;
  border-top: 1px solid var(--line);
  text-align: center;
}
.load-more {
  background: var(--bg);
  border: 1px solid var(--line);
  color: var(--txt);
  padding: 10px 24px;
  font-size: 14px;
  font-weight: 600;
  border-radius: var(--radius-pill);
  cursor: pointer;
  transition: all 0.2s;
}
.load-more:hover {
  background: var(--card);
  border-color: var(--primary);
  color: var(--primary);
  box-shadow: var(--shadow-sm);
}

/* Sidebar / KPIs */
.side { display: flex; flex-direction: column; gap: 32px; }

.kpis {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
.kpi {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 20px;
  text-align: center;
  box-shadow: var(--shadow-sm);
}
.kpi:last-child { grid-column: span 2; }
.kpi-title { color: var(--muted); font-size: 12px; font-weight: 700; text-transform: uppercase; margin-bottom: 8px; }
.kpi-val { font-size: 32px; font-weight: 800; color: var(--txt); }
.kpi-val.ok { color: var(--success); }
.kpi-val.bad { color: var(--danger); }

.sources-head { margin-bottom: 16px; }
.sources-head h3 { font-size: 16px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }

.src-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr); /* 4 items per row */
  gap: 10px;
}
.src-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 8px;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.2s;
}
.src-btn:hover {
  transform: translateY(-2px);
  border-color: var(--primary);
  box-shadow: var(--shadow);
}
.src-ico-comp {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
}
.src-name { font-size: 11px; font-weight: 600; color: var(--txt); text-align: center; line-height: 1.2; }

/* Connected Sources Table */
.connected-table { margin-top: 32px; padding: 0; overflow: hidden; }
.connected-head { padding: 16px 24px; border-bottom: 1px solid var(--line); background: var(--bg); }
.conn-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.conn-table th { text-align: left; padding: 12px 24px; color: var(--muted); font-size: 12px; text-transform: uppercase; border-bottom: 1px solid var(--line); }
.conn-table td { padding: 12px 24px; border-bottom: 1px solid var(--line); }
.conn-name { display: flex; align-items: center; gap: 12px; }
.nm { font-weight: 600; color: var(--txt); }
.kind { font-size: 12px; color: var(--muted); }

/* Modal */
.modal{ position:fixed; inset:0; background:rgba(0,0,0,.35); display:grid; place-items:center; z-index:30; }
.modal-box{ width:min(860px, 96vw); background:var(--card); border-radius:14px; border:1px solid var(--line); box-shadow:0 18px 48px rgba(31,64,175,.18); }
.modal-head{ display:flex; align-items:center; justify-content:space-between; padding:12px 14px; border-bottom:1px solid var(--line); }
.close{ background:transparent; border:none; font-size:18px; cursor:pointer; }
.wizard-tabs{ display:flex; gap:8px; padding:8px 12px; border-bottom:1px solid var(--line); overflow-x:auto; }
.wtab{ border:1px solid var(--line); background:var(--card); color:var(--txt); border-radius:9px; padding:6px 10px; cursor:pointer; font-weight:800; }
.wtab.active{ background: rgba(96,165,250,.15); color: var(--blue); border-color:#c7dafb; }
.wizard-body{ padding:14px; }
.pane{ display:grid; gap:10px; }
.row{ display:grid; gap:6px; }
.row input{ border:1px solid var(--line); border-radius:10px; padding:9px 12px; background: var(--card); color: var(--txt); }
.actions{ display:flex; justify-content:flex-end; gap:8px; }
.status{ color:#1e3a8a; font-weight:800; }

.hidden{ display:none; }

@media (max-width: 990px){
  .grid{ grid-template-columns:1fr; }
}
@media (max-width: 640px){
  .kpis{ grid-template-columns:1fr; }
  .src-grid{ grid-template-columns: repeat(3, 1fr); }
}
</style>
