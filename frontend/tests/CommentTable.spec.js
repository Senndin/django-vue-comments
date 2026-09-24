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
    const cells = render().findAll('tbody td')

    expect(cells[0].text()).toBe('Anonym')
    expect(cells[1].text()).toBe('anonym@example.com')
    expect(cells[2].text()).toBe('22.05.22 22:30')
    // Розмітка в таблиці не рендериться — лише текст.
    expect(cells[3].text()).toBe('bold message')
    expect(cells[3].html()).not.toContain('<strong>')
    expect(cells[4].text()).toBe('2')
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
