import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { createComment, previewComment } from '@/api/comments.js'
import { ApiError } from '@/api/http.js'
import CommentForm from '@/components/CommentForm.vue'
import { useAuth } from '@/composables/useAuth.js'

vi.mock('@/api/comments.js', () => ({ createComment: vi.fn(), previewComment: vi.fn() }))
vi.mock('@/api/captcha.js', () => ({
  fetchCaptcha: vi.fn().mockResolvedValue({ key: 'test-key', image_url: '/captcha/image/x/' }),
}))
vi.mock('@/api/auth.js', () => ({
  register: vi.fn(),
  obtainTokens: vi.fn().mockResolvedValue({ access: 'a1', refresh: 'r1' }),
  refreshAccess: vi.fn(),
  fetchMe: vi.fn().mockResolvedValue({ id: 1, username: 'Denis', email: 'denis@example.com' }),
}))

beforeEach(() => {
  vi.mocked(createComment).mockReset().mockResolvedValue({ id: 7, parent: null })
  vi.mocked(previewComment).mockReset().mockResolvedValue({ html: '<i>preview</i>' })
  useAuth().logout()
})

async function render(props = {}) {
  const wrapper = mount(CommentForm, { props })
  await flushPromises()
  return wrapper
}

async function fill(wrapper, values = {}) {
  const fields = {
    '#user_name': 'Anonym',
    '#email': 'anonym@example.com',
    '#text': 'Hello there',
    '#captcha': 'ABC123',
    ...values,
  }
  for (const [selector, value] of Object.entries(fields)) {
    await wrapper.find(selector).setValue(value)
  }
}

function sentFields() {
  const payload = vi.mocked(createComment).mock.calls[0][0]
  return Object.fromEntries(payload.entries())
}

describe('CommentForm', () => {
  it('asks for a new captcha challenge when it appears', async () => {
    const wrapper = await render()

    expect(wrapper.find('.captcha img').attributes('src')).toBe('/captcha/image/x/')
  })

  it('sends the filled form', async () => {
    const wrapper = await render()
    await fill(wrapper)

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(sentFields()).toEqual({
      user_name: 'Anonym',
      email: 'anonym@example.com',
      text: 'Hello there',
      captcha_value: 'ABC123',
      captcha_key: 'test-key',
    })
    expect(wrapper.emitted('created')[0][0].id).toBe(7)
  })

  it('sends the parent when answering a comment', async () => {
    const wrapper = await render({ replyTo: { id: 3, user_name: 'Rum8' } })
    await fill(wrapper)

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(sentFields().parent).toBe('3')
    expect(wrapper.find('h2').text()).toBe('Reply to Rum8')
  })

  it('clears the form after a successful send', async () => {
    const wrapper = await render()
    await fill(wrapper)

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.find('#text').element.value).toBe('')
    expect(wrapper.find('#user_name').element.value).toBe('')
  })

  it('shows client side errors and sends nothing', async () => {
    const wrapper = await render()

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const errors = wrapper.findAll('.error').map((node) => node.text())
    expect(errors.length).toBeGreaterThanOrEqual(4)
    expect(createComment).not.toHaveBeenCalled()
  })

  it.each([
    ['#user_name', 'Денис', 'Only latin letters and digits are allowed.'],
    ['#email', 'not-an-email', 'Enter a valid e-mail address.'],
    ['#home_page', 'javascript:alert(1)', 'Only http and https links are allowed.'],
  ])('reports a wrong value of %s', async (selector, value, message) => {
    const wrapper = await render()
    await fill(wrapper)
    await wrapper.find(selector).setValue(value)

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain(message)
    expect(createComment).not.toHaveBeenCalled()
  })

  it('reports forbidden markup before sending anything', async () => {
    const wrapper = await render()
    await fill(wrapper, { '#text': '<script>alert(1)</script>' })

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('Tag <script> is not allowed')
    expect(createComment).not.toHaveBeenCalled()
  })

  it('shows server errors next to the matching fields', async () => {
    vi.mocked(createComment).mockRejectedValue(
      new ApiError(400, { captcha_value: ['CAPTCHA answer is wrong or expired.'] }),
    )
    const wrapper = await render()
    await fill(wrapper)

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('CAPTCHA answer is wrong or expired.')
  })

  it('survives a network failure', async () => {
    vi.mocked(createComment).mockRejectedValue(new TypeError('network down'))
    const wrapper = await render()
    await fill(wrapper)

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('Network error')
  })

  it('shows the preview rendered by the server', async () => {
    const wrapper = await render()
    await fill(wrapper, { '#text': '<i>preview</i>' })

    await wrapper.findAll('button').find((b) => b.text() === 'Preview').trigger('click')
    await flushPromises()

    expect(previewComment).toHaveBeenCalledWith('<i>preview</i>')
    expect(wrapper.find('.preview-body').html()).toContain('<i>preview</i>')
  })

  it('does not ask the server for a preview of broken markup', async () => {
    const wrapper = await render()
    await fill(wrapper, { '#text': '<i>unclosed' })

    await wrapper.findAll('button').find((b) => b.text() === 'Preview').trigger('click')
    await flushPromises()

    expect(previewComment).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('is not closed')
  })
})

describe('CommentForm for a signed in visitor', () => {
  it('fills the name and the e-mail from the account and locks them (A1)', async () => {
    await useAuth().login({ username: 'Denis', password: 'TestPass123!' })
    const wrapper = await render()

    expect(wrapper.find('#user_name').element.value).toBe('Denis')
    expect(wrapper.find('#email').element.value).toBe('denis@example.com')
    expect(wrapper.find('#user_name').attributes('disabled')).toBeDefined()
    expect(wrapper.find('#email').attributes('disabled')).toBeDefined()
  })

  it('sends the account values', async () => {
    await useAuth().login({ username: 'Denis', password: 'TestPass123!' })
    const wrapper = await render()
    await wrapper.find('#text').setValue('from the account')
    await wrapper.find('#captcha').setValue('ABC123')

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(sentFields()).toMatchObject({ user_name: 'Denis', email: 'denis@example.com' })
  })

  it('clears the fields after logging out', async () => {
    await useAuth().login({ username: 'Denis', password: 'TestPass123!' })
    const wrapper = await render()

    useAuth().logout()
    await flushPromises()

    expect(wrapper.find('#user_name').element.value).toBe('')
    expect(wrapper.find('#user_name').attributes('disabled')).toBeUndefined()
  })
})
