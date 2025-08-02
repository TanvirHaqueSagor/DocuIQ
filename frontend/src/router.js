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
