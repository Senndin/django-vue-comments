<script setup>
/** Гілка обговорення: заголовний коментар і всі відповіді (R10, A4, A5). */
import { onMounted, ref } from 'vue'

import { fetchThread } from '@/api/comments.js'
import CommentItem from '@/components/CommentItem.vue'

const props = defineProps({
  commentId: { type: Number, required: true },
})

defineEmits(['reply'])

const thread = ref(null)
const loading = ref(false)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    // Гілка приходить одним запитом цілком, без посторінкового виводу (A4).
    thread.value = await fetchThread(props.commentId)
  } catch {
    error.value = 'Failed to load the thread.'
  } finally {
    loading.value = false
  }
}

onMounted(load)
defineExpose({ load })
</script>

<template>
  <div class="thread">
    <p v-if="loading" class="hint">Loading…</p>
    <p v-else-if="error" class="hint error">
      {{ error }}
      <button type="button" @click="load">Retry</button>
    </p>
    <CommentItem v-else-if="thread" :comment="thread" @reply="$emit('reply', $event)" />
  </div>
</template>

<style scoped>
.thread {
  padding: 0.25rem 0 0.75rem;
}

.hint {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  margin: 0.5rem 0;
  color: var(--color-text-muted);
}

.error {
  color: var(--color-error);
}
</style>
