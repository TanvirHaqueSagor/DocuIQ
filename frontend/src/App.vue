<template>
  <div class="app-shell">
    <!-- Login/Register ইত্যাদিতে সাইডবার লুকাতে চাইলে meta.hideSidebar=true -->
    <Sidebar v-if="!route.meta.hideSidebar" />

    <!-- সাইডবার থাকলে with-sidebar ক্লাস দিন, না থাকলে full -->
    <main :class="['app-main', { 'with-sidebar': !route.meta.hideSidebar, 'full': route.meta.hideSidebar }]">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'

const route = useRoute()
</script>

<style>
:root {
  /* Sidebar dimensions */
  --sb-open: 280px;
  --sb-rail: 72px;
}

.app-shell {
  min-height: 100vh;
  background: var(--bg);
  display: flex;
}

/* Main Content Area */
.app-main {
  flex: 1;
  min-width: 0;
  transition: margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: var(--bg);
}

/* Sidebar logic handled via classes/attributes */
.app-main.with-sidebar {
  margin-left: var(--sb-open);
}

body[data-sidebar="closed"] .app-main.with-sidebar {
  margin-left: var(--sb-rail);
}

.app-main.full {
  margin-left: 0;
  padding: 0;
}

/* Mobile Responsiveness */
@media (max-width: 1024px) {
  .app-main.with-sidebar {
    margin-left: 0 !important; /* Sidebar becomes overlay or hidden */
  }
}
</style>
