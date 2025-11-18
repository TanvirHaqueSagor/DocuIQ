<template>
  <div class="setup-wrap">
    <header class="head">
      <div class="back-row">
        <button class="ghost back-btn" @click="goBack">
          <span aria-hidden="true">←</span>
          <span>{{ t('sourceSetup.actions.back') }}</span>
        </button>
      </div>
      <div class="hero-card">
        <div class="hero-brand">
          <span class="hero-icon">{{ schema.emoji }}</span>
          <div>
            <h1>{{ schema.title }}</h1>
            <p class="sub">{{ schema.tagline }}</p>
            <p class="hero-help" v-if="schemaSupportsBrowser">{{ schema.browserConnectHelp }}</p>
          </div>
        </div>
        <div class="hero-actions" v-if="schemaSupportsBrowser">
          <button
            class="hero-connect"
            type="button"
            :disabled="browserConnecting"
            @click="startBrowserConnect"
          >
            {{ browserConnecting ? 'Opening…' : schema.heroConnectLabel }}
          </button>
          <button v-if="browserPopupOpen" class="ghost" type="button" @click="reopenBrowserPopup">
            Re-open window
          </button>
        </div>
      </div>
    </header>
    <p class="hero-status" v-if="browserStatus">{{ browserStatus }}</p>

    <div class="drawer-actions">
      <button class="ghost" type="button" @click="showInfoModal = true">View app details</button>
      <button class="ghost" type="button" @click="showPermissionsModal = true">View permissions</button>
    </div>

    <section class="card">
      <div v-if="supportsManual && isFileKind" class="pane">
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

      <div v-else-if="supportsManual" class="pane">
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
      <div v-else class="pane empty-pane">
        <p class="muted">
          Manual configuration is not required for this connector. Use the browser authorization above to finish setup.
        </p>
      </div>
      <div v-if="connectedNotice" class="pane success-pane" role="status">
        <div class="success-icon" aria-hidden="true">✅</div>
        <div>
          <h3 class="success-title">Connected</h3>
          <p class="muted">{{ connectedNotice }}</p>
        </div>
        <button class="ghost" type="button" @click="goDocuments">{{ t('sourceSetup.actions.viewDocuments') }}</button>
      </div>
    </section>
  </div>

  <div v-if="showInfoModal" class="modal-backdrop" @click.self="closeInfo">
    <section class="modal">
      <header>
        <h3>{{ t('sourceSetup.infoModalTitle', { name: schema.title }) }}</h3>
        <button class="modal-close" type="button" @click="closeInfo">×</button>
      </header>
      <dl>
        <div>
          <dt>{{ t('sourceSetup.info.category') }}</dt>
          <dd>{{ infoValue('category') }}</dd>
        </div>
        <div>
          <dt>{{ t('sourceSetup.info.developer') }}</dt>
          <dd>{{ infoValue('developer') }}</dd>
        </div>
        <div>
          <dt>{{ t('sourceSetup.info.website') }}</dt>
          <dd>
            <template v-if="isLinkField(schema.info.website)">
              <a
                class="icon-link"
                :href="schema.info.website"
                target="_blank"
                rel="noopener"
                :title="formatLinkLabel(schema.info.website)"
                :aria-label="formatLinkLabel(schema.info.website)"
              >
                <span class="sr-only">{{ formatLinkLabel(schema.info.website) }}</span>
                <span class="external-icon" aria-hidden="true">↗</span>
              </a>
            </template>
            <template v-else>{{ infoValue('website') }}</template>
          </dd>
        </div>
        <div>
          <dt>{{ t('sourceSetup.info.privacy') }}</dt>
          <dd>
            <template v-if="isLinkField(schema.info.privacy)">
              <a
                class="icon-link"
                :href="schema.info.privacy"
                target="_blank"
                rel="noopener"
                :title="formatLinkLabel(schema.info.privacy)"
                :aria-label="formatLinkLabel(schema.info.privacy)"
              >
                <span class="sr-only">{{ formatLinkLabel(schema.info.privacy) }}</span>
                <span class="external-icon" aria-hidden="true">↗</span>
              </a>
            </template>
            <template v-else>{{ infoValue('privacy') }}</template>
          </dd>
        </div>
      </dl>
    </section>
  </div>

  <div v-if="showPermissionsModal" class="modal-backdrop" @click.self="closePermissions">
    <section class="modal">
      <header>
        <h3>{{ t('sourceSetup.permissionsTitle') }}</h3>
        <button class="modal-close" type="button" @click="closePermissions">×</button>
      </header>
      <ul class="permission-list">
        <li>
          <strong>Explicit access only</strong>
          <p>{{ schema.info.permissions }}</p>
        </li>
        <li>
          <strong>You're in control</strong>
          <p>{{ schema.info.control }}</p>
        </li>
        <li>
          <strong>Know the risks</strong>
          <p>{{ schema.info.risks }}</p>
        </li>
      </ul>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, onBeforeUnmount, watch } from 'vue'
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
const manualConnectOnly = computed(() => kind.value === 'files' || kind.value === 'web')

const pickedFiles = ref([])
const filesForm = reactive({ title: '', tags: '', language: '' })
const name = ref('')
const config = reactive({})
const loading = ref(false)
const statusMsg = ref('')
const oauthConnected = ref(false)
const browserConnecting = ref(false)
const browserStatus = ref('')
const browserPopupOpen = ref(false)
const connectedNotice = ref('')
const showInfoModal = ref(false)
const showPermissionsModal = ref(false)
let browserPopup = null
let popupTimer = null

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

const goBack = () => {
  if (window.history.length > 1) router.back()
  else router.push('/documents')
}
const goDocuments = () => router.push('/documents')
const closeInfo = () => { showInfoModal.value = false }
const closePermissions = () => { showPermissionsModal.value = false }

