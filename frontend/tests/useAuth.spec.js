import { beforeEach, describe, expect, it, vi } from 'vitest'

import { fetchMe, obtainTokens, refreshAccess, register as registerRequest } from '@/api/auth.js'
import { ApiError } from '@/api/http.js'
import { useAuth } from '@/composables/useAuth.js'

vi.mock('@/api/auth.js', () => ({
  register: vi.fn(),
  obtainTokens: vi.fn(),
  refreshAccess: vi.fn(),
  fetchMe: vi.fn(),
}))

/**
 * Просте сховище в пам'яті: у цьому середовищі глобальний `localStorage` неповний,
 * а нам потрібна лише передбачувана пара «ключ — значення».
 */
function memoryStorage() {
  const values = new Map()
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, String(value)),
    removeItem: (key) => values.delete(key),
    clear: () => values.clear(),
  }
}

const account = { id: 1, username: 'Denis', email: 'denis@example.com' }
const credentials = { username: 'Denis', email: 'denis@example.com', password: 'TestPass123!' }

beforeEach(() => {
  vi.stubGlobal('localStorage', memoryStorage())
  vi.mocked(obtainTokens).mockReset().mockResolvedValue({ access: 'a1', refresh: 'r1' })
  vi.mocked(fetchMe).mockReset().mockResolvedValue(account)
  vi.mocked(registerRequest).mockReset().mockResolvedValue(account)
  vi.mocked(refreshAccess).mockReset().mockResolvedValue({ access: 'a2' })
  useAuth().logout()
})

describe('useAuth', () => {
  it('logs in and remembers both tokens', async () => {
    const auth = useAuth()

    await auth.login(credentials)

    expect(auth.user.value).toEqual(account)
    expect(auth.isAuthenticated.value).toBe(true)
    expect(localStorage.getItem('comments.access')).toBe('a1')
    expect(localStorage.getItem('comments.refresh')).toBe('r1')
  })

  it('registers and signs in right away', async () => {
    const auth = useAuth()

    await auth.register(credentials)

    expect(registerRequest).toHaveBeenCalledWith(credentials)
    // Реєстрація токенів не видає, тож одразу виконується вхід.
    expect(obtainTokens).toHaveBeenCalled()
    expect(auth.user.value).toEqual(account)
  })

  it('forgets everything on logout', async () => {
    const auth = useAuth()
    await auth.login(credentials)

    auth.logout()

    expect(auth.user.value).toBeNull()
    expect(localStorage.getItem('comments.access')).toBeNull()
    expect(localStorage.getItem('comments.refresh')).toBeNull()
  })

  it('restores the session from a stored token', async () => {
    localStorage.setItem('comments.access', 'a1')
    const auth = useAuth()

    await auth.restore()

    expect(auth.user.value).toEqual(account)
  })

  it('does not ask the server without tokens', async () => {
    const auth = useAuth()

    await auth.restore()

    expect(fetchMe).not.toHaveBeenCalled()
    expect(auth.user.value).toBeNull()
  })

  it('drops a session the server no longer accepts', async () => {
    localStorage.setItem('comments.access', 'stale')
    vi.mocked(fetchMe).mockRejectedValue(new ApiError(401, { detail: 'invalid' }))
    const auth = useAuth()

    await auth.restore()

    expect(auth.user.value).toBeNull()
    expect(localStorage.getItem('comments.access')).toBeNull()
  })

  it('keeps the user signed out when login fails', async () => {
    vi.mocked(obtainTokens).mockRejectedValue(new ApiError(401, { detail: 'no' }))
    const auth = useAuth()

    await expect(auth.login(credentials)).rejects.toBeInstanceOf(ApiError)

    expect(auth.user.value).toBeNull()
  })
})
