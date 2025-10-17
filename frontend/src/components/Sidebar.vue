<template>
  <aside :class="['sidebar', { closed: !isOpen }]">
    <div class="sidebar-top">
      <div class="logo-section">
        <transition name="logo-large">
          <router-link v-if="isOpen" to="/" class="brand" :title="$t ? $t('home') : 'Home'">
            <span class="brand-main">Docu</span><span class="highlight">IQ</span>
          </router-link>
        </transition>

        <transition name="logo-mini">
          <span class="brand-mini" v-if="!isOpen">
            <router-link to="/" class="brand-mini-text" :title="$t ? $t('home') : 'Home'">Docu<span class="highlight">IQ</span></router-link>
            <button class="open-hint" aria-label="Open sidebar" @click.stop="toggleSidebar" :title="$t ? $t('openSidebar') : 'Open sidebar'">
              <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M9.5 5 L15.5 12 L9.5 19" fill="none" stroke="#4a5568" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </span>
        </transition>

        <button
          class="sidebar-toggle"
          @click="toggleSidebar"
          :title="isOpen ? ($t ? $t('closeSidebar') : 'Close sidebar') : ($t ? $t('openSidebar') : 'Open sidebar')"
          aria-label="Toggle sidebar"
        >
          <transition name="chev">
            <svg v-if="isOpen" width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M14.5 5 L8.5 12 L14.5 19" fill="none" stroke="#4a5568" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <svg v-else width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M9.5 5 L15.5 12 L9.5 19" fill="none" stroke="#4a5568" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </transition>
        </button>
      </div>

      <nav class="sidebar-menu">
        <router-link to="/" class="menu-item" active-class="active" :title="$t ? $t('newAnalysis') : 'New Analysis'">
          <span class="menu-icon" aria-hidden="true">📝</span>
          <span class="menu-label">{{ $t ? $t('newAnalysis') : 'New Analysis' }}</span>
        </router-link>

        <router-link to="/dashboard" class="menu-item" active-class="active" :title="$t ? $t('dashboard') : 'Dashboard'">
          <span class="menu-icon" aria-hidden="true">📊</span>
          <span class="menu-label">{{ $t ? $t('dashboard') : 'Dashboard' }}</span>
        </router-link>

        <router-link to="/documents" class="menu-item" active-class="active" :title="$t ? $t('documents') : 'Documents'">
          <span class="menu-icon" aria-hidden="true">🗂️</span>
          <span class="menu-label">{{ $t ? $t('documents') : 'Documents' }}</span>
        </router-link>

        

        <div class="menu-group-title" :title="$t ? $t('history') : 'History'" tabindex="0">
          <span class="menu-icon" aria-hidden="true">🕑</span>
          <span class="menu-label">{{ $t ? $t('history') : 'History' }}</span>
        </div>
        <ul class="menu-sublist">
          <li v-for="h in historyList" :key="h.id" :class="['history-item', { active: isActive(h) }]" @click="goThread(h)">
            <router-link v-if="editingId!==h.id" :to="`/analysis/${h.id}`" class="menu-child" :title="h.title || ($t ? $t('untitled') : 'Untitled')">
              <span class="menu-label">{{ h.title || ($t ? $t('untitled') : 'Untitled') }}</span>
            </router-link>
            <div v-else class="menu-child">
              <input
                class="history-rename"
                v-model="editingTitle"
                :placeholder="h.title || ($t ? $t('untitled') : 'Untitled')"
                @keydown.enter.prevent="commitRename(h)"
                @keydown.esc.prevent="cancelRename"
                @blur="commitRename(h)"
              />
            </div>
            <button class="item-actions" @click.stop="openItemMenu(h)">⋯</button>
            <div v-if="activeMenuFor===h.id" class="item-menu" @click.stop>
              <button class="item-menu-btn" @click="startRename(h)">{{ $t ? $t('rename') : 'Rename' }}</button>
              <button v-if="!h.archived" class="item-menu-btn" @click="archiveThread(h, true)">{{ $t ? $t('archive') : 'Archive' }}</button>
              <button v-else class="item-menu-btn" @click="archiveThread(h, false)">{{ $t ? $t('unarchive') : 'Unarchive' }}</button>
              <button class="item-menu-btn danger" @click="deleteThread(h)">{{ $t ? $t('delete') : 'Delete' }}</button>
            </div>
          </li>
          <li v-if="!historyList.length" class="menu-child-empty">
            <span class="menu-label">{{ $t ? $t('noHistory') : 'No history yet' }}</span>
          </li>
        </ul>

        
      </nav>
    </div>

    <div class="sidebar-bottom">
      <div class="sidebar-profile" @click="toggleMenu" :title="displayName">
        <span class="sidebar-avatar" aria-hidden="true">👤</span>
        <span class="sidebar-username">{{ displayName }}</span>
      </div>

      <div v-if="showMenu" class="profile-menu" @click.stop>
        <div v-if="planDisplayLabel" class="profile-plan">
          <span class="plan-caption">{{ t ? t('upgradePage.statusLabel') : 'Current plan' }}</span>
          <span class="plan-chip" :class="planChipClass">{{ planDisplayLabel }}</span>
        </div>
        <button class="profile-item" @click="goSettings">{{ $t ? $t('settings') : 'Settings' }}</button>
        <button class="profile-item" @click="goUpgrade">{{ $t ? $t('upgradePlan') : 'Upgrade plan' }}</button>
        <div class="profile-item help-group">
          <button class="help-trigger" @click.stop="toggleHelpMenu">
            {{ $t ? $t('helpMenu.title') : 'Get help' }}
            <svg class="help-trigger-icon" width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <transition name="fade">
            <div v-if="showHelpMenu" class="help-menu" @click.stop>
              <button v-for="opt in helpOptions" :key="opt.key" class="help-pill" @click="selectHelp(opt)">
                <span class="help-pill-icon" aria-hidden="true">{{ opt.icon }}</span>
                <span class="help-pill-label">{{ opt.title }}</span>
              </button>
              <div class="help-footer">{{ $t ? $t('helpMenu.footer') : 'We respond within one business day.' }}</div>
            </div>
          </transition>
        </div>
        <button class="profile-item" @click="toggleArchived">{{ showArchived ? ($t ? $t('hideArchived') : 'Hide archived') : ($t ? $t('showArchived') : 'Show archived') }}</button>
        <button class="profile-item danger" @click="goLogout">{{ $t ? $t('logout') : 'Logout' }}</button>
      </div>
    </div>

    <div class="scrim" v-if="isOpen && isMobile" @click="toggleSidebar"></div>
  </aside>
