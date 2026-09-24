import { flushPromises, mount } from '@vue/test-utils'
import { ref } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { fetchComments, fetchThread } from '@/api/comments.js'
import App from '@/App.vue'

vi.mock('@/api/comments.js', () => ({
  fetchComments: vi.fn(),
  fetchThread: vi.fn(),
  createComment: vi.fn(),
  previewComment: vi.fn(),
}))
// CAPTCHA ходить по мережі вже під час монтування форми — підміняємо й її.
vi.mock('@/api/captcha.js', () => ({
  fetchCaptcha: vi.fn().mockResolvedValue({ key: 'test-key', image_url: '/captcha/image/x/' }),
}))
vi.mock('@/api/auth.js', () => ({
  register: vi.fn(),
  obtainTokens: vi.fn(),
  refreshAccess: vi.fn(),
  fetchMe: vi.fn(),
}))
// З'єднання підміняємо: тест сам викликає обробник, ніби подія прийшла з сервера.
let liveHandler = null
vi.mock('@/composables/useWebSocket.js', () => ({
  useWebSocket: (path, onMessage) => {
    liveHandler = onMessage
    return { connected: ref(true), close: vi.fn() }
  },
}))

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
  // jsdom не вміє прокручувати вікно — підміняємо, щоб не було шуму в логах.
  window.scrollTo = vi.fn()
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

  it('switches the form into reply mode', async () => {
    const wrapper = await render()
    await wrapper.find('.toggle').trigger('click')
    await flushPromises()

    await wrapper.findAll('.reply-button')[1].trigger('click')

    expect(wrapper.find('.comment-form h2').text()).toBe('Reply to Replier')
  })

  it('leaves reply mode on cancel', async () => {
    const wrapper = await render()
    await wrapper.find('.toggle').trigger('click')
    await flushPromises()
    await wrapper.findAll('.reply-button')[1].trigger('click')

    await wrapper.find('.form-header button').trigger('click')

    expect(wrapper.find('.comment-form h2').text()).toBe('Add a comment')
  })

  it('adds a top level comment that arrives over the websocket', async () => {
    const wrapper = await render()

    liveHandler({
      type: 'comment.created',
      comment: { ...topComment, id: 99, user_name: 'FromAnotherTab', parent: null, root: null },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('FromAnotherTab')
    expect(wrapper.text()).toContain('2 discussions')
  })

  it('ignores a comment it already shows', async () => {
    const wrapper = await render()

    liveHandler({ type: 'comment.created', comment: { ...topComment, parent: null, root: null } })
    await flushPromises()

    expect(wrapper.findAll('.comment-row')).toHaveLength(1)
  })

  it('counts a reply in the row of its thread', async () => {
    const wrapper = await render()

    liveHandler({
      type: 'comment.created',
      comment: { ...topComment, id: 100, parent: 1, root: 1 },
    })
    await flushPromises()

    // У колонці «Replies» стало на одну більше.
    expect(wrapper.findAll('.comment-row td').at(-1).text()).toBe('2')
  })

  it('adds a reply to the open thread', async () => {
    const wrapper = await render()
    await wrapper.find('.toggle').trigger('click')
    await flushPromises()

    liveHandler({
      type: 'comment.created',
      comment: {
        ...topComment,
        id: 101,
        user_name: 'LiveReply',
        text: 'live reply',
        parent: 1,
        root: 1,
      },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('LiveReply')
  })

  it('shows an error when the list cannot be loaded', async () => {
    vi.mocked(fetchComments).mockRejectedValue(new Error('boom'))

    const wrapper = await render()

    expect(wrapper.find('.error').exists()).toBe(true)
  })
})
