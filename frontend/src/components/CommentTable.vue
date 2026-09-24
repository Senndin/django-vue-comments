<script setup>
/** Таблиця заголовних коментарів із сортуванням за заголовками (R11, A3). */
import { formatDate } from '@/utils/formatDate.js'
import { excerpt } from '@/utils/text.js'

const props = defineProps({
  comments: { type: Array, required: true },
  ordering: { type: String, required: true },
})

const emit = defineEmits(['update:ordering'])

// Поля, за якими бекенд дозволяє сортувати (білий список у `ordering_fields`).
const columns = [
  { field: 'user_name', label: 'User Name' },
  { field: 'email', label: 'E-mail' },
  { field: 'created_at', label: 'Date' },
]

function isSortedBy(field) {
  return props.ordering === field || props.ordering === `-${field}`
}

function isDescending(field) {
  return props.ordering === `-${field}`
}

/** Перший клік — за спаданням (свіже зверху), повторний — перемикає напрям. */
function toggleSort(field) {
  emit('update:ordering', isDescending(field) ? field : `-${field}`)
}
</script>

<template>
  <div class="table-wrapper">
    <table class="comments-table">
      <thead>
        <tr>
          <th v-for="column in columns" :key="column.field" scope="col">
            <button
              type="button"
              class="sort-button"
              :class="{ active: isSortedBy(column.field) }"
              :aria-sort="
                isSortedBy(column.field)
                  ? isDescending(column.field)
                    ? 'descending'
                    : 'ascending'
                  : 'none'
              "
              @click="toggleSort(column.field)"
            >
              {{ column.label }}
              <span class="sort-arrow" aria-hidden="true">
                {{ isSortedBy(column.field) ? (isDescending(column.field) ? '▼' : '▲') : '↕' }}
              </span>
            </button>
          </th>
          <th scope="col">Message</th>
          <th scope="col" class="numeric">Replies</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="comment in comments" :key="comment.id">
          <td class="nowrap">{{ comment.user_name }}</td>
          <td class="nowrap">{{ comment.email }}</td>
          <td class="nowrap">{{ formatDate(comment.created_at) }}</td>
          <!-- Фрагмент виводимо як текст: обрізаний HTML міг би зламати розмітку сторінки. -->
          <td>{{ excerpt(comment.text) }}</td>
          <td class="numeric">{{ comment.replies_count }}</td>
        </tr>
        <tr v-if="!comments.length">
          <td class="empty" colspan="5">No comments yet — be the first to write one.</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.table-wrapper {
  overflow-x: auto;
}

.comments-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
}

.comments-table th,
.comments-table td {
  padding: 0.6rem 0.75rem;
  border-bottom: 1px solid var(--color-border);
  text-align: left;
  vertical-align: top;
}

.comments-table thead th {
  background: var(--color-surface);
  font-weight: 600;
  white-space: nowrap;
}

.comments-table tbody tr:hover {
  background: var(--color-surface);
}

.sort-button {
  display: inline-flex;
  gap: 0.35rem;
  align-items: center;
  padding: 0;
  border: none;
  background: none;
  font: inherit;
  color: inherit;
  cursor: pointer;
}

.sort-button.active {
  color: var(--color-accent);
}

.sort-arrow {
  font-size: 0.75em;
  opacity: 0.7;
}

.nowrap {
  white-space: nowrap;
}

.numeric {
  text-align: right;
}

.empty {
  padding: 2rem 0.75rem;
  color: var(--color-text-muted);
  text-align: center;
}
</style>