const fakeOauth = () => {
  oauthConnected.value = true
}

const cleanupBrowserWatcher = () => {
  if (popupTimer) {
    clearInterval(popupTimer)
    popupTimer = null
  }
  browserPopup = null
  browserPopupOpen.value = false
}

const startBrowserConnect = () => {
  if (typeof window === 'undefined') return
  ensureAuth()
  browserStatus.value = ''
  browserConnecting.value = true
  if (browserPopup && !browserPopup.closed) {
    try { browserPopup.close() } catch (_) {}
  }
  cleanupBrowserWatcher()
  try {
    const url = schema.value.browserConnectUrl || `${API_BASE_URL}/api/ingest/oauth/start?kind=${encodeURIComponent(canonicalKind(kind.value) || 'files')}`
    const features = 'width=520,height=640,resizable=yes,scrollbars=yes'
    browserPopup = window.open(url, `docuiq-connect-${Date.now()}`, features)
    if (!browserPopup) {
      throw new Error('Popup blocked. Please allow pop-ups for DocuIQ.')
    }
    browserPopup.focus?.()
    browserPopupOpen.value = true
    browserStatus.value = 'Complete the authorization in the newly opened window.'
    popupTimer = window.setInterval(() => {
      if (!browserPopup || browserPopup.closed) {
        cleanupBrowserWatcher()
        browserConnecting.value = false
        if (!browserStatus.value) {
          browserStatus.value = 'Browser authorization window was closed.'
        }
      }
    }, 500)
  } catch (error) {
    browserConnecting.value = false
    browserStatus.value = `Unable to open browser flow: ${error?.message || error}`
  }
}

const reopenBrowserPopup = () => {
  if (browserPopupOpen.value && browserPopup && !browserPopup.closed) {
    browserPopup.focus?.()
    return
  }
  startBrowserConnect()
}

const handleBrowserMessage = (event) => {
  const data = event?.data
  if (!data || typeof data !== 'object') return
  if (data.type !== 'docuiq:oauthComplete') return
  const incomingKind = canonicalKind(data.kind || '')
  if (incomingKind && incomingKind !== canonicalKind(kind.value)) return
  cleanupBrowserWatcher()
  browserConnecting.value = false
  if (data.error) {
    browserStatus.value = `Authorization failed: ${data.error}`
    return
  }
  browserStatus.value = data.message || 'Authorization complete! You can now run this source.'
  statusMsg.value = t('sourceSetup.status.savedAndQueued')
  connectedNotice.value = data.message || `Your ${schema.value.title} connection is ready.`
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
    connectedNotice.value = runAfter
      ? `Queued a sync job for ${schema.value.title}.`
      : `${schema.value.title} saved. You can run it anytime from the Documents page.`
  } catch (error) {
    statusMsg.value = t('sourceSetup.status.error', { error: error.message || error })
  } finally {
    loading.value = false
  }
}

const CONNECTOR_ALIASES = {
  upload: 'files',
  file: 'files',
  files: 'files',
  drive: 'gdrive',
  googledrive: 'gdrive',
  'google-drive': 'gdrive',
  box: 'box',
  dropbox: 'dropbox',
  onedrive: 'onedrive',
  'one-drive': 'onedrive',
  sharepoint: 'sharepoint',
  msft: 'microsoft',
  ms_teams: 'teams',
  microsoftteams: 'teams',
  'microsoft-teams': 'teams',
  slack: 'slack',
  jira: 'jira',
  confluence: 'confluence',
  postgres: 'postgres',
  postgresql: 'postgres',
  mysql: 'mysql',
  mongodb: 'mongodb',
  mongo: 'mongodb',
  snowflake: 'snowflake',
  bigquery: 'bigquery',
  elasticsearch: 'elasticsearch',
  opensearch: 'opensearch',
  'open-search': 'opensearch',
  rss: 'rss',
  feed: 'rss',
  api: 'api',
}

const canonicalKind = (value) => {
  const key = String(value || '').toLowerCase().trim()
  if (!key) return ''
  return CONNECTOR_ALIASES[key] || key
}

