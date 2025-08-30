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
          <li v-for="h in historyList" :key="h.id">
            <router-link :to="`/analysis/${h.id}`" class="menu-child" :title="h.title">
              <span class="menu-label">{{ h.title }}</span>
            </router-link>
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
        <button class="profile-item danger" @click="goLogout">{{ $t ? $t('logout') : 'Logout' }}</button>
      </div>
    </div>

    <div class="scrim" v-if="isOpen && isMobile" @click="toggleSidebar"></div>
  </aside>
</template>

<script setup>
import { ref, onMounted, watch, computed, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { API_BASE_URL } from '../config'

const historyList = ref([
  { id: 1, title: 'Annual Report Summary' },
  { id: 2, title: 'ESG Risk Analysis' },
])

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

const onDocClick = () => { showMenu.value = false }

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
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: width .28s cubic-bezier(.4,0,.2,1);
  z-index: 21;
}
.sidebar.closed { width: var(--sb-rail); }

.sidebar-top { padding: 16px 0 0 0; }
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
.open-hint { 
  display: inline-flex; align-items: center; justify-content: center;
  width: 22px; height: 22px; border-radius: 6px; border: 1px solid #dbe3f3;
  background: #fff; cursor: pointer; opacity: 0; transform: translateX(-2px);
  pointer-events: none;
  transition: opacity .18s ease, transform .18s ease, background .12s ease;
}
.open-hint:hover { background: #eef3ff; }

/* Show mini brand only when closed */
.sidebar.closed .brand { display: none; }
.sidebar.closed .brand-mini { display: inline-flex; }
/* Reveal the chevron only on hover of the logo row */
.sidebar.closed .logo-section:hover .open-hint { opacity: 1; transform: translateX(0); pointer-events: auto; }

.sidebar-toggle { background: transparent; border: none; cursor: pointer; margin-left: 5px; padding: 4px; outline: none; border-radius: 7px; transition: background .13s, transform .24s ease; width: 32px; height: 32px; display:inline-flex; align-items:center; justify-content:center; }
.sidebar-toggle:hover { background: #e2e8f0; transform: translateX(0); }
/* Keep toggle visible in rail mode (consistent chevron size) */
.sidebar.closed .sidebar-toggle { display: none; }
.sidebar.closed .logo-section { padding: 0 8px 8px 8px; flex-direction: row; align-items: center; gap: 6px; }
.sidebar.closed .brand-mini { display: inline-flex; align-items: center; justify-content: center; }
.sidebar.closed .open-hint { display: inline-flex; }
.sidebar.closed .brand-mini-text { font-size: .78rem; letter-spacing: -.2px; line-height: 1.1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.sidebar-menu { display: flex; flex-direction: column; gap: 5px; padding: 0 6px; }
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

.menu-sublist { list-style: none; margin: 0; padding: 0; }
.menu-child {
  color: #50556b; font-size: 0.97rem; display: block; text-decoration: none;
  border-radius: 5px; padding: 7px 7px 7px 36px; transition: background .12s, color .15s;
}
.menu-child:hover, .menu-child.router-link-exact-active { background: #ecf3fd; color: #1976d2; }
.menu-child-empty { color: #9fa8c1; font-size: 0.95rem; padding: 7px 7px 7px 36px; }

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
.sidebar.closed .menu-sublist { display: none; }
.sidebar.closed .sidebar-username { width: 0; opacity: 0; margin: 0; }
.sidebar.closed .profile-menu { left: calc(var(--sb-rail) + 8px); width: 260px; bottom: 96px; }

.scrim { position: fixed; inset: 0; background: rgba(0,0,0,.25); z-index: 20; }

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