</template>

<script setup>
import { ref, onMounted, watch, computed, onBeforeUnmount, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { API_BASE_URL } from '../config'
import { authFetch } from '../lib/authFetch'
import { loadCachedPlan, fetchSubscriptionPlan } from '../services/subscription'

const historyList = ref([])

const isOpen = ref(true)
const showMenu = ref(false)
const router = useRouter()
const { t } = useI18n ? useI18n() : { t: (s)=>s }

const planCode = ref('')
const planLabel = ref('')

const planChipClass = computed(() => {
  if (planCode.value === 'pro') return 'plan-chip-blue'
  if (planCode.value === 'enterprise') return 'plan-chip-gold'
  return 'plan-chip-green'
})

const planDisplayLabel = computed(() => {
  if (!planCode.value) return planLabel.value || ''
  const translated = t ? t(`upgradePage.plans.${planCode.value}.name`, planLabel.value || planCode.value) : planLabel.value
  return translated || planLabel.value || ''
})

const showHelpMenu = ref(false)
const helpOptions = computed(() => {
  const base = [
    { key: 'helpCenter', icon: '📚', to: '/help-center' },
    { key: 'releaseNotes', icon: '🗒️', to: '/release-notes' },
    { key: 'termsPolicies', icon: '📜', to: '/terms-policies' },
    { key: 'bugReport', icon: '🐞', to: '/bug-report' },
  ]
  return base.map(opt => ({
    ...opt,
    title: t ? t(`helpMenu.options.${opt.key}.title`) : opt.key,
    desc: t ? t(`helpMenu.options.${opt.key}.desc`) : '',
  }))
})

function applyPlan(data){
  if (!data) return
  planCode.value = data.code || ''
  const translated = data.code ? (t ? t(`upgradePage.plans.${data.code}.name`, data.label || data.code) : '') : ''
  planLabel.value = translated || data.label || data.code || ''
}

async function refreshPlan(){
  try {
    const data = await fetchSubscriptionPlan()
    applyPlan(data)
  } catch (_) {
    /* ignore network errors */
  }
}

function onStorage(event){
  if (!event || event.key !== 'subscription_plan') return
  try {
    const parsed = event.newValue ? JSON.parse(event.newValue) : null
    applyPlan(parsed)
  } catch (_) {}
}

function onPlanChanged(event){
  if (!event || !event.detail) return
  applyPlan(event.detail)
}

function toggleHelpMenu(){
  showHelpMenu.value = !showHelpMenu.value
}

function selectHelp(opt){
  if (!opt || !opt.to) return
  showHelpMenu.value = false
  showMenu.value = false
  try {
    router.push(opt.to)
  } catch (_) {}
}

const isMobile = computed(() => {
  if (typeof window === 'undefined' || !window.matchMedia) return false
  return window.matchMedia('(max-width: 700px)').matches
})

const toggleSidebar = () => {
  isOpen.value = !isOpen.value
  showMenu.value = false
}

const toggleMenu = (e) => {
  e.stopPropagation()
  showMenu.value = !showMenu.value
  if (!showMenu.value) showHelpMenu.value = false
}

const goLogout = () => {
  showMenu.value = false
  showHelpMenu.value = false
  router.push('/logout')
}

const goSettings = () => {
  showMenu.value = false
  showHelpMenu.value = false
  router.push('/settings')
}

const goUpgrade = () => {
  showMenu.value = false
  showHelpMenu.value = false
  router.push('/upgrade')
}

const updateBodyAttr = () => {
  if (typeof document !== 'undefined') {
    document.body.setAttribute('data-sidebar', isOpen.value ? 'open' : 'closed')
  }
}
watch(isOpen, updateBodyAttr)

const onDocClick = () => {
  showMenu.value = false
  showHelpMenu.value = false
  activeMenuFor.value = null
}

onMounted(() => {
  updateBodyAttr()
  if (typeof document !== 'undefined') {
    document.addEventListener('click', onDocClick)
  }
  const cachedPlan = loadCachedPlan()
  if (cachedPlan) applyPlan(cachedPlan)
  refreshPlan()
  if (typeof window !== 'undefined') {
    window.addEventListener('storage', onStorage)
    window.addEventListener('docuiq-plan-changed', onPlanChanged)
  }
})

onBeforeUnmount(() => {
  if (typeof document !== 'undefined') {
    document.removeEventListener('click', onDocClick)
  }
  if (typeof window !== 'undefined') {
    window.removeEventListener('storage', onStorage)
    window.removeEventListener('docuiq-plan-changed', onPlanChanged)
  }
})

/* ---------- Chat history ---------- */
const route = useRoute()
const showArchived = ref(false)
const activeMenuFor = ref(null)
const editingId = ref(null)
const editingTitle = ref('')
let renaming = false

async function fetchHistory(){
  try{
    // Always fetch active (non-archived)
    const r1 = await authFetch(`${API_BASE_URL}/api/chats/threads/?archived=0`)
    const a = r1.ok ? await r1.json() : []
    if (!showArchived.value) { historyList.value = a; return }
    // Optionally include archived and merge
    const r2 = await authFetch(`${API_BASE_URL}/api/chats/threads/?archived=1`)
    const b = r2.ok ? await r2.json() : []
    const byId = new Map()
    for (const x of [...a, ...b]) byId.set(x.id, x)
    historyList.value = Array.from(byId.values())
  }catch(_){ /* ignore */ }
}
onMounted(fetchHistory)
watch(() => route.fullPath, () => { fetchHistory() })

function toggleArchived(){
  showArchived.value = !showArchived.value
  fetchHistory()
  showMenu.value = false
}
function openItemMenu(h){
  activeMenuFor.value = (activeMenuFor.value === h.id) ? null : h.id
}
function isActive(h){
  try { return String(route.params?.id || '') === String(h.id) } catch { return false }
}
function goThread(h){
  try{ router.push(`/analysis/${h.id}`) }catch(_){ }
}
function startRename(h){
  activeMenuFor.value = null
  editingId.value = h.id
  editingTitle.value = h.title || ''
  nextTick(() => { try { document.querySelector('.history-rename')?.focus() } catch(_) {} })
}
async function commitRename(h){
  if (renaming) return
  if (!editingId.value) return cancelRename()
  const newTitle = (editingTitle.value || '').trim()
  if ((h.title || '') === newTitle) return cancelRename()
  renaming = true
  try{
    const r = await authFetch(`${API_BASE_URL}/api/chats/threads/${h.id}/`, {
      method:'PATCH', headers:{ 'Content-Type':'application/json' }, body: JSON.stringify({ title: newTitle || 'Untitled' })
    })
    if (r.ok) await fetchHistory()
  }catch(_){ /* ignore */ }
  finally{
    renaming = false
    cancelRename()
  }
}
function cancelRename(){ editingId.value = null; editingTitle.value = '' }
async function archiveThread(h, val){
  activeMenuFor.value = null
  try{
    const r = await authFetch(`${API_BASE_URL}/api/chats/threads/${h.id}/`, {
      method:'PATCH', headers:{ 'Content-Type':'application/json' }, body: JSON.stringify({ archived: !!val })
    })
    if (r.ok) fetchHistory()
  }catch(_){ /* ignore */ }
}
async function deleteThread(h){
  activeMenuFor.value = null
  const msg = (typeof t === 'function') ? t('confirmDeleteChat') : 'Delete this chat? This cannot be undone.'
  if (!confirm(msg)) return
  try{
    const r = await authFetch(`${API_BASE_URL}/api/chats/threads/${h.id}/`, { method:'DELETE' })
    if (r.ok) fetchHistory()
  }catch(_){ /* ignore */ }
}

/* ---------- Name display logic ---------- */
const me = ref(null)
const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

const displayName = computed(() => {
  const m = me.value
  if (m) {
    if (m.name && m.name.trim()) return m.name.trim()
    const fl = [m.first_name, m.last_name].filter(Boolean).join(' ').trim()
    if (fl) return fl
    if (m.email) return String(m.email).split('@')[0]
    if (m.username) return m.username
  }
  if (user.value) {
    const fl2 = [user.value.first_name, user.value.last_name].filter(Boolean).join(' ').trim()
    if (fl2) return fl2
    if (user.value.email) return String(user.value.email).split('@')[0]
    if (user.value.username) return user.value.username
  }
  return 'User'
})

onMounted(async () => {
  try {
    const access = localStorage.getItem('token') || localStorage.getItem('access')
    if (!access || access.indexOf('.') === -1) return
    const res = await fetch(`${API_BASE_URL}/api/accounts/me/`, {
      headers: { Authorization: `Bearer ${access}` }
    })
    if (res.ok) {
      me.value = await res.json()
    }
  } catch (_) {}
})
</script>

<style scoped>
:root {
  --sb-open: 260px;
  --sb-rail: 56px;
}

.sidebar {
  position: fixed;
  top: 0; left: 0; bottom: 0;
  width: var(--sb-open);
  background: var(--card);
  box-shadow: 2px 0 8px #00000012;
  border-right: 1px solid var(--line); /* thin vertical divider */
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: width .28s cubic-bezier(.4,0,.2,1);
  z-index: 21;
}
.sidebar.closed { width: var(--sb-rail); }

.sidebar-top { padding: 16px 0 0 0; display:flex; flex-direction:column; flex:1; min-height:0; overflow:hidden; }
.logo-section {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 18px 14px 18px; min-height: 56px; position: relative;
}

/* Brand (open) */
.brand { font-size: 1.34rem; font-weight: 700; color: var(--blue); letter-spacing: -.7px; white-space: nowrap; text-decoration: none; }
.brand-main { letter-spacing: -.7px; }
.highlight { color: #2196f3; }

/* Mini brand (closed) */
.brand-mini { display: none; align-items: center; gap: 6px; cursor: pointer; }
.brand-mini-text { font-size: .98rem; font-weight: 700; color: var(--blue); letter-spacing: -.3px; white-space: nowrap; text-decoration: none; }
.brand-mini-text { transition: opacity .18s ease, transform .18s ease; }
.open-hint {
  display: inline-flex; align-items: center; justify-content: center;
  width: 32px; height: 32px; border-radius: 6px; border: 1px solid var(--line);
  background: var(--card); cursor: pointer; opacity: 0;
  position: absolute; right: 8px; top: 50%; transform: translateY(-50%) translateX(-2px);
  pointer-events: none;
  transition: opacity .18s ease, transform .18s ease, background .12s ease;
  z-index: 2;
}
.open-hint:hover { background: rgba(148,163,184,.15); }

/* Show mini brand only when closed */
.sidebar.closed .brand { display: none; }
.sidebar.closed .brand-mini { display: inline-flex; }
/* Reveal the chevron only on hover of the logo row */
.sidebar.closed .logo-section:hover .open-hint,
.sidebar.closed .brand-mini:hover .open-hint,
.sidebar.closed:hover .open-hint { opacity: 1; transform: translateY(-50%) translateX(0); pointer-events: auto; }

/* On hover in collapsed mode, fade out the small DocuIQ label and show only the expand chevron */
.sidebar.closed .brand-mini { position: relative; }
.sidebar.closed .logo-section:hover .brand-mini-text,
.sidebar.closed .brand-mini:hover .brand-mini-text { opacity: 0; pointer-events: none; transform: scale(.98); }

.sidebar-toggle { background: transparent; border: none; cursor: pointer; margin-left: 5px; padding: 4px; outline: none; border-radius: 7px; transition: background .13s, transform .24s ease; width: 32px; height: 32px; display:inline-flex; align-items:center; justify-content:center; }
.sidebar-toggle:hover { background: rgba(148,163,184,.2); transform: translateX(0); }
/* Keep toggle visible in rail mode (consistent chevron size) */
.sidebar.closed .sidebar-toggle { display: none; }
.sidebar.closed .logo-section { padding: 0 8px 8px 8px; flex-direction: row; align-items: center; gap: 6px; }
.sidebar.closed .brand-mini { display: inline-flex; align-items: center; justify-content: center; }
.sidebar.closed .open-hint { display: inline-flex; }
.sidebar.closed .brand-mini-text { font-size: .78rem; letter-spacing: -.2px; line-height: 1.1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.sidebar-menu { display: flex; flex-direction: column; gap: 5px; padding: 0 6px; flex:1; padding-right: 0; min-height: 0; overflow-x: hidden; }
.menu-item {
  display: flex; align-items: center; gap: 11px;
  justify-content: flex-start;
  font-size: 1.08rem; color: var(--txt); border-radius: 7px; text-decoration: none;
  padding: 9px 10px; margin: 0 2px; font-weight: 500; transition: background .14s, color .16s;
}
.menu-item.active, .menu-item.router-link-exact-active { background: rgba(96,165,250,.15); color: var(--blue); }
.menu-item:hover { background: rgba(148,163,184,.15); color: var(--blue); }
.menu-icon { font-size: 1.18rem; display: inline-flex; width: 24px; min-width: 24px; justify-content: center; }

.menu-group-title {
  display: flex; align-items: center; gap: 11px; color: var(--muted);
  justify-content: flex-start;
  font-size: 0.97rem; font-weight: 500; margin: 0 2px 5px 2px; letter-spacing: .03em;
  padding: 9px 10px; border-radius: 7px;
  transition: background .14s, color .16s;
}
.menu-group-title:hover,
.menu-group-title:focus { background: rgba(148,163,184,.15); color: var(--blue); outline: none; }

.menu-sublist { list-style: none; margin: 0; padding: 0 6px 0 0; flex: 1; min-height: 0; overflow-y: auto; overflow-x: hidden; scrollbar-gutter: stable both-edges; }
/* Thin, subtle scrollbar for history list */
.menu-sublist{ scrollbar-width: thin; scrollbar-color: #b7c5de transparent; }
.menu-sublist::-webkit-scrollbar{ width: 6px; height: 6px; }
.menu-sublist::-webkit-scrollbar-track{ background: transparent; }
.menu-sublist::-webkit-scrollbar-thumb{ background-color: #cbd5e1; border-radius: 8px; border: 2px solid transparent; background-clip: padding-box; }
/* On hover, make scrollbar stand out a bit (focus) */
.menu-sublist:hover{ scrollbar-color: #94a3b8 transparent; }
.menu-sublist:hover::-webkit-scrollbar{ width: 8px; }
.menu-sublist:hover::-webkit-scrollbar-thumb{ background-color: #94a3b8; }
.menu-child {
  color: var(--txt); font-size: 0.97rem; display: block; text-decoration: none;
  border-radius: 5px; padding: 7px 7px 7px 36px; transition: background .12s, color .15s;
}
.menu-child:hover, .menu-child.router-link-exact-active { background: rgba(96,165,250,.12); color: var(--blue); }
.menu-child-empty { color: var(--muted); font-size: 0.95rem; padding: 7px 7px 7px 36px; }

.history-item{ position: relative; display:flex; align-items:center; border-radius: 5px; }
.history-item:hover { background: rgba(148,163,184,.12); }
.history-item.active, .history-item:focus-within { background: rgba(96,165,250,.12); }
.history-item.active .menu-child.router-link-exact-active { background: transparent; }
.history-item:hover .menu-child, .history-item:hover .menu-child.router-link-exact-active { background: transparent; }
.history-item.active .menu-label, .history-item:focus-within .menu-label { color: var(--blue); }
.history-item:hover .menu-label { color: var(--blue); }
.history-item .menu-child{ flex:1 1 auto; min-width: 0; padding-right: 36px; padding-left: 16px; }
.history-item:hover .menu-child{ padding-right: 56px; }
.history-item .menu-label{ display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
/* Ensure no pseudo ellipsis; rely on native text-overflow */
.history-item:hover .menu-label::after{ content: none; }

/* Hide the three-dot actions until hover/focus */
.item-actions{ position:absolute; right:8px; border:none; background:transparent; color: var(--muted); cursor:pointer; padding:4px 6px; border-radius:6px; opacity:0; pointer-events:none; transition: opacity .15s ease; z-index: 1; }
.history-item:hover .item-actions,
.history-item:focus-within .item-actions{ opacity:1; pointer-events:auto; }
.item-actions:hover{ background: rgba(148,163,184,.18); color: var(--txt); }
.item-menu{ position:absolute; right:6px; top:30px; background: var(--card); border:1px solid var(--line); border-radius:8px; box-shadow: 0 8px 24px rgba(0,0,0,.25); z-index:23; padding:4px; display:flex; flex-direction:column; min-width:160px; }
.item-menu-btn{ text-align:left; padding:8px 10px; border:none; background: var(--card); border-radius:6px; font-size:.9rem; color: var(--txt); cursor:pointer; }
.item-menu-btn:hover{ background: rgba(148,163,184,.15); }
.item-menu-btn.danger{ color:#d93025; }
.item-menu-btn.danger:hover{ background: rgba(220,38,38,.15); }

.history-rename{ width: 100%; border: 1px solid var(--line); background: var(--card); color: var(--txt); border-radius:6px; padding:6px 8px; font-size:.95rem; outline:none; }
.history-rename:focus{ border-color:#b7cdfa; box-shadow: 0 0 0 3px rgba(99,102,241,.15); }

.sidebar-bottom {
  margin: 10px 0 22px 0; padding: 12px 16px 0 16px; display: flex; flex-direction: column; gap: 14px; position: relative;
  border-top: 1px solid var(--line);
}
.sidebar-profile {
  display: flex; align-items: center; gap: 7px; padding: 9px 8px; border-radius: 8px;
  background: var(--bg); width: 100%; font-size: 0.97rem; font-weight: 500; color: var(--blue);
  cursor: pointer; position: relative;
}
.sidebar-avatar { font-size: 1.23rem; display: inline-flex; width: 24px; justify-content: center; }
.sidebar-username { font-size: 0.97rem; margin-left: 2px; white-space: nowrap; transition: opacity .2s ease, width .2s ease, margin .2s ease; color: var(--txt); }

.profile-menu {
  position: fixed; left: 16px; bottom: 96px; width: 260px;
  background: var(--card); border: 1px solid var(--line); border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,.12);
  padding: 8px; display: flex; flex-direction: column; gap: 4px;
  z-index: 22;
}
.profile-plan {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 6px 8px 10px;
  border-bottom: 1px solid rgba(148,163,184,.35);
  margin-bottom: 6px;
}
.plan-caption {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(71,85,105,.9);
}
.plan-chip {
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  padding: 6px 10px;
  border-radius: 999px;
  font-weight: 700;
  font-size: 0.82rem;
  color: #0f172a;
  background: rgba(71,85,105,.12);
  width: fit-content;
}
.plan-chip-green { background: rgba(22,163,74,.16); color: #166534; }
.plan-chip-blue { background: rgba(37,99,235,.16); color: #1d4ed8; }
.plan-chip-gold { background: rgba(217,119,6,.18); color: #b45309; }
.profile-item {
  text-align: left; padding: 10px 12px; border: none; background: var(--card); border-radius: 8px;
  font-size: 0.96rem; color: var(--txt); cursor: pointer; transition: background .12s;
}
.profile-item:hover { background: rgba(148,163,184,.15); }
.profile-item.danger { color: #d93025; }
.profile-item.danger:hover { background: rgba(220,38,38,.15); }
.profile-item.help-group { position: relative; padding: 0; }
.help-trigger {
  width: 100%; display: flex; align-items: center; justify-content: space-between;
  gap: 8px; padding: 10px 12px; background: transparent; border: none; cursor: pointer;
  color: var(--txt); font-size: 0.96rem; border-radius: 8px;
}
.help-trigger:hover { background: rgba(148,163,184,.15); }
.help-trigger svg { color: inherit; }
.help-menu {
  position: absolute; left: calc(100% + 8px); top: 0; min-width: 220px;
  background: var(--card); border: 1px solid var(--line); border-radius: 16px;
  box-shadow: 0 12px 32px rgba(15,23,42,0.16); padding: 6px; display: flex; flex-direction: column;
  z-index: 40;
}
.help-pill {
  display: flex; align-items: center; gap: 8px; width: 100%; padding: 6px 10px;
  border: none; border-radius: 8px; background: transparent; color: var(--txt); cursor: pointer;
  font-size: 0.93rem; font-weight: 600; transition: background .16s ease;
}
.help-pill:hover { background: rgba(148,163,184,.18); }
.help-pill-icon { font-size: 17px; }
.help-footer { font-size: 0.75rem; color: var(--muted); text-align: center; padding-top: 6px; border-top: 1px solid rgba(148,163,184,.2); }
.fade-enter-active,.fade-leave-active{ transition: opacity .18s ease; }
.fade-enter-from,.fade-leave-to{ opacity: 0; }

.sidebar.closed .menu-label { display: none; }
.sidebar.closed .sidebar-username { width: 0; opacity: 0; margin: 0; }
.sidebar.closed .profile-menu { left: calc(var(--sb-rail) + 8px); width: 260px; bottom: 96px; }

.scrim { position: fixed; inset: 0; background: rgba(0,0,0,.25); z-index: 20; pointer-events: none; }

@media (max-width: 700px) {
  .sidebar { width: min(88vw, var(--sb-open)); }
  .sidebar.closed { width: var(--sb-rail); }
}

/* --- Smooth transitions --- */
.logo-large-enter-active, .logo-large-leave-active,
.logo-mini-enter-active, .logo-mini-leave-active { transition: opacity .18s ease, transform .18s ease; }
.logo-large-enter-from, .logo-large-leave-to { opacity: 0; transform: translateY(-4px) scale(.98); }
.logo-mini-enter-from, .logo-mini-leave-to { opacity: 0; transform: translateY(4px) scale(.9); }

.chev-enter-active, .chev-leave-active { transition: opacity .16s ease, transform .16s ease; }
.chev-enter-from, .chev-leave-to { opacity: 0; transform: scale(.8); }
</style>
