import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  fetchDashboardSummary,
  fetchUsage,
  fetchRecentDocuments,
} from '../services/dashboard'

describe('dashboard service', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('attaches bearer token when fetching summary', async () => {
    localStorage.setItem('token', 'abc123')
    const response = { ok: true, json: async () => ({ total_documents: 5 }) }
    global.fetch = vi.fn().mockResolvedValue(response)

    const data = await fetchDashboardSummary()
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8890/api/dashboard/summary',
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer abc123' }),
      }),
    )
    expect(data.total_documents).toBe(5)
  })

  it('throws if usage endpoint fails', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false, json: async () => ({}) })
    await expect(fetchUsage(3)).rejects.toThrow('Failed usage')
  })

  it('fetches recent documents with the provided limit', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ count: 5, results: [{ id: 1 }] }),
    })
    const list = await fetchRecentDocuments(2)
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8890/api/documents?limit=2&sort=-created_at',
      expect.any(Object),
    )
    expect(list).toEqual([{ id: 1 }])
  })
})
