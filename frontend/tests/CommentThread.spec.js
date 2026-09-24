import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { fetchThread } from '@/api/comments.js'
import CommentThread from '@/components/CommentThread.vue'

// Запити до API підміняємо: тест перевіряє гілку, а не мережу.
vi.mock('@/api/comments.js', () => ({ fetchThread: vi.fn() }))

const thread = {
  id: 1,
  user_name: 'Top',
  home_page: '',
  created_at: new Date(2022, 4, 22, 22, 30).toISOString(),
  text: 'top comment',
  attachment: null,
  attachment_type: '',
  children: [
    {
      id: 2,
      user_name: 'Reply',
      home_page: '',
      created_at: new Date(2022, 4, 22, 22, 43).toISOString(),
      text: 'reply',
      attachment: null,
      attachment_type: '',
      children: [],
    },
  ],
}

beforeEach(() => {
  vi.mocked(fetchThread).mockReset()
})

async function render() {
  const wrapper = mount(CommentThread, { props: { commentId: 1 } })
  await flushPromises()
  return wrapper
}

describe('CommentThread', () => {
  it('loads the thread of the given comment', async () => {
    vi.mocked(fetchThread).mockResolvedValue(thread)

    const wrapper = await render()

    expect(fetchThread).toHaveBeenCalledWith(1)
    expect(wrapper.findAll('.author').map((node) => node.text())).toEqual(['Top', 'Reply'])
  })

  it('shows an error with a retry button when loading fails', async () => {
    vi.mocked(fetchThread).mockRejectedValue(new Error('boom'))

    const wrapper = await render()

    expect(wrapper.find('.error').exists()).toBe(true)

    vi.mocked(fetchThread).mockResolvedValue(thread)
    await wrapper.find('.error button').trigger('click')
    await flushPromises()

    expect(wrapper.find('.error').exists()).toBe(false)
    expect(wrapper.find('.author').text()).toBe('Top')
  })

  it('passes a reply request up', async () => {
    vi.mocked(fetchThread).mockResolvedValue(thread)
    const wrapper = await render()

    await wrapper.findAll('.reply-button')[1].trigger('click')

    expect(wrapper.emitted('reply')[0][0].id).toBe(2)
  })
})
