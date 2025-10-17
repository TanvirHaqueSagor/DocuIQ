<template>
  <div class="page settings">
    <header class="head">
      <h1>{{ t('settingsTitle') }}</h1>
    </header>

    <section class="card">
      <h2>{{ t('settingsBasic') }}</h2>
      <div class="row">
        <label>{{ t('settingsTheme') }}</label>
        <select v-model="theme" @change="applyTheme">
          <option value="light">{{ t('settingsThemeLight') }}</option>
          <option value="dark">{{ t('settingsThemeDark') }}</option>
          <option value="system">{{ t('settingsThemeSystem') }}</option>
        </select>
      </div>
      <div class="row">
        <label>{{ t('settingsLanguage') }}</label>
        <select v-model="lang" @change="applyLang">
          <option v-for="l in locales" :key="l.code" :value="l.code">{{ l.label }}</option>
        </select>
      </div>
    </section>

    <section class="card danger">
      <h2>{{ t('settingsDanger') }}</h2>
      <p class="warn">{{ t('settingsDangerHint') }}</p>
      <div class="actions">
        <button class="btn" :disabled="busy" @click="clearVectors">{{ t('settingsClearVectors') }}</button>
        <button class="btn" :disabled="busy" @click="deleteDocs">{{ t('settingsDeleteDocs') }}</button>
        <button class="btn danger" :disabled="busy" @click="deleteAll">{{ t('settingsDeleteAll') }}</button>
      </div>
      <div class="status" v-if="msg">{{ msg }}</div>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { API_BASE_URL } from '../config'
import { authFetch } from '../lib/authFetch'

const i18n = useI18n ? useI18n() : null
const t = i18n ? i18n.t : ((key, params = {}) => {
  return key.replace(/\{(\w+)\}/g, (_, k) => (params && params[k] !== undefined ? params[k] : `{${k}}`))
})
const locale = i18n ? i18n.locale : { value: 'en' }
const theme = ref(localStorage.getItem('theme') || 'system')
const lang = ref(localStorage.getItem('locale') || (locale && locale.value) || 'en')
const locales = [
  { code:'en', label:'English' },
  { code:'ja', label:'日本語 (Japanese)' },
  { code:'zh', label:'中文 (Chinese)' },
  { code:'ko', label:'한국어 (Korean)' },
  { code:'es', label:'Español (Spanish)' },
  { code:'hi', label:'हिन्दी (Hindi)' },
  { code:'bn', label:'বাংলা (Bangla)' },
]
const busy = ref(false)
const msg = ref('')

function applyTheme(){
  localStorage.setItem('theme', theme.value)
  const el = document.documentElement
  if (theme.value === 'system'){
    const prefersDark = typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
    if (prefersDark) el.setAttribute('data-theme', 'dark')
    else el.setAttribute('data-theme', 'light')
  } else {
    el.setAttribute('data-theme', theme.value)
  }
}
function applyLang(){
  try { if (locale) locale.value = lang.value } catch(_) {}
  localStorage.setItem('locale', lang.value)
  localStorage.setItem('lang', lang.value) // backward-compatible
}

async function callCleanup(action){
  busy.value = true; msg.value = ''
  try{
    const actionLabel = {
      clear_vectors: t('settingsClearVectors'),
      delete_documents: t('settingsDeleteDocs'),
      delete_all: t('settingsDeleteAll'),
    }[action] || action
    if (!confirm(t('settingsConfirm', { action: actionLabel }))) { busy.value=false; return }
    const r = await authFetch(`${API_BASE_URL}/api/admin/cleanup/`, { method:'POST', headers:{ 'Content-Type':'application/json' }, body: JSON.stringify({ action }) })
    const d = await r.json().catch(()=>({}))
    if (!r.ok) throw new Error(d?.detail || t('settingsOperationFailed'))
    // Build friendly message
    const parts = []
    if (action === 'clear_vectors' || action === 'delete_all'){
      const vr = (typeof d.vectors_removed === 'number') ? d.vectors_removed : (d.cleared_vectors ? 'all' : 0)
      parts.push(t('settingsSummaryClearedVectors', { count: vr })) 
    }
    if (action === 'delete_documents' || action === 'delete_all'){
      parts.push(t('settingsSummaryDeletedDocs', { count: d.deleted_docs || 0 })) 
      parts.push(t('settingsSummaryDeletedJobs', { count: d.deleted_jobs || 0 })) 
      if (typeof d.deleted_sources === 'number') parts.push(t('settingsSummaryDeletedSources', { count: d.deleted_sources })) 
    }
    const human = parts.length ? parts.join(', ') : t('settingsDoneFallback')
    msg.value = t('settingsDone', { summary: human })
  } catch(e){ msg.value = t('settingsError', { error: e?.message || e }) }
  finally{ busy.value = false }
}

const clearVectors = () => callCleanup('clear_vectors')
const deleteDocs = () => callCleanup('delete_documents')
const deleteAll = () => callCleanup('delete_all')
</script>

<style scoped>
.settings{ width:min(900px,94%); margin:18px auto; display:grid; gap:12px; }
.head h1{ margin:0; font-size:22px; color:var(--txt); }
.card{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:12px; display:grid; gap:10px; }
.card.danger{ border-color:#f3d1d1; }
.row{ display:grid; gap:6px; }
label{ color:var(--txt); font-weight:700; }
select{ border:1px solid var(--line); border-radius:8px; padding:9px 12px; background:var(--card); color:var(--txt); max-width:200px; }
.warn{ color:#92400e; background:#fff7ed; border:1px solid #fed7aa; padding:8px 10px; border-radius:8px; }
.actions{ display:flex; gap:8px; }
.btn{ border:1px solid var(--line); background:var(--card); color:var(--blue); font-weight:700; border-radius:8px; padding:8px 10px; cursor:pointer; }
.btn.danger{ border-color:#fecaca; color:#b91c1c; }
.status{ color:var(--txt); font-size:13px; }
</style>
