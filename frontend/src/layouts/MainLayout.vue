<template>
  <div class="main-layout">
    <Sidebar />
    <div class="content-area">
      <slot />
    </div>
  </div>
</template>

<script setup>
import Sidebar from '../components/Sidebar.vue'
</script>

<style scoped>
.main-layout {
  display: flex;
  height: 100vh;
  background: #f7fafd;
}
.content-area {
  flex: 1;
  padding: 0 0 0 0;
  background: #f7fafd;
  overflow-y: auto;
}
</style>
