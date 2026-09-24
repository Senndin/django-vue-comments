<script setup>
/** Головна сторінка: таблиця заголовних коментарів (R11, R12, R14). */
import { onMounted, ref } from 'vue'

import AuthPanel from '@/components/AuthPanel.vue'
import CommentForm from '@/components/CommentForm.vue'
import CommentTable from '@/components/CommentTable.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import { useAuth } from '@/composables/useAuth.js'
import { DEFAULT_ORDERING, PAGE_SIZE, useComments } from '@/composables/useComments.js'
import { useWebSocket } from '@/composables/useWebSocket.js'

const { comments, total, page, ordering, loading, error, pageCount, load, setOrdering, setPage } =
  useComments()
const { restore } = useAuth()

// Розкрита гілка одна: так сторінка лишається оглядовою, а не перетворюється на стрічку.
const expandedId = ref(null)
const replyTo = ref(null)

function toggleThread(commentId) {
  expandedId.value = expandedId.value === commentId ? null : commentId
  replyTo.value = null
}

function startReply(comment) {
  replyTo.value = comment
  // Форма одна на сторінку і стоїть зверху — після натискання Reply гортаємо до неї.
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

/** Новий коментар: оновлюємо таблицю, щоб побачити його одразу (до етапу 15 — перезапитом). */
async function onCreated(comment) {
  replyTo.value = null
  if (comment.parent === null) {
    expandedId.value = null
    page.value = 1
    ordering.value = DEFAULT_ORDERING
  }
  await load()
}

/** Останній коментар із WebSocket: розкрита гілка сама забере його, якщо він її (A16). */
const liveComment = ref(null)

function onLiveEvent(event) {
  if (event?.type !== 'comment.created') return

  const comment = event.comment
  liveComment.value = comment

  if (comment.parent === null) {
    addToTable(comment)
    return
  }

  // Відповідь: оновлюємо лічильник у рядку її гілки, якщо він зараз на екрані.
  const row = comments.value.find((item) => item.id === comment.root)
  if (row) row.replies_count += 1
}

function addToTable(comment) {
  // Свій же коментар ми вже додали після відправки — не дублюємо.
  if (comments.value.some((item) => item.id === comment.id)) return

  total.value += 1
  // Вставляємо тільки там, де новий коментар справді має бути зверху: на першій
  // сторінці зі звичайним сортуванням. В інших випадках його видно після оновлення.
  if (page.value === 1 && ordering.value === DEFAULT_ORDERING) {
    comments.value = [{ ...comment, replies_count: 0 }, ...comments.value].slice(0, PAGE_SIZE)
  }
}

const { connected } = useWebSocket('/ws/comments/', onLiveEvent)

onMounted(() => {
  load()
  restore()
})
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>Comments</h1>
        <p class="subtitle">
          {{ total }} {{ total === 1 ? 'discussion' : 'discussions' }}
          <span
            class="live"
            :class="{ on: connected }"
            :title="connected ? 'Live updates are on' : 'Reconnecting…'"
          >
            ● {{ connected ? 'live' : 'offline' }}
          </span>
        </p>
      </div>
      <AuthPanel />
    </header>

    <main>
      <p v-if="error" class="message error">
        {{ error }}
        <button type="button" @click="load">Retry</button>
      </p>

      <CommentForm :reply-to="replyTo" @created="onCreated" @cancel-reply="replyTo = null" />

      <div :class="{ loading }">
        <CommentTable
          :comments="comments"
          :ordering="ordering"
          :expanded-id="expandedId"
          :live-comment="liveComment"
          @update:ordering="setOrdering"
          @toggle="toggleThread"
          @reply="startReply"
        />
      </div>

      <PaginationBar :page="page" :page-count="pageCount" @update:page="setPage" />
    </main>
  </div>
</template>

<style scoped>
.page {
  max-width: 60rem;
  margin: 0 auto;
  padding: 2rem 1rem 3rem;
}

.page-header {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

/* Індикатор живого з'єднання: видно, чи прийдуть нові коментарі самі. */
.live {
  margin-left: 0.5rem;
  color: var(--color-text-muted);
  font-size: 0.8rem;
}

.live.on {
  color: #15803d;
}

.subtitle {
  margin-top: 0.25rem;
  color: var(--color-text-muted);
}

.message {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  border-radius: var(--radius);
}

.error {
  background: var(--color-error-surface);
  color: var(--color-error);
}

/* Поки сторінка вантажиться, таблиця лишається на місці — просто тьмянішає. */
.loading {
  opacity: 0.5;
  transition: opacity 0.15s ease;
}
</style>
