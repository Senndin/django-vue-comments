import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { fetchComments, fetchThread } from '@/api/comments.js'
import App from '@/App.vue'

vi.mock('@/api/comments.js', () => ({ fetchComments: vi.fn(), fetchThread: vi.fn() }))

const topComment = {
  id: 1,
  user_name: 'Anonym',
  email: 'anonym@example.com',
  home_page: '',
  created_at: new Date(2022, 4, 22, 22, 30).toISOString(),
  text: 'top comment',
  attachment: null,
  attachment_type: '',
  replies_count: 1,
}

const thread = {
  ...topComment,
  children: [{ ...topComment, id: 2, user_name: 'Replier', text: 'a reply', children: [] }],
}

beforeEach(() => {
  vi.mocked(fetchComments).mockReset().mockResolvedValue({ count: 1, results: [topComment] })
  vi.mocked(fetchThread).mockReset().mockResolvedValue(thread)
})

async function render() {
  const wrapper = mount(App)
  await flushPromises()
  return wrapper
}

describe('App', () => {
  it('loads the first page on start', async () => {
    const wrapper = await render()

    expect(fetchComments).toHaveBeenCalledWith({ page: 1, ordering: '-created_at' })
    expect(wrapper.text()).toContain('Anonym')
  })

  it('loads and shows the thread when a row is expanded', async () => {
    const wrapper = await render()

    await wrapper.find('.toggle').trigger('click')
    await flushPromises()

    expect(fetchThread).toHaveBeenCalledWith(1)
    expect(wrapper.text()).toContain('Replier')
  })

  it('collapses the thread on a second click', async () => {
    const wrapper = await render()
    await wrapper.find('.toggle').trigger('click')
    await flushPromises()

    await wrapper.find('.toggle').trigger('click')

    expect(wrapper.find('.thread-row').exists()).toBe(false)
  })

  it('reloads the first page when sorting changes', async () => {
    const wrapper = await render()

    await wrapper.findAll('.sort-button')[0].trigger('click')
    await flushPromises()

    expect(fetchComments).toHaveBeenLastCalledWith({ page: 1, ordering: '-user_name' })
  })

  it('remembers which comment the visitor answers', async () => {
    const wrapper = await render()
    await wrapper.find('.toggle').trigger('click')
    await flushPromises()

    await wrapper.findAll('.reply-button')[1].trigger('click')

    expect(wrapper.find('.reply-hint').text()).toContain('Replier')
  })

  it('shows an error when the list cannot be loaded', async () => {
    vi.mocked(fetchComments).mockRejectedValue(new Error('boom'))

    const wrapper = await render()

    expect(wrapper.find('.error').exists()).toBe(true)
  })
})
