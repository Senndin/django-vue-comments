import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import PaginationBar from '@/components/PaginationBar.vue'

function render(page, pageCount) {
  return mount(PaginationBar, { props: { page, pageCount } })
}

describe('PaginationBar', () => {
  it('stays hidden while everything fits on one page', () => {
    expect(render(1, 1).find('nav').exists()).toBe(false)
  })

  it('shows the current position', () => {
    expect(render(2, 5).text()).toContain('Page 2 of 5')
  })

  it('asks for the next and the previous page', async () => {
    const wrapper = render(2, 5)
    const [previous, next] = wrapper.findAll('button')

    await next.trigger('click')
    await previous.trigger('click')

    expect(wrapper.emitted('update:page')).toEqual([[3], [1]])
  })

  it('disables navigation at the edges', () => {
    expect(render(1, 3).findAll('button')[0].attributes('disabled')).toBeDefined()
    expect(render(3, 3).findAll('button')[1].attributes('disabled')).toBeDefined()
  })
})
