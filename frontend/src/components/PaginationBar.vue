<script setup>
/** Перемикання сторінок списку (R12). */
const props = defineProps({
  page: { type: Number, required: true },
  pageCount: { type: Number, required: true },
})

const emit = defineEmits(['update:page'])

function go(page) {
  if (page >= 1 && page <= props.pageCount && page !== props.page) emit('update:page', page)
}
</script>

<template>
  <nav v-if="pageCount > 1" class="pagination" aria-label="Pagination">
    <button type="button" :disabled="page === 1" @click="go(page - 1)">← Previous</button>
    <span class="status">Page {{ page }} of {{ pageCount }}</span>
    <button type="button" :disabled="page === pageCount" @click="go(page + 1)">Next →</button>
  </nav>
</template>

<style scoped>
.pagination {
  display: flex;
  gap: 1rem;
  align-items: center;
  justify-content: center;
  margin-top: 1.25rem;
}

.status {
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

button:disabled {
  opacity: 0.5;
  cursor: default;
}
</style>
