/** Запит нового завдання CAPTCHA (R8, A15). */

import { get } from './http.js'

export function fetchCaptcha() {
  return get('/api/captcha/')
}
