// src/lib/authFetch.js
import { API_BASE_URL } from '../config'

const getToken = () => localStorage.getItem('token') || localStorage.getItem('access') || ''
const isJwt = (t) => typeof t === 'string' && t.includes('.')

const setAccess = (access) => {
  if (!access) return
  localStorage.setItem('token', access)
  localStorage.setItem('access', access)
}

const redirectToLogin = () => {
  const r = encodeURIComponent(window.location.pathname + window.location.search)
  window.location.href = `/login?redirect=${r}`
}

export async function authFetch(input, init = {}) {
  const opts = { ...(init || {}) }
  opts.headers = { ...(opts.headers || {}) }
  // attach auth header only if token looks like JWT
  const t = getToken()
  if (isJwt(t)) {
    opts.headers['Authorization'] = `Bearer ${t}`
  } else {
    delete opts.headers['Authorization']
  }

  let res = await fetch(input, opts)
  if (res.status !== 401) return res

  // Try refresh-once
  const refresh = localStorage.getItem('refresh')
  if (!refresh) {
    redirectToLogin()
    return res
  }
  try {
    const r = await fetch(`${API_BASE_URL}/api/accounts/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh })
    })
    const data = await r.json().catch(() => ({}))
    if (r.ok && data && data.access) {
      setAccess(data.access)
      if (data.refresh) localStorage.setItem('refresh', data.refresh)
      // retry original with new token
      const retryOpts = { ...(init || {}) }
      retryOpts.headers = { ...(retryOpts.headers || {}) }
      retryOpts.headers['Authorization'] = `Bearer ${data.access}`
      return await fetch(input, retryOpts)
    }
  } catch (_) { /* ignore */ }

  redirectToLogin()
  return res
}

