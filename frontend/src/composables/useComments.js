/** Стан таблиці заголовних коментарів: сторінка, сортування, завантаження (R11, R12, R14). */

import { computed, ref } from 'vue'

import { fetchComments } from '@/api/comments.js'

export const PAGE_SIZE = 25
export const DEFAULT_ORDERING = '-created_at'

export function useComments() {
  const comments = ref([])
  const total = ref(0)
  const page = ref(1)
  const ordering = ref(DEFAULT_ORDERING)
  const loading = ref(false)
  const error = ref('')

  const pageCount = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

  async function load() {
    loading.value = true
    error.value = ''
    try {
      const data = await fetchComments({ page: page.value, ordering: ordering.value })
      comments.value = data.results
      total.value = data.count
    } catch {
      // Деталі помилки користувачу не потрібні — потрібна можливість повторити.
      error.value = 'Failed to load comments. Please try again.'
    } finally {
      loading.value = false
    }
  }

  /** Зміна сортування завжди повертає на першу сторінку: інакше вона «поїде». */
  function setOrdering(value) {
    ordering.value = value
    page.value = 1
    return load()
  }

  function setPage(value) {
    page.value = Math.min(Math.max(1, value), pageCount.value)
    return load()
  }

  return { comments, total, page, ordering, loading, error, pageCount, load, setOrdering, setPage }
}
