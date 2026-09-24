import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import CommentItem from '@/components/CommentItem.vue'

function makeComment(overrides = {}) {
  return {
    id: 1,
    user_name: 'Anonym',
    email: 'anonym@example.com',
    home_page: '',
    created_at: new Date(2022, 4, 22, 22, 30).toISOString(),
    text: 'plain text',
    attachment: null,
    attachment_type: '',
    children: [],
    ...overrides,
  }
}

function render(overrides = {}) {
  return mount(CommentItem, { props: { comment: makeComment(overrides) } })
}

describe('CommentItem', () => {
  it('shows the author, the date and the initials', () => {
    const wrapper = render()

    expect(wrapper.find('.author').text()).toBe('Anonym')
    expect(wrapper.find('.date').text()).toBe('22.05.22 22:30')
    expect(wrapper.find('.avatar').text()).toBe('AN')
  })

  it('renders allowed markup of the text', () => {
    const wrapper = render({ text: '<strong>bold</strong> and <i>italic</i>' })

    expect(wrapper.find('.comment-text').html()).toContain('<strong>bold</strong>')
  })

  it('links the author name to the home page safely', () => {
    const link = render({ home_page: 'https://example.com' }).find('a.author')

    expect(link.attributes('href')).toBe('https://example.com')
    // Чуже посилання не повинно отримати доступ до нашої вкладки (A28).
    expect(link.attributes('rel')).toBe('nofollow noopener noreferrer')
    expect(link.attributes('target')).toBe('_blank')
  })

  it('keeps the name as plain text without a home page', () => {
    expect(render().find('a.author').exists()).toBe(false)
  })

  it('renders nested replies of any depth', () => {
    const wrapper = render({
      children: [
        makeComment({
          id: 2,
          user_name: 'Reply',
          children: [makeComment({ id: 3, user_name: 'Deep' })],
        }),
      ],
    })

    const authors = wrapper.findAll('.author').map((node) => node.text())
    expect(authors).toEqual(['Anonym', 'Reply', 'Deep'])
  })

  it('reports a reply request of any nested comment', async () => {
    const wrapper = render({ children: [makeComment({ id: 2, user_name: 'Reply' })] })

    await wrapper.findAll('.reply-button')[1].trigger('click')

    expect(wrapper.emitted('reply')[0][0].id).toBe(2)
  })

  it('shows a thumbnail for an image and a file button for a text file', () => {
    const image = render({ attachment: '/media/a.png', attachment_type: 'image' })
    const file = render({ attachment: '/media/a.txt', attachment_type: 'text' })

    expect(image.find('.attachment img').attributes('src')).toBe('/media/a.png')
    expect(file.find('.attachment img').exists()).toBe(false)
    expect(file.find('.attachment .file').text()).toContain('text file')
  })

  it('shows nothing about attachments when there is no file', () => {
    expect(render().find('.attachment').exists()).toBe(false)
  })
})
