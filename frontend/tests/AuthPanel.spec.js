import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { fetchMe, obtainTokens, register as registerRequest } from '@/api/auth.js'
import { ApiError } from '@/api/http.js'
import AuthPanel from '@/components/AuthPanel.vue'
import { useAuth } from '@/composables/useAuth.js'

vi.mock('@/api/auth.js', () => ({
  register: vi.fn(),
  obtainTokens: vi.fn(),
  refreshAccess: vi.fn(),
  fetchMe: vi.fn(),
}))

const account = { id: 1, username: 'Denis', email: 'denis@example.com' }

beforeEach(() => {
  vi.mocked(obtainTokens).mockReset().mockResolvedValue({ access: 'a1', refresh: 'r1' })
  vi.mocked(fetchMe).mockReset().mockResolvedValue(account)
  vi.mocked(registerRequest).mockReset().mockResolvedValue(account)
  useAuth().logout()
})

async function openForm() {
  const wrapper = mount(AuthPanel)
  await wrapper.find('button').trigger('click')
  return wrapper
}

async function fillAndSubmit(wrapper, { email } = {}) {
  const inputs = wrapper.findAll('input')
  await inputs[0].setValue('Denis')
  if (email) await inputs[1].setValue(email)
  await wrapper.findAll('input').at(-1).setValue('TestPass123!')
  await wrapper.find('form').trigger('submit')
  await flushPromises()
}

describe('AuthPanel', () => {
  it('offers signing in to a visitor', () => {
    expect(mount(AuthPanel).text()).toContain('Sign in')
  })

  it('logs the visitor in', async () => {
    const wrapper = await openForm()

    await fillAndSubmit(wrapper)

    expect(obtainTokens).toHaveBeenCalledWith({ username: 'Denis', password: 'TestPass123!' })
    expect(wrapper.text()).toContain('Signed in as')
    expect(wrapper.text()).toContain('Denis')
  })

  it('registers a new account', async () => {
    const wrapper = await openForm()
    await wrapper.findAll('.tabs button')[1].trigger('click')

    await fillAndSubmit(wrapper, { email: 'denis@example.com' })

    expect(registerRequest).toHaveBeenCalledWith({
      username: 'Denis',
      email: 'denis@example.com',
      password: 'TestPass123!',
    })
    expect(wrapper.text()).toContain('Signed in as')
  })

  it('explains a wrong password', async () => {
    vi.mocked(obtainTokens).mockRejectedValue(new ApiError(401, { detail: 'no' }))
    const wrapper = await openForm()

    await fillAndSubmit(wrapper)

    expect(wrapper.find('.error').text()).toBe('Wrong user name or password.')
  })

  it('shows field errors of registration', async () => {
    vi.mocked(registerRequest).mockRejectedValue(
      new ApiError(400, { username: ['A user with that username already exists.'] }),
    )
    const wrapper = await openForm()
    await wrapper.findAll('.tabs button')[1].trigger('click')

    await fillAndSubmit(wrapper, { email: 'denis@example.com' })

    expect(wrapper.find('.error').text()).toContain('already exists')
  })

  it('logs the user out', async () => {
    const wrapper = await openForm()
    await fillAndSubmit(wrapper)

    await wrapper.findAll('button').at(-1).trigger('click')

    expect(wrapper.text()).toContain('Sign in')
  })
})
