import { createRouter, createWebHistory } from 'vue-router'

// Static, relative imports (no alias, no lazy)
import Dashboard from './views/Dashboard.vue'
import Documents from './views/Documents.vue'
import Home from './views/Home.vue'

import Login from './views/Login.vue'
import Register from './views/Register.vue'
import Logout from './views/Logout.vue'
import SourceSetup from './views/SourceSetup.vue'

const routes = [
  // Home = Search (public)
  { path: '/', component: Home, meta: { requiresAuth: true } },

  // Main app
  { path: '/dashboard', component: Dashboard, meta: { requiresAuth: true } },
  { path: '/documents', component: Documents, meta: { requiresAuth: true } },
  // Redirect legacy document detail route to Documents (edit handled from list)
  { path: '/documents/:id', redirect: '/documents' },

  // Chat history: reuse Home for viewing a saved chat
  { path: '/analysis/:id', component: Home, meta: { requiresAuth: true } },

  // Connect sources (per-kind setup)
  { path: '/connect/:kind', component: SourceSetup, meta: { requiresAuth: true } },


  // Auth
  { path: '/login', component: Login, meta: { hideSidebar: true, public: true } },
  { path: '/register', component: Register, meta: { hideSidebar: true, public: true } },
  { path: '/logout', component: Logout, meta: { requiresAuth: true, hideSidebar: true } },
  // Fallback
  { path: '/:pathMatch(.*)*', redirect: '/login' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Keep simple auth guard
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const publicPaths = ['/login', '/register']
  const isPublic = publicPaths.includes(to.path)
  const deriveRootDomain = (hn) => {
    if (!hn) return 'localhost'
    if (hn === 'localhost') return 'localhost'
    const parts = hn.split('.')
    if (parts.length >= 2) return parts.slice(1).join('.')
    return hn
  }
  const ROOT_DOMAIN = import.meta.env.VITE_ROOT_DOMAIN || deriveRootDomain(window.location.hostname)
  const acctType = localStorage.getItem('account_type')
  const orgSub = localStorage.getItem('org_subdomain')
  // লগআউট অবস্থায়: যেকোনো non-public রুটে গেলে login এ পাঠান
  if (!token && !isPublic) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }
  // লগইন থাকা অবস্থায়: login/register এ এলে dashboard এ পাঠান
  if (token && isPublic) {
    return next('/')
  }
  // Enforce org subdomain for protected routes
  if (token && !isPublic && acctType === 'organization' && orgSub && ROOT_DOMAIN) {
    const expectedHost = `${orgSub}.${ROOT_DOMAIN}`
    if (window.location.hostname !== expectedHost) {
      const proto = window.location.protocol
      const port  = window.location.port ? (':' + window.location.port) : ''
      const r = encodeURIComponent(to.fullPath || '/dashboard')
      window.location.href = `${proto}//${expectedHost}${port}/login?redirect=${r}`
      return
    }
  }
  next()
})

export default router
