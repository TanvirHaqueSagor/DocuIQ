import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import ImportWizard from '../components/ImportWizard.vue'
import { importWizardBus, closeImportWizard } from '../stores/importWizardBus'

vi.mock('../config', () => ({
  API_BASE_URL: 'http://api.test',
}))

vi.mock('../stores/importWizardBus', async (orig) => {
  const actual = await orig()
  return {
    ...actual,
  }
})

const mountWizard = () =>
  mount(ImportWizard, {
    attachTo: document.body,
  })

describe('ImportWizard', () => {
  beforeEach(() => {
    importWizardBus.open = true
    importWizardBus.preset = null
  })

  afterEach(() => {
    closeImportWizard()
  })

  it('opens with the preset tab selected', async () => {
    importWizardBus.preset = { tab: 'web' }
    const wrapper = mountWizard()
    await nextTick()

    const webHeader = wrapper.find('div.pane h4')
    expect(webHeader.exists()).toBe(true)
    expect(webHeader.text()).toBe('Website')
  })

  it('queues a web import job and shows a success message', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: 123 }),
    })
    global.fetch = fetchMock
    importWizardBus.preset = { tab: 'web' }

    const wrapper = mountWizard()
    await nextTick()

    const urlInput = wrapper.find('input[placeholder="https://example.com/page"]')
    await urlInput.setValue('https://test.example.com')
    await wrapper.find('div.actions .btn').trigger('click')
    await nextTick()
    await new Promise((resolve) => setTimeout(resolve, 0))
    await nextTick()

    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('✅ Website import queued')
  })
})
