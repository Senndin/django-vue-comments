import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useWebSocket } from '@/composables/useWebSocket.js'

/** Заглушка WebSocket: запам'ятовує створені з'єднання і дозволяє керувати ними з тесту. */
class FakeWebSocket {
  static instances = []

  constructor(url) {
    this.url = url
    this.closed = false
    FakeWebSocket.instances.push(this)
  }

  open() {
    this.onopen?.()
  }

  receive(data) {
    this.onmessage?.({ data })
  }

  close() {
    this.closed = true
    this.onclose?.()
  }
}

function mountWith(onMessage) {
  const component = {
    setup() {
      const { connected } = useWebSocket('/ws/comments/', onMessage)
      return { connected }
    },
    template: '<span>{{ connected }}</span>',
  }
  return mount(component)
}

beforeEach(() => {
  FakeWebSocket.instances = []
  vi.stubGlobal('WebSocket', FakeWebSocket)
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

describe('useWebSocket', () => {
  it('connects to the same host as the page', () => {
    mountWith(vi.fn())

    expect(FakeWebSocket.instances[0].url).toBe(`ws://${window.location.host}/ws/comments/`)
  })

  it('reports the connection state', async () => {
    const wrapper = mountWith(vi.fn())
    expect(wrapper.text()).toBe('false')

    FakeWebSocket.instances[0].open()
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toBe('true')
  })

  it('passes parsed messages to the handler', () => {
    const onMessage = vi.fn()
    mountWith(onMessage)

    FakeWebSocket.instances[0].receive(JSON.stringify({ type: 'comment.created', comment: { id: 1 } }))

    expect(onMessage).toHaveBeenCalledWith({ type: 'comment.created', comment: { id: 1 } })
  })

  it('survives a broken message', () => {
    const onMessage = vi.fn()
    mountWith(onMessage)

    FakeWebSocket.instances[0].receive('not json')

    expect(onMessage).not.toHaveBeenCalled()
  })

  it('reconnects with a growing delay after a drop', () => {
    mountWith(vi.fn())

    FakeWebSocket.instances[0].close()
    vi.advanceTimersByTime(1000)
    expect(FakeWebSocket.instances).toHaveLength(2)

    FakeWebSocket.instances[1].close()
    vi.advanceTimersByTime(1000)
    // Друга пауза довша за першу — сервер не бомбардується спробами.
    expect(FakeWebSocket.instances).toHaveLength(2)
    vi.advanceTimersByTime(1000)
    expect(FakeWebSocket.instances).toHaveLength(3)
  })

  it('starts the delay over after a successful connection', () => {
    mountWith(vi.fn())
    FakeWebSocket.instances[0].close()
    vi.advanceTimersByTime(1000)

    FakeWebSocket.instances[1].open()
    FakeWebSocket.instances[1].close()
    vi.advanceTimersByTime(1000)

    expect(FakeWebSocket.instances).toHaveLength(3)
  })

  it('stops reconnecting once the component is gone', () => {
    const wrapper = mountWith(vi.fn())

    wrapper.unmount()
    vi.advanceTimersByTime(60000)

    expect(FakeWebSocket.instances[0].closed).toBe(true)
    expect(FakeWebSocket.instances).toHaveLength(1)
  })
})
