import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import CommentTable from '@/components/CommentTable.vue'

const comments = [
  {
    id: 1,
    user_name: 'Anonym',
    email: 'anonym@example.com',
    created_at: new Date(2022, 4, 22, 22, 30).toISOString(),
    text: '<strong>bold</strong> message',
    replies_count: 2,
  },
]

function render(ordering = '-created_at') {
  return mount(CommentTable, { props: { comments, ordering } })
}

describe('CommentTable', () => {
  it('renders a row per comment with a plain-text excerpt', () => {
    // Перша клітинка — кнопка розкриття гілки, далі йдуть дані.
    const [, name, email, date, message, replies] = render().findAll('tbody td')

    expect(name.text()).toBe('Anonym')
    expect(email.text()).toBe('anonym@example.com')
    expect(date.text()).toBe('22.05.22 22:30')
    // Розмітка в таблиці не рендериться — лише текст.
    expect(message.text()).toBe('bold message')
    expect(message.html()).not.toContain('<strong>')
    expect(replies.text()).toBe('2')
  })

  it('asks the parent to expand the thread', async () => {
    const wrapper = render()

    await wrapper.find('.toggle').trigger('click')

    expect(wrapper.emitted('toggle')[0]).toEqual([1])
  })

  it('shows the thread only for the expanded row', () => {
    const collapsed = mount(CommentTable, { props: { comments, ordering: '-created_at' } })
    const expanded = mount(CommentTable, {
      props: { comments, ordering: '-created_at', expandedId: 1 },
      global: { stubs: { CommentThread: true } },
    })

    expect(collapsed.find('.thread-row').exists()).toBe(false)
    expect(expanded.find('.thread-row').exists()).toBe(true)
  })

  it('shows a placeholder when there are no comments', () => {
    const wrapper = mount(CommentTable, { props: { comments: [], ordering: '-created_at' } })

    expect(wrapper.find('.empty').exists()).toBe(true)
  })

  it('asks for descending order on the first click', async () => {
    const wrapper = render()

    await wrapper.findAll('.sort-button')[0].trigger('click')

    expect(wrapper.emitted('update:ordering')[0]).toEqual(['-user_name'])
  })

  it('flips the direction when the active column is clicked again', async () => {
    const wrapper = render('-user_name')

    await wrapper.findAll('.sort-button')[0].trigger('click')

    expect(wrapper.emitted('update:ordering')[0]).toEqual(['user_name'])
  })

  it('marks the active column for screen readers', () => {
    const [name, , date] = render('created_at').findAll('.sort-button')

    expect(date.attributes('aria-sort')).toBe('ascending')
    expect(name.attributes('aria-sort')).toBe('none')
  })
})