const CONNECTOR_SCHEMAS = {
  files: {
    title: 'Local files',
    emoji: '📁',
    description: 'Upload PDFs, Word docs, spreadsheets, decks, or media directly from your computer.',
  },
  gdrive: {
    title: 'Google Drive',
    emoji: '🟩',
    description: 'Sync specific folders via a service account.',
    fields: [
      { key: 'service_account_json', label: 'Service account JSON', type: 'json', required: true, placeholder: '{ "type": "service_account", ... }' },
      { key: 'folder_id', label: 'Folder ID', type: 'text', required: true, placeholder: 'e.g. 0Bxx0-example' },
      { key: 'impersonate_user', label: 'Delegated user email', type: 'text', placeholder: 'user@company.com' },
      { key: 'watch_changes', label: 'Watch for changes', type: 'checkbox', help: 'Auto-sync whenever files change.' },
    ],
  },
  dropbox: {
    title: 'Dropbox',
    emoji: '🟦',
    description: 'Mirror a Dropbox folder using a long-lived access token.',
    fields: [
      { key: 'access_token', label: 'Access token', type: 'password', required: true, placeholder: 'sl.BC0...' },
      { key: 'folder_path', label: 'Folder path', type: 'text', required: true, placeholder: '/Docs/Contracts' },
      { key: 'team', label: 'Team Dropbox?', type: 'checkbox', help: 'Check if using a Business team workspace.' },
    ],
  },
  onedrive: {
    title: 'OneDrive',
    emoji: '🟦',
    description: 'Connect a Microsoft OneDrive drive or SharePoint-backed library.',
    fields: [
      { key: 'client_id', label: 'Client ID', type: 'text', required: true },
      { key: 'client_secret', label: 'Client secret', type: 'password', required: true },
      { key: 'tenant_id', label: 'Tenant ID', type: 'text', required: true },
      { key: 'drive_id', label: 'Drive ID or share link', type: 'text', required: true },
      { key: 'folder_path', label: 'Folder path (optional)', type: 'text', placeholder: '/Shared Documents/Policies' },
    ],
  },
  box: {
    title: 'Box',
    emoji: '📦',
    description: 'Mirror Box folders using a JWT app.',
    fields: [
      { key: 'client_id', label: 'Client ID', type: 'text', required: true },
      { key: 'client_secret', label: 'Client secret', type: 'password', required: true },
      { key: 'enterprise_id', label: 'Enterprise ID', type: 'text', required: true },
      { key: 'public_key_id', label: 'Public key ID', type: 'text' },
      { key: 'private_key', label: 'Private key', type: 'textarea', required: true },
      { key: 'folder_id', label: 'Folder ID', type: 'text', required: true },
    ],
  },
  sharepoint: {
    title: 'SharePoint',
    emoji: '🏢',
    description: 'Ingest documents from SharePoint Online sites.',
    fields: [
      { key: 'site_url', label: 'Site URL', type: 'url', required: true, placeholder: 'https://contoso.sharepoint.com/sites/Docs' },
      { key: 'library', label: 'Document library', type: 'text', required: true, placeholder: 'Shared Documents' },
      { key: 'client_id', label: 'App (client) ID', type: 'text', required: true },
      { key: 'client_secret', label: 'Client secret', type: 'password', required: true },
    ],
  },
  confluence: {
    title: 'Confluence',
    emoji: '📘',
    description: 'Sync pages from Atlassian Confluence spaces.',
    fields: [
      { key: 'base_url', label: 'Base URL', type: 'url', required: true, placeholder: 'https://company.atlassian.net/wiki' },
      { key: 'email', label: 'Account email', type: 'text', required: true },
      { key: 'api_token', label: 'API token', type: 'password', required: true },
      { key: 'space_keys', label: 'Space keys', type: 'multi', placeholder: 'HR,IT,SALES' },
      { key: 'include_archived', label: 'Include archived pages', type: 'checkbox' },
    ],
  },
  notion: {
    title: 'Notion',
    emoji: '⬛',
    description: 'Pull shared Notion databases and pages.',
    fields: [
      { key: 'integration_token', label: 'Integration token', type: 'password', required: true },
      { key: 'database_ids', label: 'Database IDs', type: 'multi', placeholder: 'db-id-1,db-id-2' },
      { key: 'include_archived', label: 'Sync archived pages', type: 'checkbox' },
    ],
  },
  airtable: {
    title: 'Airtable',
    emoji: '📋',
    description: 'Fetch records from Airtable bases.',
    fields: [
      { key: 'api_key', label: 'API key', type: 'password', required: true },
      { key: 'base_id', label: 'Base ID', type: 'text', required: true },
      { key: 'table_name', label: 'Table name', type: 'text', required: true },
      { key: 'view', label: 'View (optional)', type: 'text' },
    ],
  },
  gmail: {
    title: 'Gmail',
    emoji: '✉️',
    description: 'Index inbound or outbound Gmail threads.',
    fields: [
      { key: 'service_account_json', label: 'Service account JSON', type: 'json', required: true },
      { key: 'delegated_user', label: 'Mailbox email', type: 'text', required: true },
      { key: 'label', label: 'Label filter', type: 'text', placeholder: 'support' },
      { key: 'sync_from_date', label: 'Sync from date', type: 'date' },
    ],
  },
  outlook: {
    title: 'Outlook / Microsoft 365',
    emoji: '✉️',
    description: 'Connect Exchange Online or Outlook shared mailboxes.',
    fields: [
      { key: 'tenant_id', label: 'Tenant ID', type: 'text', required: true },
      { key: 'client_id', label: 'Client ID', type: 'text', required: true },
      { key: 'client_secret', label: 'Client secret', type: 'password', required: true },
      { key: 'mailbox', label: 'Mailbox address', type: 'text', required: true },
      { key: 'sync_from_date', label: 'Sync from date', type: 'date' },
    ],
  },
  slack: {
    title: 'Slack',
    emoji: '🟩',
    description: 'Sync Slack channels, threads, and file shares.',
    fields: [
      { key: 'bot_token', label: 'Bot token', type: 'password', required: true, placeholder: 'xoxb-...' },
      { key: 'channel_ids', label: 'Channel IDs', type: 'multi', placeholder: 'C01ABCD23, C09XYZ78' },
      { key: 'lookback_days', label: 'History (days)', type: 'number', placeholder: '30' },
    ],
  },
  teams: {
    title: 'Microsoft Teams',
    emoji: '🟦',
    description: 'Mirror Teams channels using the Graph API.',
    fields: [
      { key: 'tenant_id', label: 'Tenant ID', type: 'text', required: true },
      { key: 'client_id', label: 'Client ID', type: 'text', required: true },
      { key: 'client_secret', label: 'Client secret', type: 'password', required: true },
      { key: 'team_id', label: 'Team ID', type: 'text', required: true },
      { key: 'channel_id', label: 'Channel ID', type: 'text', required: true },
    ],
  },
  zoom: {
    title: 'Zoom',
    emoji: '🎥',
    description: 'Ingest meeting transcripts and recordings.',
    fields: [
      { key: 'account_id', label: 'Account ID', type: 'text', required: true },
      { key: 'client_id', label: 'Client ID', type: 'text', required: true },
      { key: 'client_secret', label: 'Client secret', type: 'password', required: true },
      { key: 'recording_type', label: 'Recording type', type: 'select', options: [
        { value: 'cloud', label: 'Cloud recordings' },
        { value: 'local', label: 'Local uploads' },
      ] },
      { key: 'lookback_days', label: 'History (days)', type: 'number', placeholder: '14' },
    ],
  },
  github: {
    title: 'GitHub',
    emoji: '💻',
    description: 'Index repositories, issues, and pull requests.',
    fields: [
      { key: 'access_token', label: 'PAT / app token', type: 'password', required: true },
      { key: 'organization', label: 'Organization (optional)', type: 'text' },
      { key: 'repo_names', label: 'Repositories', type: 'multi', placeholder: 'docuiq/api, docuiq/frontend' },
      { key: 'include_private', label: 'Include private repos', type: 'checkbox' },
    ],
  },
  gitlab: {
    title: 'GitLab',
    emoji: '💻',
    description: 'Mirror self-hosted or SaaS GitLab projects.',
    fields: [
      { key: 'base_url', label: 'Base URL', type: 'url', placeholder: 'https://gitlab.com' },
      { key: 'access_token', label: 'Access token', type: 'password', required: true },
      { key: 'group', label: 'Group or namespace', type: 'text' },
      { key: 'project_ids', label: 'Project IDs', type: 'multi' },
    ],
  },
  jira: {
    title: 'Jira',
    emoji: '🟦',
    description: 'Sync Jira issues, descriptions, and comments.',
    fields: [
      { key: 'base_url', label: 'Base URL', type: 'url', required: true, placeholder: 'https://company.atlassian.net' },
      { key: 'email', label: 'Account email', type: 'text', required: true },
      { key: 'api_token', label: 'API token', type: 'password', required: true },
      { key: 'project_keys', label: 'Project keys', type: 'multi', placeholder: 'SUP,PLAT' },
    ],
  },
  trello: {
    title: 'Trello',
    emoji: '🗂️',
    description: 'Index cards from selected boards.',
    fields: [
      { key: 'api_key', label: 'API key', type: 'text', required: true },
      { key: 'token', label: 'Token', type: 'password', required: true },
      { key: 'board_ids', label: 'Board IDs', type: 'multi' },
      { key: 'include_archived', label: 'Include archived cards', type: 'checkbox' },
    ],
  },
  postgres: {
    title: 'PostgreSQL',
    emoji: '🗄️',
    description: 'Run SQL snapshots against a Postgres database.',
    fields: [
      { key: 'host', label: 'Host', type: 'text', required: true },
      { key: 'port', label: 'Port', type: 'number', placeholder: '5432' },
      { key: 'database', label: 'Database', type: 'text', required: true },
      { key: 'user', label: 'User', type: 'text', required: true },
      { key: 'password', label: 'Password', type: 'password', required: true },
      { key: 'schemas', label: 'Schemas', type: 'multi', placeholder: 'public,analytics' },
      { key: 'tables', label: 'Tables', type: 'multi', placeholder: 'documents,customers' },
    ],
  },
  mysql: {
    title: 'MySQL',
    emoji: '🗄️',
    description: 'Ingest tables from MySQL or MariaDB.',
    fields: [
      { key: 'host', label: 'Host', type: 'text', required: true },
      { key: 'port', label: 'Port', type: 'number', placeholder: '3306' },
      { key: 'database', label: 'Database', type: 'text', required: true },
      { key: 'user', label: 'User', type: 'text', required: true },
      { key: 'password', label: 'Password', type: 'password', required: true },
      { key: 'tables', label: 'Tables', type: 'multi' },
    ],
  },
  mongodb: {
    title: 'MongoDB',
    emoji: '🍃',
    description: 'Snapshot documents from MongoDB clusters.',
    fields: [
      { key: 'uri', label: 'Connection URI', type: 'text', required: true },
      { key: 'database', label: 'Database', type: 'text', required: true },
      { key: 'collections', label: 'Collections', type: 'multi', placeholder: 'tickets,events' },
    ],
  },
  snowflake: {
    title: 'Snowflake',
    emoji: '❄️',
    description: 'Query Snowflake tables on a schedule.',
    fields: [
      { key: 'account', label: 'Account', type: 'text', required: true },
      { key: 'user', label: 'User', type: 'text', required: true },
      { key: 'password', label: 'Password', type: 'password', required: true },
      { key: 'warehouse', label: 'Warehouse', type: 'text', required: true },
      { key: 'database', label: 'Database', type: 'text', required: true },
      { key: 'schema', label: 'Schema', type: 'text', required: true },
      { key: 'tables', label: 'Tables', type: 'multi' },
    ],
  },
  bigquery: {
    title: 'BigQuery',
    emoji: '🟨',
    description: 'Pull query results from Google BigQuery.',
    fields: [
      { key: 'project_id', label: 'Project ID', type: 'text', required: true },
      { key: 'dataset', label: 'Dataset', type: 'text', required: true },
      { key: 'table', label: 'Table', type: 'text', required: true },
      { key: 'service_account_json', label: 'Service account JSON', type: 'json', required: true },
    ],
  },
  elasticsearch: {
    title: 'Elasticsearch / OpenSearch',
    emoji: '🔍',
    description: 'Mirror documents from existing search clusters.',
    fields: [
      { key: 'host', label: 'Host or cloud ID', type: 'text', required: true },
      { key: 'username', label: 'Username', type: 'text' },
      { key: 'password', label: 'Password', type: 'password' },
      { key: 'index_pattern', label: 'Index pattern', type: 'text', required: true, placeholder: 'docs-*' },
    ],
  },
  rss: {
    title: 'RSS / Atom feeds',
    emoji: '📰',
    description: 'Follow industry or company feeds.',
    fields: [
      { key: 'feed_url', label: 'Feed URL', type: 'url', required: true },
      { key: 'frequency', label: 'Refresh cadence', type: 'select', options: [
        { value: 'hourly', label: 'Hourly' },
        { value: 'daily', label: 'Daily' },
        { value: 'weekly', label: 'Weekly' },
      ] },
    ],
  },
  api: {
    title: 'Custom API',
    emoji: '🔗',
    description: 'Fetch data from any authenticated endpoint.',
    fields: [
      { key: 'endpoint', label: 'Endpoint URL', type: 'url', required: true },
      { key: 'auth_header', label: 'Authorization header', type: 'text', placeholder: 'Bearer ...' },
      { key: 'method', label: 'HTTP method', type: 'select', options: [
        { value: 'GET', label: 'GET' },
        { value: 'POST', label: 'POST' },
      ] },
      { key: 'body', label: 'Request body (JSON)', type: 'textarea', placeholder: '{ "status": "open" }' },
      { key: 'cron', label: 'Schedule (cron)', type: 'text', placeholder: '0 * * * *' },
    ],
  },
  bloomberg: {
    title: 'Bloomberg',
    emoji: '📈',
    description: 'Ingest Bloomberg data exports.',
    fields: [
      { key: 'sftp_host', label: 'SFTP host', type: 'text', required: true },
      { key: 'username', label: 'Username', type: 'text', required: true },
      { key: 'password', label: 'Password', type: 'password', required: true },
      { key: 'folder', label: 'Remote folder', type: 'text', required: true },
    ],
  },
  refinitiv: {
    title: 'Refinitiv',
    emoji: '📈',
    description: 'Bring in Refinitiv DataScope extractions.',
    fields: [
      { key: 'username', label: 'Username', type: 'text', required: true },
      { key: 'password', label: 'Password', type: 'password', required: true },
      { key: 'sftp_host', label: 'SFTP host', type: 'text', placeholder: 'sftp.datascope.refinitiv.com' },
      { key: 'folder', label: 'Folder', type: 'text' },
    ],
  },
  esg: {
    title: 'ESG APIs',
    emoji: '🌱',
    description: 'Collect ESG disclosures from providers.',
    fields: [
      { key: 'provider', label: 'Provider', type: 'select', options: [
        { value: 'sustainalytics', label: 'Sustainalytics' },
        { value: 'msci', label: 'MSCI' },
        { value: 'other', label: 'Other' },
      ] },
      { key: 'api_key', label: 'API key / token', type: 'password', required: true },
      { key: 'universe', label: 'Universe / tickers', type: 'multi', placeholder: 'AAPL,MSFT' },
    ],
  },
  linkedin: {
    title: 'LinkedIn',
    emoji: '🔮',
    description: 'Capture company page posts and analytics.',
    fields: [
      { key: 'organization_id', label: 'Organization ID', type: 'text', required: true },
      { key: 'access_token', label: 'Access token', type: 'password', required: true },
      { key: 'include_comments', label: 'Include comments', type: 'checkbox' },
    ],
  },
  twitter: {
    title: 'Twitter / X',
    emoji: '🔮',
    description: 'Mirror tweets from handles or searches.',
    fields: [
      { key: 'bearer_token', label: 'Bearer token', type: 'password', required: true },
      { key: 'handle', label: 'Handle or query', type: 'text', required: true, placeholder: '@docuiq' },
      { key: 'include_replies', label: 'Include replies', type: 'checkbox' },
    ],
  },
  gcal: {
    title: 'Google Calendar',
    emoji: '📆',
    description: 'Sync events for briefings or exec updates.',
    fields: [
      { key: 'service_account_json', label: 'Service account JSON', type: 'json', required: true },
      { key: 'calendar_id', label: 'Calendar ID', type: 'text', required: true, placeholder: 'ops@company.com' },
      { key: 'sync_from_date', label: 'Sync from date', type: 'date' },
    ],
  },
  figma: {
    title: 'Figma',
    emoji: '🎨',
    description: 'Index design files, comments, and handoff notes.',
    fields: [
      { key: 'personal_access_token', label: 'Personal access token', type: 'password', required: true },
      { key: 'team_id', label: 'Team ID', type: 'text', placeholder: '1234567890' },
      { key: 'file_keys', label: 'File keys', type: 'multi', placeholder: 'AbCdEf123' },
    ],
  },
}

