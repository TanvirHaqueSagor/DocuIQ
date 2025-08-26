//  ======================================
//  src/services/dashboard.js
//  ======================================
const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8890'

export async function fetchDashboardSummary(){
  const r = await fetch(`${baseUrl}/api/dashboard/summary`)
  if(!r.ok) throw new Error('Failed summary')
  return r.json()
}

export async function fetchUsage(days = 14){
  const r = await fetch(`${baseUrl}/api/analytics/usage?days=${days}`)
  if(!r.ok) throw new Error('Failed usage')
  return r.json()
}

export async function fetchRecentDocuments(limit = 8){
  const r = await fetch(`${baseUrl}/api/documents?limit=${limit}&sort=-created_at`)
  if(!r.ok) throw new Error('Failed recent docs')
  return r.json()
}

export async function deleteDocument(id){
  const r = await fetch(`${baseUrl}/api/documents/${id}`, { method:'DELETE' })
  if(!r.ok) throw new Error('Delete failed')
  return r.json().catch(()=> ({}))
}
