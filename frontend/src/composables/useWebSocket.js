/**
 * Підключення до WebSocket із автоматичним перепідключенням (T6, A16).
 *
 * З'єднання рветься частіше, ніж здається: сон ноутбука, зміна мережі, перезапуск сервера.
 * Тому клієнт сам повертається на місце, збільшуючи паузу між спробами.
 */

import { onUnmounted, ref } from 'vue'

const INITIAL_DELAY = 1000
const MAX_DELAY = 30000

export function useWebSocket(path, onMessage) {
  const connected = ref(false)

  let socket = null
  let delay = INITIAL_DELAY
  let timer = null
  let closedByUs = false

  function url() {
    // Той самий хост і схема, що й у сторінки: у розробці запит іде через проксі Vite,
    // у production — через nginx (етап 16).
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${window.location.host}${path}`
  }

  function scheduleReconnect() {
    if (closedByUs) return
    timer = setTimeout(connect, delay)
    delay = Math.min(delay * 2, MAX_DELAY)
  }

  function connect() {
    socket = new WebSocket(url())

    socket.onopen = () => {
      connected.value = true
      // Успішне підключення скидає паузу: наступний розрив знову почнеться з секунди.
      delay = INITIAL_DELAY
    }

    socket.onmessage = (event) => {
      try {
        onMessage(JSON.parse(event.data))
      } catch {
        // Пошкоджене повідомлення не має валити з'єднання.
      }
    }

    socket.onclose = () => {
      connected.value = false
      scheduleReconnect()
    }

    // `onerror` завжди супроводжується `onclose` — перепідключення там і станеться.
    socket.onerror = () => socket?.close()
  }

  function close() {
    closedByUs = true
    clearTimeout(timer)
    socket?.close()
  }

  connect()
  onUnmounted(close)

  return { connected, close }
}
