/** Запити до API коментарів (files/SPEC.md §3.5). */

import { get, post, request } from './http.js'

/** Сторінка заголовних коментарів: 25 штук, із сортуванням (R11, R12). */
export function fetchComments({ page = 1, ordering = '-created_at' } = {}) {
  const query = new URLSearchParams({ page: String(page), ordering })
  return get(`/api/comments/?${query}`)
}

/** Заголовний коментар з усім деревом відповідей (R10, A5). */
export function fetchThread(commentId) {
  return get(`/api/comments/${commentId}/thread/`)
}

/** Створення коментаря або відповіді. Надсилаємо `FormData` — разом із можливим файлом. */
export function createComment(formData) {
  return request('/api/comments/', { method: 'POST', body: formData })
}

/** Попередній перегляд: сервер повертає той самий HTML, що збереже (R22, A29). */
export function previewComment(text) {
  return post('/api/comments/preview/', { text })
}