const CONNECTOR_INFO = {
  default: {
    tagline: 'Connect this data source to DocuIQ',
    category: 'Knowledge',
    developer: 'DocuIQ',
    permissions: 'DocuIQ only uses this connector with your explicit approval and scopes.',
    control: 'Disable or remove the connector anytime from the Documents → Sources panel.',
    risks: 'Third-party connectors may access workspace data—review their policies before granting access.',
  },
  files: { tagline: 'Upload documents directly from your device', category: 'Local File Source', developer: 'N/A', website: null, privacy: null },
  web: { tagline: 'Capture content from public webpages', category: 'Web Page / URL Capture', developer: 'N/A', website: null, privacy: null },
  gdrive: { tagline: 'Sync folders from Google Drive', category: 'Cloud Storage', developer: 'Google LLC', website: 'https://www.google.com/drive/', privacy: 'https://policies.google.com/privacy' },
  dropbox: { tagline: 'Find and access your Dropbox files', category: 'Cloud Storage', developer: 'Dropbox, Inc.', website: 'https://www.dropbox.com/', privacy: 'https://www.dropbox.com/privacy' },
  onedrive: { tagline: 'Mirror OneDrive libraries', category: 'Cloud Storage', developer: 'Microsoft Corporation', website: 'https://onedrive.live.com/', privacy: 'https://privacy.microsoft.com/' },
  box: { tagline: 'Manage Box content inside DocuIQ', category: 'Cloud Content Management', developer: 'Box, Inc.', website: 'https://www.box.com/', privacy: 'https://www.box.com/legal/privacypolicy' },
  sharepoint: { tagline: 'Bring in SharePoint Online sites', category: 'Document Management / Collaboration', developer: 'Microsoft Corporation', website: 'https://www.microsoft.com/sharepoint', privacy: 'https://privacy.microsoft.com/' },
  confluence: { tagline: 'Sync pages from Confluence spaces', category: 'Knowledge Base / Documentation', developer: 'Atlassian', website: 'https://www.atlassian.com/software/confluence', privacy: 'https://www.atlassian.com/legal/privacy-policy' },
  notion: { tagline: 'Pull shared Notion databases and pages', category: 'Workspace / Knowledge Base', developer: 'Notion Labs, Inc.', website: 'https://www.notion.so/', privacy: 'https://www.notion.so/help/privacy' },
  airtable: { tagline: 'Fetch Airtable bases and tables', category: 'Database / Collaboration Platform', developer: 'Airtable, Inc.', website: 'https://www.airtable.com/', privacy: 'https://www.airtable.com/privacy' },
  gmail: { tagline: 'Index Gmail messages', category: 'Email', developer: 'Google LLC', website: 'https://mail.google.com/', privacy: 'https://policies.google.com/privacy' },
  outlook: { tagline: 'Connect Outlook or Microsoft 365 mailboxes', category: 'Email', developer: 'Microsoft Corporation', website: 'https://outlook.live.com/', privacy: 'https://privacy.microsoft.com/' },
  slack: { tagline: 'Bring Slack channels into context', category: 'Team Messaging / Collaboration', developer: 'Slack Technologies (Salesforce)', website: 'https://slack.com/', privacy: 'https://slack.com/trust/privacy/privacy-policy' },
  teams: { tagline: 'Mirror Microsoft Teams channels', category: 'Team Collaboration', developer: 'Microsoft Corporation', website: 'https://www.microsoft.com/microsoft-teams', privacy: 'https://privacy.microsoft.com/' },
  zoom: { tagline: 'Ingest Zoom recordings and transcripts', category: 'Video Conferencing', developer: 'Zoom Video Communications, Inc.', website: 'https://www.zoom.com/', privacy: 'https://www.zoom.com/en/privacy' },
  github: { tagline: 'Analyze GitHub repos, issues, and PRs', category: 'Code Hosting / Version Control', developer: 'GitHub, Inc. (Microsoft)', website: 'https://github.com/', privacy: 'https://github.com/privacy' },
  gitlab: { tagline: 'Sync GitLab projects and issues', category: 'DevOps / Code Hosting', developer: 'GitLab Inc.', website: 'https://gitlab.com/', privacy: 'https://about.gitlab.com/privacy/' },
  jira: { tagline: 'Reference Jira issues and workflows', category: 'Project Management', developer: 'Atlassian', website: 'https://www.atlassian.com/software/jira', privacy: 'https://www.atlassian.com/legal/privacy-policy' },
  trello: { tagline: 'Pull Trello boards and cards', category: 'Kanban / Project Management', developer: 'Atlassian', website: 'https://trello.com/', privacy: 'https://www.atlassian.com/legal/privacy-policy' },
  postgres: { tagline: 'Query PostgreSQL databases', category: 'Database', developer: 'PostgreSQL Global Development Group', website: 'https://www.postgresql.org/', privacy: 'https://www.postgresql.org/about/policies/privacy/' },
  mysql: { tagline: 'Capture data from MySQL or MariaDB', category: 'Database', developer: 'Oracle Corporation', website: 'https://www.mysql.com/', privacy: 'https://www.oracle.com/legal/privacy/' },
  mongodb: { tagline: 'Snapshot MongoDB collections', category: 'NoSQL Database', developer: 'MongoDB, Inc.', website: 'https://www.mongodb.com/', privacy: 'https://www.mongodb.com/legal/privacy-policy' },
  snowflake: { tagline: 'Run Snowflake SQL extracts', category: 'Cloud Data Warehouse', developer: 'Snowflake Inc.', website: 'https://www.snowflake.com/', privacy: 'https://www.snowflake.com/legal/privacy/' },
  bigquery: { tagline: 'Fetch datasets from Google BigQuery', category: 'Cloud Data Warehouse', developer: 'Google LLC', website: 'https://cloud.google.com/bigquery', privacy: 'https://policies.google.com/privacy' },
  elasticsearch: { tagline: 'Mirror Elasticsearch clusters', category: 'Search Engine / Analytics', developer: 'Elastic NV', website: 'https://www.elastic.co/', privacy: 'https://www.elastic.co/legal/privacy-statement' },
  opensearch: { tagline: 'Connect OpenSearch clusters', category: 'Search Engine / Analytics', developer: 'OpenSearch Project (Amazon-led)', website: 'https://opensearch.org/', privacy: 'https://www.amazon.com/privacy' },
  rss: { tagline: 'Follow RSS / Atom feeds', category: 'Web Feeds', developer: 'N/A', website: null, privacy: null },
  api: { tagline: 'Connect any custom API endpoint', category: 'API Connector', developer: 'N/A', website: null, privacy: null },
  bloomberg: { tagline: 'Pull Bloomberg Data License exports', category: 'Financial Market Data', developer: 'Bloomberg L.P.', website: 'https://www.bloomberg.com/professional/', privacy: 'https://www.bloomberg.com/notices/privacy/' },
  refinitiv: { tagline: 'Ingest Refinitiv DataScope batches', category: 'Financial Market Data', developer: 'Refinitiv (LSEG)', website: 'https://www.lseg.com/en/data-analytics', privacy: 'https://www.lseg.com/en/privacy' },
  esg: { tagline: 'Aggregate ESG disclosures from providers', category: 'ESG Ratings / Data', developer: 'Various (MSCI, Sustainalytics, S&P, FTSE)', website: 'Varies', privacy: 'Varies' },
  linkedin: { tagline: 'Monitor LinkedIn company updates', category: 'Social Network', developer: 'LinkedIn Corporation', website: 'https://www.linkedin.com/', privacy: 'https://www.linkedin.com/legal/privacy-policy' },
  twitter: { tagline: 'Track posts from X (Twitter)', category: 'Social Media', developer: 'X Corp.', website: 'https://x.com/', privacy: 'https://x.com/en/privacy' },
  gcal: { tagline: 'Sync Google Calendar events', category: 'Calendar / Productivity', developer: 'Google LLC', website: 'https://calendar.google.com/', privacy: 'https://policies.google.com/privacy' },
  figma: { tagline: 'Index Figma files, comments, and specs', category: 'Design / Prototyping', developer: 'Figma, Inc.', website: 'https://www.figma.com/', privacy: 'https://www.figma.com/privacy/' },
}

