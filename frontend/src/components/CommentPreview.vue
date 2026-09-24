<script setup>
/** Попередній перегляд повідомлення (R22): показуємо саме те, що збереже сервер (A29). */
defineProps({
  html: { type: String, required: true },
})

defineEmits(['close'])
</script>

<template>
  <section class="preview">
    <header>
      <h3>Preview</h3>
      <button type="button" @click="$emit('close')">Close</button>
    </header>
    <!-- HTML приходить із сервера, зібраний санітайзером із дозволених тегів (A10). -->
    <div class="preview-body" v-html="html"></div>
  </section>
</template>

<style scoped>
.preview {
  margin-top: 0.75rem;
  border: 1px dashed var(--color-border);
  border-radius: var(--radius);
  background: #fff;
}

header {
  display: flex;
  gap: 1rem;
  align-items: center;
  justify-content: space-between;
  padding: 0.4rem 0.6rem;
  border-bottom: 1px dashed var(--color-border);
}

h3 {
  margin: 0;
  font-size: 0.95rem;
}

.preview-body {
  padding: 0.6rem;
  overflow-wrap: anywhere;
}

.preview-body :deep(code) {
  padding: 0.05rem 0.25rem;
  border-radius: 3px;
  background: var(--color-surface);
  font-family: ui-monospace, monospace;
}
</style>
