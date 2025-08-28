import { createRouter, createWebHistory } from 'vue-router'

// Static, relative imports (no alias, no lazy)
import Dashboard from './views/Dashboard.vue'
import Documents from './views/Documents.vue'
import DocumentDetail from './views/DocumentDetail.vue'
import Home from './views/Home.vue'

import Login from './views/Login.vue'
import Register from './views/Register.vue'
import Logout from './views/Logout.vue'

const routes = [
  // Home = Search (public)
  { path: '/', component: Home, meta: { requiresAuth: true } },

  // Main app
  { path: '/dashboard', component: Dashboard, meta: { requiresAuth: true } },
  { path: '/documents', component: Documents, meta: { requiresAuth: true } },
  { path: '/documents/:id', component: DocumentDetail, meta: { requiresAuth: true } },


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
  // লগআউট অবস্থায়: যেকোনো non-public রুটে গেলে login এ পাঠান
  if (!token && !isPublic) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }
  // লগইন থাকা অবস্থায়: login/register এ এলে dashboard এ পাঠান
  if (token && isPublic) {
    return next('/dashboard')
  }
  next()
})

export default router