const schemaFor = (rawKey) => {
  const base = (title, emoji, description, fields = [], extras = {}) => ({
    title,
    emoji,
    description,
    fields,
    ...extras,
  })

  const key = canonicalKind(String(rawKey || ''))
  if (key === 'web') {
    return base(
      translate('sourceSetup.schemas.web.title', 'Website'),
      '🌐',
      translate('sourceSetup.schemas.web.description', 'Scrape or crawl a website'),
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
  }
  if (key === 's3') {
    return base(
      translate('sourceSetup.schemas.s3.title', 'AWS S3'),
      '🟦',
      translate('sourceSetup.schemas.s3.description', 'Connect an S3 bucket/prefix'),
      [
        { key: 'bucket', label: translate('sourceSetup.schemas.s3.fields.bucket.label', 'Bucket'), type: 'text', required: true },
        { key: 'prefix', label: translate('sourceSetup.schemas.s3.fields.prefix.label', 'Prefix'), type: 'text', placeholder: translate('sourceSetup.schemas.s3.fields.prefix.placeholder', 'folder/path/') },
        { key: 'sync', label: translate('sourceSetup.schemas.s3.fields.sync.label', 'Keep in sync'), type: 'checkbox', help: translate('sourceSetup.schemas.s3.fields.sync.help', 'Auto-sync folder') },
      ],
    )
  }
  const def = CONNECTOR_SCHEMAS[key] || CONNECTOR_SCHEMAS[rawKey]
  if (def) {
    return base(
      translate(`sourceSetup.schemas.${key}.title`, def.title),
      def.emoji || '🔗',
      translate(`sourceSetup.schemas.${key}.description`, def.description || 'Configure your source'),
      (def.fields || []).map((field) => ({ ...field })),
      {
        browserConnectPath: def.browserConnectPath,
        browserConnectUrl: def.browserConnectUrl,
        browserConnectLabel: def.browserConnectLabel,
        browserConnectHelp: def.browserConnectHelp,
        browserConnect: def.browserConnect,
      },
    )
  }
  return base(
    translate(`sourceSetup.schemas.${key}.title`, key ? key.toUpperCase() : 'Source'),
    '🔗',
    translate(`sourceSetup.schemas.${key}.description`, 'Configure your source connection details'),
    [],
    { browserConnect: true },
  )
}

const schema = computed(() => {
  const descriptor = schemaFor(kind.value)
  const normalizedKind = canonicalKind(kind.value || descriptor?.title || '')
  const fallbackQuery = normalizedKind ? `?kind=${encodeURIComponent(normalizedKind)}` : ''
  const info = { ...CONNECTOR_INFO.default, ...(CONNECTOR_INFO[normalizedKind] || {}) }
  let browserConnectUrl = descriptor.browserConnectUrl || descriptor.browserConnectPath || ''
  if (browserConnectUrl && !browserConnectUrl.startsWith('http')) {
    browserConnectUrl = `${API_BASE_URL}${browserConnectUrl.startsWith('/') ? browserConnectUrl : `/${browserConnectUrl}`}`
  }
  if (!browserConnectUrl) {
    browserConnectUrl = `${API_BASE_URL}/api/ingest/oauth/start${fallbackQuery}`
  }
  return {
    ...descriptor,
    browserConnect: descriptor.browserConnect !== false,
    browserConnectLabel: descriptor.browserConnectLabel || 'Connect via browser',
    browserConnectHelp: descriptor.browserConnectHelp || 'Authorize DocuIQ from a secure browser pop-up. Once complete, the connection will appear in Documents › Sources.',
    browserConnectUrl,
    heroConnectLabel: descriptor.heroConnectLabel || `Connect ${descriptor.title}`,
    tagline: descriptor.tagline || info.tagline || descriptor.description,
    info,
  }
})

const schemaSupportsBrowser = computed(() => !manualConnectOnly.value && !!schema.value?.browserConnect)
const supportsManual = computed(() => {
  if (isFileKind.value) return true
  return (schema.value?.fields || []).length > 0
})

onMounted(() => {
  try {
    const qp = route.query || {}
    if (qp.name) name.value = String(qp.name)
  } catch (_) {}
  if (typeof window !== 'undefined') {
    window.addEventListener('message', handleBrowserMessage)
  }
})

watch(kind, () => {
  name.value = ''
  statusMsg.value = ''
  oauthConnected.value = false
  pickedFiles.value = []
  Object.keys(config).forEach((key) => { delete config[key] })
  browserStatus.value = ''
  browserConnecting.value = false
  connectedNotice.value = ''
  showInfoModal.value = false
  showPermissionsModal.value = false
  cleanupBrowserWatcher()
})

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('message', handleBrowserMessage)
  }
  cleanupBrowserWatcher()
})

