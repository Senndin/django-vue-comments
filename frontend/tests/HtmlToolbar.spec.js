import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import HtmlToolbar from '@/components/HtmlToolbar.vue'

/** Заглушка `<textarea>`: компоненту потрібні лише межі виділення і фокус. */
function fakeTextarea(selectionStart, selectionEnd) {
  return {
    selectionStart,
    selectionEnd,
    focus: vi.fn(),
    setSelectionRange: vi.fn(),
  }
}

function render(modelValue, textarea = null) {
  return mount(HtmlToolbar, { props: { modelValue, textarea } })
}

function clickTag(wrapper, label) {
  return wrapper.findAll('button').find((button) => button.text() === label).trigger('click')
}

describe('HtmlToolbar', () => {
  it('offers exactly the four allowed tags', () => {
    const labels = render('').findAll('button').map((button) => button.text())

    expect(labels).toEqual(['[i]', '[strong]', '[code]', '[a]'])
  })

  it('wraps the selected text', async () => {
    const wrapper = render('hello world', fakeTextarea(6, 11))

    await clickTag(wrapper, '[strong]')

    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['hello <strong>world</strong>'])
  })

  it('inserts an empty pair when nothing is selected', async () => {
    const wrapper = render('hello', fakeTextarea(5, 5))

    await clickTag(wrapper, '[i]')

    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['hello<i></i>'])
  })

  it('gives a link a ready to fill template with an allowed scheme', async () => {
    const wrapper = render('site', fakeTextarea(0, 4))

    await clickTag(wrapper, '[a]')

    expect(wrapper.emitted('update:modelValue')[0]).toEqual([
      '<a href="https://" title="">site</a>',
    ])
  })

  it('appends to the end when there is no textarea yet', async () => {
    const wrapper = render('text')

    await clickTag(wrapper, '[code]')

    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['text<code></code>'])
  })

  it('returns the focus to the textarea', async () => {
    const textarea = fakeTextarea(0, 0)
    const wrapper = render('', textarea)

    await clickTag(wrapper, '[i]')

    expect(textarea.focus).toHaveBeenCalled()
  })
})
