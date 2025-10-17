import { API_BASE_URL } from '../config'
import { authFetch } from '../lib/authFetch'

const PLAN_KEY = 'subscription_plan'

const parseJson = async (res) => {
  try {
    return await res.json()
  } catch (_) {
    return null
  }
}

export async function fetchSubscriptionPlan() {
  const res = await authFetch(`${API_BASE_URL}/api/accounts/plan/`, { method: 'GET' })
  const data = await parseJson(res)
  if (!res.ok) {
    throw new Error(data?.detail || 'Failed to load plan')
  }
  if (data?.code) {
    try { localStorage.setItem(PLAN_KEY, JSON.stringify(data)) } catch (_) {}
  }
  return data
}

export async function updateSubscriptionPlan(plan) {
  const res = await authFetch(`${API_BASE_URL}/api/accounts/plan/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ plan }),
  })
  const data = await parseJson(res)
  if (!res.ok) {
    throw new Error(data?.detail || 'Unable to update plan')
  }
  if (data?.code) {
    try { localStorage.setItem(PLAN_KEY, JSON.stringify(data)) } catch (_) {}
  }
  return data
}

export async function submitSalesInquiry(payload) {
  const res = await authFetch(`${API_BASE_URL}/api/accounts/contact-sales/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const data = await parseJson(res)
  if (!res.ok) {
    throw new Error(data?.detail || 'Unable to submit request')
  }
  return data
}

export function loadCachedPlan() {
  const raw = localStorage.getItem(PLAN_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch (_) {
    return null
  }
}
