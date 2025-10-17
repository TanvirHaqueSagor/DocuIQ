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
:root{
  /* এক জায়গা থেকে কন্ট্রোল */
  --sb-open: 260px;   /* সাইডবার open প্রস্থ */
  --sb-rail: 56px;    /* সাইডবার closed “রেল” প্রস্থ */
}

.app-shell {
  min-height: 100vh;
  background: var(--bg);
}

/* ডিফল্ট main */
.app-main {
  min-height: 100vh;
  min-width: 0;
  padding: 16px;
  transition: margin-left .2s cubic-bezier(.4,0,.2,1);
}

/* সাইডবার থাকলে main বাম দিকে জায়গা ছাড়বে (Sidebar.vue body[data-sidebar] সেট করে) */
.app-main.with-sidebar {
  margin-left: var(--sb-open);
}

/* সাইডবার closed হলে রেল সাইজ */
body[data-sidebar="closed"] .app-main.with-sidebar {
  margin-left: var(--sb-rail);
}

/* সাইডবার লুকানো পাতায় (login/register) full-width */
.app-main.full {
  margin-left: 0;
  padding: 0; /* লগইন/রেজিস্টারে padding না চাইলে রাখুন */
}

/* মোবাইলে: সাইডবার open হলেও overlay স্টাইল—কনটেন্টকে রেলে রাখি */
@media (max-width: 700px) {
  .app-main.with-sidebar {
    margin-left: var(--sb-rail);
  }
}
</style>