const infoUnavailable = computed(() => t('sourceSetup.info.notAvailable'))

function infoValue(field) {
  const value = schema.value?.info?.[field]
  return value && String(value).trim() ? value : infoUnavailable.value
}

function isLinkField(value) {
  return typeof value === 'string' && /^https?:\/\//i.test(value)
}

function formatLinkLabel(value) {
  if (!value) return ''
  try {
    const url = new URL(value)
    return url.hostname.replace(/^www\\./, '')
  } catch (_) {
    return value
  }
}
</script>

<style scoped>
.setup-wrap { display: grid; gap: 18px; padding: 16px 16px 32px; }
.head { display:grid; gap:12px; align-items:flex-start; }
.back-row{ display:flex; justify-content:flex-end; }
.hero-card { width:100%; background:var(--card); border:1px solid var(--line); border-radius:18px; padding:18px; display:flex; justify-content:space-between; align-items:center; box-shadow:var(--md-shadow-1); }
.hero-brand { display:flex; gap:12px; align-items:center; }
.hero-icon { font-size:32px; }
.hero-brand h1 { margin:0; font-size:24px; font-weight:800; color:var(--txt); }
.hero-brand .sub { margin:6px 0 4px; color:var(--muted); }
.hero-help { margin:0; color:var(--muted); font-size:.9rem; }
.hero-actions { display:flex; gap:10px; align-items:center; flex-wrap:wrap; }
.hero-connect { background:#0f172a; color:#fff; border:none; border-radius:999px; padding:10px 20px; font-weight:700; box-shadow:0 12px 36px rgba(15,23,42,0.25); cursor:pointer; }
.hero-connect:disabled { opacity:.6; cursor:not-allowed; box-shadow:none; }
.hero-status { margin:0; color:var(--muted); font-weight:600; }
.ghost { border:1px solid var(--line); background:var(--card); border-radius:8px; padding:8px 12px; cursor:pointer; font-weight:600; display:inline-flex; gap:6px; align-items:center; }
.ghost.back-btn span:first-child { font-size:14px; }
.drawer-actions { display:flex; gap:10px; flex-wrap:wrap; margin-top:8px; }
.permission-list { list-style:none; padding:0; margin:0; display:grid; gap:12px; }
.permission-list li { border:1px solid rgba(15,23,42,0.08); border-radius:12px; padding:12px; background:rgba(148,163,184,0.12); }
.permission-list strong { display:block; margin-bottom:4px; color:var(--txt); }
.permission-list p { margin:0; color:var(--muted); line-height:1.4; }
.card { background:var(--card); border:1px solid var(--line); border-radius:16px; padding:24px; display:grid; gap:16px; box-shadow:var(--md-shadow-1); }
.pane { display:grid; gap:12px; }
.row { display:grid; gap:6px; }
.row.inline { grid-auto-flow: column; justify-content: start; align-items: center; }
.row input[type="text"], .row input[type="number"], .row input[type="url"], .row input:not([type]), .row textarea, .row select { border:1px solid #d5def1; border-radius:8px; padding:9px 12px; background:#f8faff; font-size:.95rem; }
.row textarea { resize:vertical; }
.muted { color:#94a3b8; font-size:.85rem; }
.actions { display:flex; gap:10px; justify-content:flex-end; margin-top:6px; }
.actions.wrap { flex-wrap:wrap; justify-content:flex-start; }
.primary, .ghost { font-weight:700; }
.primary { background:#2563eb; color:#fff; border:1px solid #2563eb; border-radius:8px; padding:9px 12px; cursor:pointer; }
.primary:disabled { opacity:.6; cursor:not-allowed; }
.ghost:disabled { opacity:.6; cursor:not-allowed; }
.status { padding:10px 12px; font-weight:600; }
.hint { color:#607d8b; font-size:.85rem; }
.picked { list-style:disc; padding-left:20px; margin:0; color:#2f3b52; }
.oauth-box { display:flex; gap:10px; align-items:center; }
.btn { border:1px solid var(--line); background:var(--card); color:var(--blue); border-radius:8px; padding:8px 12px; cursor:pointer; font-weight:600; }
.empty-pane { background:#f8fafc; border-radius:12px; padding:16px; }
.success-pane { display:flex; align-items:center; gap:14px; border:1px solid rgba(34,197,94,0.4); background:rgba(34,197,94,0.08); border-radius:16px; padding:16px; }
.success-icon { font-size:28px; }
.success-title { margin:0 0 4px; font-size:1.1rem; color:#15803d; }
.modal-backdrop { position:fixed; inset:0; background:rgba(15,23,42,0.65); display:grid; place-items:center; z-index:50; padding:20px; }
.modal { background:#fff; color:#0f172a; border-radius:18px; max-width:460px; width:100%; padding:24px; box-shadow:0 20px 48px rgba(15,23,42,0.3); }
.modal header { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }
.modal h3 { margin:0; font-size:1.2rem; }
.modal-close { border:none; background:transparent; font-size:1.5rem; cursor:pointer; }
.modal dl { margin:0; display:grid; gap:10px; }
.modal dl div { display:flex; justify-content:space-between; gap:12px; }
.modal dt { font-weight:600; color:#475569; }
.modal dd { margin:0; font-weight:700; color:#0f172a; }
.modal a { color:#2563eb; text-decoration:none; }
.icon-link { display:inline-flex; align-items:center; justify-content:center; width:28px; height:28px; border:1px solid rgba(37,99,235,0.45); border-radius:8px; background:rgba(37,99,235,0.08); }
.icon-link .external-icon { margin-left:0; font-size:1rem; }
.sr-only { position:absolute; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden; clip:rect(0,0,0,0); white-space:nowrap; border:0; }
.modal .permission-list li { background:rgba(148,163,184,0.18); border-color:rgba(148,163,184,0.4); }
.external-icon { font-size:0.8em; margin-left:4px; }
</style>
