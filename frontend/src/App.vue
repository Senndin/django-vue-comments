<script setup>
/** Головна сторінка: таблиця заголовних коментарів (R11, R12, R14). */
import { onMounted, ref } from 'vue'

import CommentTable from '@/components/CommentTable.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import { useComments } from '@/composables/useComments.js'

const { comments, total, page, ordering, loading, error, pageCount, load, setOrdering, setPage } =
  useComments()

// Розкрита гілка одна: так сторінка лишається оглядовою, а не перетворюється на стрічку.
const expandedId = ref(null)
const replyTo = ref(null)

function toggleThread(commentId) {
  expandedId.value = expandedId.value === commentId ? null : commentId
  replyTo.value = null
}

function startReply(comment) {
  replyTo.value = comment
}

onMounted(load)
</script>

<template>
  <div class="page">
    <header class="page-header">
      <h1>Comments</h1>
      <p class="subtitle">{{ total }} {{ total === 1 ? 'discussion' : 'discussions' }}</p>
    </header>

    <main>
      <p v-if="error" class="message error">
        {{ error }}
        <button type="button" @click="load">Retry</button>
      </p>

      <p v-if="replyTo" class="message reply-hint">
        Replying to <strong>{{ replyTo.user_name }}</strong>
        <button type="button" @click="replyTo = null">Cancel</button>
      </p>

      <div :class="{ loading }">
        <CommentTable
          :comments="comments"
          :ordering="ordering"
          :expanded-id="expandedId"
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
  margin-bottom: 1.5rem;
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

.reply-hint {
  background: var(--color-surface);
}

/* Поки сторінка вантажиться, таблиця лишається на місці — просто тьмянішає. */
.loading {
  opacity: 0.5;
  transition: opacity 0.15s ease;
}
</style>
