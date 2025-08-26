# ==============================================
# src/components/dashboard/QuickActions.vue
# ==============================================
<template>
  <div class="quick-actions">
    <button class="qa" @click="$emit('newSearch')">🔎 New Search</button>
    <button class="qa" @click="$emit('upload')">⬆️ Upload Document</button>
    <button class="qa" @click="$emit('addDoc')">➕ Add Metadata</button>
  </div>
</template>

<script setup lang="ts"></script>

<style scoped>
.quick-actions{ display:grid; grid-template-columns:1fr; gap:10px; }
.qa{
  border:1px solid rgba(124,92,255,.35);
  background:linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
  padding:12px; border-radius:12px; text-align:left; font-weight:700; color:var(--txt);
  transition: transform .15s ease, box-shadow .15s ease;
}
.qa:hover{ transform: translateY(-2px); box-shadow:0 10px 24px rgba(2,6,23,0.18); }
</style>