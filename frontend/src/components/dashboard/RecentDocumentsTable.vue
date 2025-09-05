# =====================================================
# src/components/dashboard/RecentDocumentsTable.vue
# =====================================================
<template>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>{{ $t ? $t('title') : 'Title' }}</th>
          <th>{{ $t ? $t('company') : 'Company' }}</th>
          <th>{{ $t ? $t('year') : 'Year' }}</th>
          <th>{{ $t ? $t('uploaded') : 'Uploaded' }}</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.id">
          <td>{{ row.title }}</td>
          <td>{{ row.company ?? '—' }}</td>
          <td>{{ row.year ?? '—' }}</td>
          <td>{{ formatDate(row.created_at) }}</td>
          <td class="actions">
            <button class="btn sm" @click="$emit('view', row)">{{ $t ? $t('view') : 'View' }}</button>
            <button class="btn sm danger" @click="$emit('delete', row)">{{ $t ? $t('delete') : 'Delete' }}</button>
          </td>
        </tr>
        <tr v-if="!rows || rows.length===0">
          <td colspan="5" class="empty">{{ $t ? $t('noDocs') : 'No documents yet.' }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ rows: any[] }>()

function formatDate(d?: string){
  if(!d) return '—'
  const date = new Date(d)
  return date.toLocaleDateString()
}
</script>

<style scoped>
.table-wrap{ width:100%; overflow:auto; }
table{ width:100%; border-collapse:separate; border-spacing:0 8px; }
th{
  text-align:left; padding:0 10px 6px; color:var(--muted);
  font-size:12px; font-weight:700;
}
td{
  background:var(--panel); color:var(--txt); padding:14px 10px;
  border-top:1px solid rgba(124,92,255,.14); border-bottom:1px solid rgba(124,92,255,.14);
}
tr td:first-child{ border-left:1px solid rgba(124,92,255,.14); border-top-left-radius:10px; border-bottom-left-radius:10px; }
tr td:last-child{ border-right:1px solid rgba(124,92,255,.14); border-top-right-radius:10px; border-bottom-right-radius:10px; }
.actions{ display:flex; gap:6px; justify-content:flex-end; }

.btn.sm{
  padding:8px 10px; border:1px solid rgba(124,92,255,.35); border-radius:8px;
  background:transparent; color:var(--txt); transition: all .15s ease;
}
.btn.sm:hover{ transform: translateY(-1px); box-shadow:0 8px 18px rgba(2,6,23,0.18); }
.btn.sm.danger{ border-color:#ef4444; color:#ef4444; }

.empty{ text-align:center; color:var(--muted); padding:22px; }
.badge{
  background:linear-gradient(90deg, var(--brand), var(--brand-2));
  color:#fff; font-size:11px; padding:4px 8px; border-radius:999px;
}
</style>
