
import { createRouter, createWebHistory } from 'vue-router'

// Core pages
import Dashboard from '@/views/Dashboard.vue'

// Optional pages (create later if not present yet)
const Documents = () => import('@/views/Documents.vue')
const DocumentDetail = () => import('@/views/DocumentDetail.vue')
const Search = () => import('@/views/Search.vue')
const NewAnalysis = () => import('@/views/NewAnalysis.vue')
const AnalysisView = () => import('@/views/AnalysisView.vue')

// Auth pages
const Login = () => import('@/views/Login.vue')
const Register = () => import('@/views/Register.vue')

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: Dashboard, meta: { requiresAuth: true } },

  // Documents
  { path: '/documents', component: Documents, meta: { requiresAuth: true } },
  { path: '/documents/:id', component: DocumentDetail, meta: { requiresAuth: true } },

  // Search & Analysis
  { path: '/search', component: Search, meta: { requiresAuth: true } },
  { path: '/new-analysis', component: NewAnalysis, meta: { requiresAuth: true } },
  { path: '/analysis/:id', component: AnalysisView, meta: { requiresAuth: true } },

  // Auth
  { path: '/login', component: Login, meta: { hideSidebar: true, public: true } },
  { path: '/register', component: Register, meta: { hideSidebar: true, public: true } },

  // Fallback
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// (Optional) simple auth guard – modify per your auth logic
router.beforeEach((to, from, next) => {
  const isPublic = to.meta.public
  const token = localStorage.getItem('auth_token')
  if (!isPublic && to.meta.requiresAuth && !token) {
    return next('/login')
  }
  next()
})

export default router
