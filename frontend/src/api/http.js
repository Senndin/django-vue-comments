/**
 * Обгортка над `fetch` — єдине місце, де фронтенд говорить із бекендом.
 *
 * Замість axios: вбудований `fetch` уміє все, що нам потрібно, і не додає залежності.
 */

/** Помилка API: несе статус і тіло відповіді, щоб форма показала помилки біля полів. */
export class ApiError extends Error {
  constructor(status, data) {
    super(`API request failed with status ${status}`)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }

  /** Повідомлення для поля або загальне — те, що показуємо користувачу. */
  messagesFor(field) {
    const messages = this.data?.[field]
    return Array.isArray(messages) ? messages : []
  }
}

async function parseBody(response) {
  if (response.status === 204) return null
  const type = response.headers.get('content-type') ?? ''
  return type.includes('application/json') ? response.json() : response.text()
}

/**
 * Виконує запит і повертає розібране тіло відповіді.
 *
 * `FormData` не чіпаємо: браузер сам виставить `Content-Type` із межею частин,
 * а якщо задати заголовок вручну — multipart зламається.
 */
export async function request(path, { method = 'GET', body, headers = {} } = {}) {
  const options = { method, headers: { ...headers } }

  if (body instanceof FormData) {
    options.body = body
  } else if (body !== undefined) {
    options.headers['Content-Type'] = 'application/json'
    options.body = JSON.stringify(body)
  }

  const response = await fetch(path, options)
  const data = await parseBody(response)

  if (!response.ok) throw new ApiError(response.status, data)
  return data
}

export const get = (path) => request(path)
export const post = (path, body) => request(path, { method: 'POST', body })
