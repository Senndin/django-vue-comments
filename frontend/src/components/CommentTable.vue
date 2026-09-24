<script setup>
/** Таблиця заголовних коментарів із сортуванням за заголовками (R11, A3). */
import CommentThread from '@/components/CommentThread.vue'
import { formatDate } from '@/utils/formatDate.js'
import { excerpt } from '@/utils/text.js'

const props = defineProps({
  comments: { type: Array, required: true },
  ordering: { type: String, required: true },
  expandedId: { type: Number, default: null },
  liveComment: { type: Object, default: null },
})

const emit = defineEmits(['update:ordering', 'toggle', 'reply'])

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
          <th scope="col"><span class="visually-hidden">Expand</span></th>
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
        <template v-for="comment in comments" :key="comment.id">
          <tr class="comment-row" :class="{ expanded: expandedId === comment.id }">
            <td>
              <button
                type="button"
                class="toggle"
                :aria-expanded="expandedId === comment.id"
                :aria-label="expandedId === comment.id ? 'Collapse thread' : 'Expand thread'"
                @click="emit('toggle', comment.id)"
              >
                {{ expandedId === comment.id ? '▾' : '▸' }}
              </button>
            </td>
            <td class="nowrap">{{ comment.user_name }}</td>
            <td class="nowrap">{{ comment.email }}</td>
            <td class="nowrap">{{ formatDate(comment.created_at) }}</td>
            <!-- Фрагмент виводимо як текст: обрізаний HTML міг би зламати розмітку сторінки. -->
            <td>{{ excerpt(comment.text) }}</td>
            <td class="numeric">{{ comment.replies_count }}</td>
          </tr>
          <!-- Гілка вантажиться тільки коли рядок розкрито: зайвих запитів немає. -->
          <tr v-if="expandedId === comment.id" class="thread-row appear">
            <td colspan="6">
              <CommentThread
                :comment-id="comment.id"
                :live-comment="liveComment"
                @reply="emit('reply', $event)"
              />
            </td>
          </tr>
        </template>
        <tr v-if="!comments.length">
          <td class="empty" colspan="6">No comments yet — be the first to write one.</td>
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

.comments-table tbody tr.comment-row:hover {
  background: var(--color-surface);
}

.comment-row.expanded {
  background: var(--color-surface);
}

.thread-row td {
  padding: 0 0.75rem;
  background: var(--color-background);
}

.toggle {
  padding: 0.1rem 0.45rem;
  line-height: 1;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
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
