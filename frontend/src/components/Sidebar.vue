<template>
  <aside :class="['sidebar', { closed: !isOpen }]">
    <div class="sidebar-top">
      <div class="logo-section">
        <!-- Full logo (open state) -->
        <span class="brand" v-show="isOpen">
          <span class="brand-main">Docu</span><span class="highlight">IQ</span>
        </span>

        <!-- Mini logo (closed state) with hover chevron to open -->
        <span class="brand-mini" v-show="!isOpen" @click="toggleSidebar" :title="$t('openSidebar')">
          <span class="brand-mini-text">Docu<span class="highlight">IQ</span></span>
          <button class="open-hint" aria-label="Open sidebar" @click.stop="toggleSidebar">
            <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M9.5 5 L15.5 12 L9.5 19" fill="none" stroke="#4a5568" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </span>

        <!-- Close/Open buttons (ChatGPT-style chevrons) -->
        <button
          class="sidebar-toggle"
          @click="toggleSidebar"
          :title="isOpen ? $t('closeSidebar') : $t('openSidebar')"
          aria-label="Toggle sidebar"
        >
          <svg v-if="isOpen" width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
            <!-- chevron-left to close -->
            <path d="M14.5 5 L8.5 12 L14.5 19" fill="none" stroke="#4a5568" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <svg v-else width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
            <!-- chevron-right to open (kept for accessibility, hidden via CSS when closed) -->
            <path d="M9.5 5 L15.5 12 L9.5 19" fill="none" stroke="#4a5568" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>

      <nav class="sidebar-menu">
        <router-link
          to="/new-analysis"
          class="menu-item"
          active-class="active"
          :title="$t('newAnalysis')"
        >
          <span class="menu-icon" aria-hidden="true">📝</span>
          <span class="menu-label">{{ $t('newAnalysis') }}</span>
        </router-link>

        <div class="menu-group-title" :title="$t('history')" tabindex="0">
          <span class="menu-icon" aria-hidden="true">🕑</span>
          <span class="menu-label">{{ $t('history') }}</span>
        </div>
        <ul class="menu-sublist">
          <li v-for="h in historyList" :key="h.id">
            <router-link
              :to="`/analysis/${h.id}`"
              class="menu-child"
              :title="h.title"
            >
              <span class="menu-label">{{ h.title }}</span>
            </router-link>
          </li>
          <li v-if="!historyList.length" class="menu-child-empty">
            <span class="menu-label">{{ $t('noHistory') }}</span>
          </li>
        </ul>
      </nav>
    </div>

    <div class="sidebar-bottom">
      <div class="sidebar-profile" @click="toggleMenu" :title="username">
        <span class="sidebar-avatar" aria-hidden="true">👤</span>
        <span class="sidebar-username">{{ username }}</span>
      </div>

      <div v-if="showMenu" class="profile-menu" @click.stop>
        <button class="profile-item">{{ $t('settings') }}</button>
        <button class="profile-item">{{ $t('upgradePlan') }}</button>
        <button class="profile-item">{{ $t('help') }}</button>
        <button class="profile-item danger">{{ $t('logout') }}</button>
      </div>
    </div>

    <div class="scrim" v-if="isOpen && isMobile" @click="toggleSidebar"></div>
  </aside>
</template>

<script setup>
import { ref, onMounted, watch, computed, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'

const username = 'tanvir.haque'
const historyList = ref([
  { id: 1, title: 'Annual Report Summary' },
  { id: 2, title: 'ESG Risk Analysis' },
])

const isOpen = ref(true)
const showMenu = ref(false)
const { t } = useI18n()

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

const updateBodyAttr = () => {
  document.body.setAttribute('data-sidebar', isOpen.value ? 'open' : 'closed')
}
watch(isOpen, updateBodyAttr)

const onDocClick = () => { showMenu.value = false }

onMounted(() => {
  updateBodyAttr()
  document.addEventListener('click', onDocClick)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', onDocClick)
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
.brand { font-size: 1.34rem; font-weight: 700; color: #2788df; letter-spacing: -.7px; white-space: nowrap; }
.brand-main { letter-spacing: -.7px; }
.highlight { color: #2196f3; }

/* Mini brand (closed) */
.brand-mini { display: none; align-items: center; gap: 6px; cursor: pointer; }
.brand-mini-text { font-size: .98rem; font-weight: 700; color: #2788df; letter-spacing: -.3px; white-space: nowrap; }
.open-hint { 
  display: inline-flex; align-items: center; justify-content: center;
  width: 22px; height: 22px; border-radius: 6px; border: 1px solid #dbe3f3;
  background: #fff; cursor: pointer; opacity: 0; transform: translateX(-2px);
  transition: opacity .18s ease, transform .18s ease, background .12s ease;
}
.open-hint:hover { background: #eef3ff; }

/* Show mini brand only when closed */
.sidebar.closed .brand { display: none; }
.sidebar.closed .brand-mini { display: inline-flex; }
/* Reveal the chevron only on hover of the logo row */
.sidebar.closed .logo-section:hover .open-hint { opacity: 1; transform: translateX(0); }

.sidebar-toggle { background: transparent; border: none; cursor: pointer; margin-left: 5px; padding: 4px; outline: none; border-radius: 7px; transition: background .13s, transform .24s ease; }
.sidebar-toggle:hover { background: #e2e8f0; transform: translateX(0); }
/* Hide the generic toggle button in closed mode to encourage using mini logo hover */
.sidebar.closed .sidebar-toggle { display: none; }

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
  position: absolute; left: 16px; right: 16px; bottom: 60px;
  background: #fff; border: 1px solid #e6ecf7; border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,.06);
  padding: 8px; display: flex; flex-direction: column; gap: 4px;
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
.sidebar.closed .profile-menu { left: 8px; right: 8px; }

.scrim { position: fixed; inset: 0; background: rgba(0,0,0,.25); z-index: 20; }

@media (max-width: 700px) {
  .sidebar { width: min(88vw, var(--sb-open)); }
  .sidebar.closed { width: var(--sb-rail); }
}
</style>
