import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import Login from './views/Login.vue'
import Register from './views/Register.vue'

const routes = [
  // অ্যাপের মূল হোম
  { path: '/', component: Home, meta: { requiresAuth: true } },
  { path: '/home', component: Home, meta: { requiresAuth: true } },

  // অথ পেজগুলোতে সাইডবার লুকাতে hideSidebar:true
  { path: '/login', component: Login, meta: { hideSidebar: true, public: true } },
  { path: '/register', component: Register, meta: { hideSidebar: true, public: true } },

  // ফ্যালব্যাক
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})