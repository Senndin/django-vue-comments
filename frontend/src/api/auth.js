/** Запити аутентифікації (T10, A1, A20). */

import { get, post } from './http.js'

export function register(credentials) {
  return post('/api/auth/register/', credentials)
}

export function obtainTokens({ username, password }) {
  return post('/api/auth/token/', { username, password })
}

export function refreshAccess(refresh) {
  return post('/api/auth/token/refresh/', { refresh })
}

export function fetchMe() {
  return get('/api/auth/me/')
}
