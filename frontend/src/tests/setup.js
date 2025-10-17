import { afterEach, vi } from 'vitest'

afterEach(() => {
  try {
    localStorage.clear()
  } catch (_) {
    /* jsdom may not support localStorage depending on env */
  }
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

if (!global.fetch) {
  global.fetch = vi.fn()
}
