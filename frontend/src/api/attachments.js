/** Читання вмісту текстового вкладення для перегляду в модальному вікні (R18a). */

import { request } from './http.js'

export function fetchTextFile(url) {
  return request(url)
}
