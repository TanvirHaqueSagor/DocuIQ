//  ======================================
//  src/services/dashboard.js
//  ======================================
const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8890'

const auth = () => {
  const t = localStorage.getItem('token') || localStorage.getItem('access')
  return t ? { Authorization: `Bearer ${t}` } : {}
}

export async function fetchDashboardSummary(){
  const r = await fetch(`${baseUrl}/api/dashboard/summary`, { headers: auth() })
  if(!r.ok) throw new Error('Failed summary')
  return r.json()
}

export async function fetchUsage(days = 14){
  const r = await fetch(`${baseUrl}/api/analytics/usage?days=${days}`, { headers: auth() })
  if(!r.ok) throw new Error('Failed usage')
  return r.json()
}

export async function fetchRecentDocuments(limit = 8){
  const r = await fetch(`${baseUrl}/api/documents?limit=${limit}&sort=-created_at`, { headers: auth() })
  if(!r.ok) throw new Error('Failed recent docs')
  const data = await r.json()
  if (Array.isArray(data?.results)) return data.results
  if (Array.isArray(data)) return data
  return []
}

export async function deleteDocument(id){
  const r = await fetch(`${baseUrl}/api/documents/${id}`, { method:'DELETE', headers: auth() })
  if(!r.ok) throw new Error('Delete failed')
  return r.json().catch(()=> ({}))
}
