import { createRouter, createWebHistory } from 'vue-router'
import Login from './views/Login.vue'
import Logout from './views/Logout.vue'
import App from './App.vue'

const routes = [
  { path: '/', component: App },
  { path: '/login', component: Login },
  { path: '/logout', component: Logout }
]

export default createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const isAuthenticated = !!localStorage.getItem('access_token')
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})