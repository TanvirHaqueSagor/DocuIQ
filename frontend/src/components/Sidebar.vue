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
        <button class="profile-item">{{ $t ? $t('settings') : 'Settings' }}</button>
        <button class="profile-item">{{ $t ? $t('upgradePlan') : 'Upgrade plan' }}</button>
        <button class="profile-item">{{ $t ? $t('help') : 'Help' }}</button>
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

const historyList = ref([])

const isOpen = ref(true)
const showMenu = ref(false)
const router = useRouter()
const { t } = useI18n ? useI18n() : { t: (s)=>s }

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
}

const goLogout = () => {
  showMenu.value = false
  router.push('/logout')
}

const updateBodyAttr = () => {
  if (typeof document !== 'undefined') {
    document.body.setAttribute('data-sidebar', isOpen.value ? 'open' : 'closed')
  }
}
watch(isOpen, updateBodyAttr)

const onDocClick = () => { showMenu.value = false; activeMenuFor.value = null }

onMounted(() => {
  updateBodyAttr()
  if (typeof document !== 'undefined') {
    document.addEventListener('click', onDocClick)
  }
})

onBeforeUnmount(() => {
  if (typeof document !== 'undefined') {
    document.removeEventListener('click', onDocClick)
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
  background: #f6f7fa;
  box-shadow: 2px 0 8px #dde7fa26;
  border-right: 1px solid #e6ecf7; /* thin vertical divider */
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
.brand { font-size: 1.34rem; font-weight: 700; color: #2788df; letter-spacing: -.7px; white-space: nowrap; text-decoration: none; }
.brand-main { letter-spacing: -.7px; }
.highlight { color: #2196f3; }

/* Mini brand (closed) */
.brand-mini { display: none; align-items: center; gap: 6px; cursor: pointer; }
.brand-mini-text { font-size: .98rem; font-weight: 700; color: #2788df; letter-spacing: -.3px; white-space: nowrap; text-decoration: none; }
.brand-mini-text { transition: opacity .18s ease, transform .18s ease; }
.open-hint {
  display: inline-flex; align-items: center; justify-content: center;
  width: 32px; height: 32px; border-radius: 6px; border: 1px solid #dbe3f3;
  background: #fff; cursor: pointer; opacity: 0;
  position: absolute; right: 8px; top: 50%; transform: translateY(-50%) translateX(-2px);
  pointer-events: none;
  transition: opacity .18s ease, transform .18s ease, background .12s ease;
  z-index: 2;
}
.open-hint:hover { background: #eef3ff; }

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
.sidebar-toggle:hover { background: #e2e8f0; transform: translateX(0); }
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
  font-size: 1.08rem; color: #374151; border-radius: 7px; text-decoration: none;
  padding: 9px 10px; margin: 0 2px; font-weight: 500; transition: background .14s, color .16s;
}
.menu-item.active, .menu-item.router-link-exact-active { background: #e8f0fe; color: #1976d2; }
.menu-item:hover { background: #e4eaf8; color: #2788df; }
.menu-icon { font-size: 1.18rem; display: inline-flex; width: 24px; min-width: 24px; justify-content: center; }

.menu-group-title {
  display: flex; align-items: center; gap: 11px; color: #5a5e6a;
  justify-content: flex-start;
  font-size: 0.97rem; font-weight: 500; margin: 0 2px 5px 2px; letter-spacing: .03em;
  padding: 9px 10px; border-radius: 7px;
  transition: background .14s, color .16s;
}
.menu-group-title:hover,
.menu-group-title:focus { background: #e4eaf8; color: #2788df; outline: none; }

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
  color: #50556b; font-size: 0.97rem; display: block; text-decoration: none;
  border-radius: 5px; padding: 7px 7px 7px 36px; transition: background .12s, color .15s;
}
.menu-child:hover, .menu-child.router-link-exact-active { background: #ecf3fd; color: #1976d2; }
.menu-child-empty { color: #9fa8c1; font-size: 0.95rem; padding: 7px 7px 7px 36px; }

.history-item{ position: relative; display:flex; align-items:center; border-radius: 5px; }
.history-item:hover { background:#f5f9ff; }
.history-item.active, .history-item:focus-within { background:#ecf3fd; }
.history-item.active .menu-child.router-link-exact-active { background: transparent; }
.history-item:hover .menu-child, .history-item:hover .menu-child.router-link-exact-active { background: transparent; }
.history-item.active .menu-label, .history-item:focus-within .menu-label { color:#1976d2; }
.history-item:hover .menu-label { color:#1d4ed8; }
.history-item .menu-child{ flex:1 1 auto; min-width: 0; padding-right: 36px; padding-left: 16px; }
.history-item:hover .menu-child{ padding-right: 56px; }
.history-item .menu-label{ display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
/* Ensure no pseudo ellipsis; rely on native text-overflow */
.history-item:hover .menu-label::after{ content: none; }

/* Hide the three-dot actions until hover/focus */
.item-actions{ position:absolute; right:8px; border:none; background:transparent; color:#6b7280; cursor:pointer; padding:4px 6px; border-radius:6px; opacity:0; pointer-events:none; transition: opacity .15s ease; z-index: 1; }
.history-item:hover .item-actions,
.history-item:focus-within .item-actions{ opacity:1; pointer-events:auto; }
.item-actions:hover{ background:#eef2ff; color:#374151; }
.item-menu{ position:absolute; right:6px; top:30px; background:#fff; border:1px solid #e6ecf7; border-radius:8px; box-shadow: 0 8px 24px rgba(0,0,0,.12); z-index:23; padding:4px; display:flex; flex-direction:column; min-width:160px; }
.item-menu-btn{ text-align:left; padding:8px 10px; border:none; background:#fff; border-radius:6px; font-size:.9rem; color:#2f3b52; cursor:pointer; }
.item-menu-btn:hover{ background:#eff6ff; }
.item-menu-btn.danger{ color:#d93025; }
.item-menu-btn.danger:hover{ background:#feeceb; }

.history-rename{ width: 100%; border: 1px solid #dbe3f3; background:#fff; color:#1e2a44; border-radius:6px; padding:6px 8px; font-size:.95rem; outline:none; }
.history-rename:focus{ border-color:#b7cdfa; box-shadow: 0 0 0 3px rgba(99,102,241,.15); }

.sidebar-bottom {
  margin: 10px 0 22px 0; padding: 12px 16px 0 16px; display: flex; flex-direction: column; gap: 14px; position: relative;
  border-top: 1px solid #e6ecf7;
}
.sidebar-profile {
  display: flex; align-items: center; gap: 7px; padding: 9px 8px; border-radius: 8px;
  background: #eef6fd; width: 100%; font-size: 0.97rem; font-weight: 500; color: #1976d2;
  cursor: pointer; position: relative;
}
.sidebar-avatar { font-size: 1.23rem; display: inline-flex; width: 24px; justify-content: center; }
.sidebar-username { font-size: 0.97rem; margin-left: 2px; white-space: nowrap; transition: opacity .2s ease, width .2s ease, margin .2s ease; }

.profile-menu {
  position: fixed; left: 16px; bottom: 96px; width: 260px;
  background: #fff; border: 1px solid #e6ecf7; border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,.12);
  padding: 8px; display: flex; flex-direction: column; gap: 4px;
  z-index: 22;
}
.profile-item {
  text-align: left; padding: 10px 12px; border: none; background: #fff; border-radius: 8px;
  font-size: 0.96rem; color: #2f3b52; cursor: pointer; transition: background .12s;
}
.profile-item:hover { background: #eff6ff; }
.profile-item.danger { color: #d93025; }
.profile-item.danger:hover { background: #feeceb; }

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
