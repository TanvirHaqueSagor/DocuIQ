import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import LoginView from '../views/Login.vue'

const replaceMock = vi.fn(() => Promise.resolve())
const pushMock = vi.fn(() => Promise.resolve())

vi.mock('vue-router', () => ({
  useRouter: () => ({ replace: replaceMock, push: pushMock }),
  useRoute: () => ({ query: {} }),
  RouterLink: {
    name: 'RouterLink',
    props: ['to'],
    template: '<a><slot /></a>',
  },
}))

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (key) => key }),
}))

vi.mock('../components/LanguageSwitcher.vue', () => ({
  default: { name: 'LanguageSwitcher', template: '<div />' },
}))

const mountLogin = () =>
  mount(LoginView, {
    global: {
      stubs: {
        transition: false,
        'router-link': {
          template: '<a><slot /></a>',
        },
      },
      mocks: {
        $t: (key) => key,
      },
    },
  })

describe('LoginView', () => {
  beforeEach(() => {
    replaceMock.mockClear()
    pushMock.mockClear()
  })

  it('shows an error when the API rejects the credentials', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'Invalid credentials' }),
    })

    const wrapper = mountLogin()

    await wrapper.find('#email').setValue('user@example.com')
    await wrapper.find('#password').setValue('WrongPass1!')
    await wrapper.find('form').trigger('submit.prevent')
    await nextTick()
    await nextTick()

    expect(wrapper.text()).toContain('invalidAuth')
    expect(global.fetch).toHaveBeenCalledTimes(1)
  })

  it('stores credentials and navigates on successful login', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        access: 'access-token',
        refresh: 'refresh-token',
        user: { id: 1, email: 'user@example.com' },
        account_type: 'individual',
      }),
    })

    const wrapper = mountLogin()

    await wrapper.find('#email').setValue('user@example.com')
    await wrapper.find('#password').setValue('CorrectPass1!')
    await wrapper.find('form').trigger('submit.prevent')
    await nextTick()
    await nextTick()

    expect(localStorage.getItem('token')).toBe('access-token')
    expect(localStorage.getItem('refresh')).toBe('refresh-token')
    expect(replaceMock).toHaveBeenCalledWith('/dashboard')
  })
})
