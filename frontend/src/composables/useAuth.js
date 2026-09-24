/**
 * Вхід, реєстрація і зберігання токенів (T10, A1, A20).
 *
 * Стан оголошено на рівні модуля, а не всередині функції: тоді всі компоненти —
 * панель входу і форма коментаря — бачать одного й того самого користувача.
 */

import { computed, ref } from 'vue'

import { fetchMe, obtainTokens, refreshAccess, register as registerRequest } from '@/api/auth.js'
import { setAccessToken, setTokenRefresher } from '@/api/http.js'

const ACCESS_KEY = 'comments.access'
const REFRESH_KEY = 'comments.refresh'

const user = ref(null)
const ready = ref(false)

/** localStorage може бути недоступним (приватне вікно) — тоді працюємо без запам'ятовування. */
function readStorage(key) {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

function writeStorage(key, value) {
  try {
    if (value === null) localStorage.removeItem(key)
    else localStorage.setItem(key, value)
  } catch {
    // Немає сховища — токени житимуть лише до перезавантаження сторінки.
  }
}

function saveTokens({ access, refresh }) {
  writeStorage(ACCESS_KEY, access ?? null)
  if (refresh !== undefined) writeStorage(REFRESH_KEY, refresh)
  setAccessToken(access ?? null)
}

function clearTokens() {
  writeStorage(ACCESS_KEY, null)
  writeStorage(REFRESH_KEY, null)
  setAccessToken(null)
  user.value = null
}

/** Оновлення access за refresh; повертає `true`, якщо вдалося. */
async function refreshTokens() {
  const refresh = readStorage(REFRESH_KEY)
  if (!refresh) return false

  try {
    const tokens = await refreshAccess(refresh)
    saveTokens({ access: tokens.access })
    return true
  } catch {
    // Refresh теж протух — це звичайний вихід, а не помилка.
    clearTokens()
    return false
  }
}

setTokenRefresher(refreshTokens)
setAccessToken(readStorage(ACCESS_KEY))

export function useAuth() {
  const isAuthenticated = computed(() => user.value !== null)

  /** Відновлення сесії при старті сторінки: токен у сховищі є — питаємо, хто це. */
  async function restore() {
    if (!readStorage(ACCESS_KEY) && !readStorage(REFRESH_KEY)) {
      ready.value = true
      return
    }
    try {
      user.value = await fetchMe()
    } catch {
      clearTokens()
    } finally {
      ready.value = true
    }
  }

  async function login({ username, password }) {
    const tokens = await obtainTokens({ username, password })
    saveTokens(tokens)
    user.value = await fetchMe()
  }

  async function register(credentials) {
    await registerRequest(credentials)
    // Реєстрація не видає токенів, тож одразу входимо тими самими даними.
    await login(credentials)
  }

  function logout() {
    // Вихід — це забути токени: відкликати JWT на сервері ми свідомо не робимо (A20).
    clearTokens()
  }

  return { user, ready, isAuthenticated, restore, login, register, logout }
}
