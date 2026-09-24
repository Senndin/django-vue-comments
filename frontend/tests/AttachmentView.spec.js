import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { fetchTextFile } from '@/api/attachments.js'
import AttachmentView from '@/components/AttachmentView.vue'

vi.mock('@/api/attachments.js', () => ({ fetchTextFile: vi.fn() }))

function render(props) {
  return mount(AttachmentView, {
    props: { authorName: 'Anonym', ...props },
    attachTo: document.body,
  })
}

async function open(wrapper) {
  await wrapper.find('.opener').trigger('click')
  await flushPromises()
}

beforeEach(() => {
  vi.mocked(fetchTextFile).mockReset().mockResolvedValue('file contents')
  document.body.style.overflow = ''
})

describe('AttachmentView', () => {
  it('shows a thumbnail with a meaningful alt text', () => {
    const image = render({ url: '/media/a.png', type: 'image' }).find('.opener img')

    expect(image.attributes('src')).toBe('/media/a.png')
    expect(image.attributes('alt')).toBe('Attachment by Anonym')
  })

  it('opens an image in the lightbox', async () => {
    const wrapper = render({ url: '/media/a.png', type: 'image' })

    await open(wrapper)

    expect(wrapper.find('.backdrop').exists()).toBe(true)
    expect(wrapper.find('.window h3').text()).toBe('Image')
    expect(wrapper.findAll('img').length).toBe(2)
  })

  it('loads a text file once and shows its contents', async () => {
    const wrapper = render({ url: '/media/a.txt', type: 'text' })

    await open(wrapper)
    await wrapper.find('.window header button').trigger('click')
    await open(wrapper)

    expect(wrapper.find('pre').text()).toBe('file contents')
    // Вміст кешується: другий перегляд не робить нового запиту.
    expect(fetchTextFile).toHaveBeenCalledTimes(1)
  })

  it('reports a failure to load the text file', async () => {
    vi.mocked(fetchTextFile).mockRejectedValue(new Error('boom'))
    const wrapper = render({ url: '/media/a.txt', type: 'text' })

    await open(wrapper)

    expect(wrapper.find('.error').text()).toContain('Failed to load')
  })

  it('closes on the close button, on the backdrop and on Escape', async () => {
    const wrapper = render({ url: '/media/a.png', type: 'image' })

    await open(wrapper)
    await wrapper.find('.window header button').trigger('click')
    expect(wrapper.find('.backdrop').exists()).toBe(false)

    await open(wrapper)
    await wrapper.find('.backdrop').trigger('click')
    expect(wrapper.find('.backdrop').exists()).toBe(false)

    await open(wrapper)
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await flushPromises()
    expect(wrapper.find('.backdrop').exists()).toBe(false)
  })

  it('keeps the window open when its content is clicked', async () => {
    const wrapper = render({ url: '/media/a.png', type: 'image' })
    await open(wrapper)

    await wrapper.find('.window').trigger('click')

    expect(wrapper.find('.backdrop').exists()).toBe(true)
  })

  it('locks the page scroll while the window is open', async () => {
    const wrapper = render({ url: '/media/a.png', type: 'image' })

    await open(wrapper)
    expect(document.body.style.overflow).toBe('hidden')

    await wrapper.find('.window header button').trigger('click')
    expect(document.body.style.overflow).toBe('')
  })
})
