<script setup>
/**
 * Один коментар у гілці та, рекурсивно, його відповіді (R10, A6).
 *
 * Компонент викликає сам себе: саме так дерево будь-якої глибини описується
 * двома десятками рядків розмітки.
 */
import { computed } from 'vue'

import AttachmentView from '@/components/AttachmentView.vue'
import { avatarHue, initials } from '@/utils/avatar.js'
import { formatDate } from '@/utils/formatDate.js'

const props = defineProps({
  comment: { type: Object, required: true },
  depth: { type: Number, default: 0 },
})

defineEmits(['reply'])

const avatarStyle = computed(() => ({
  background: `hsl(${avatarHue(props.comment.user_name)} 60% 88%)`,
  color: `hsl(${avatarHue(props.comment.user_name)} 45% 30%)`,
}))
</script>

<template>
  <article class="comment">
    <header class="comment-header">
      <span class="avatar" :style="avatarStyle" aria-hidden="true">
        {{ initials(comment.user_name) }}
      </span>

      <!-- Ім'я стає посиланням на домашню сторінку автора (A28). -->
      <a
        v-if="comment.home_page"
        class="author"
        :href="comment.home_page"
        target="_blank"
        rel="nofollow noopener noreferrer"
      >
        {{ comment.user_name }}
      </a>
      <span v-else class="author">{{ comment.user_name }}</span>

      <time class="date" :datetime="comment.created_at">{{ formatDate(comment.created_at) }}</time>

      <button type="button" class="reply-button" @click="$emit('reply', comment)">Reply</button>
    </header>

    <!-- Єдине місце з `v-html`: текст уже зібрано санітайзером на сервері (A10). -->
    <div class="comment-text" v-html="comment.text"></div>

    <AttachmentView
      v-if="comment.attachment"
      :url="comment.attachment"
      :type="comment.attachment_type"
      :author-name="comment.user_name"
    />

    <!-- Відповіді з'являються з анімацією: помітно, що в гілці щось змінилося (R24). -->
    <TransitionGroup v-if="comment.children?.length" name="reply" tag="div" class="replies">
      <CommentItem
        v-for="child in comment.children"
        :key="child.id"
        :comment="child"
        :depth="depth + 1"
        @reply="$emit('reply', $event)"
      />
    </TransitionGroup>
  </article>
</template>

<style scoped>
.comment {
  margin-top: 0.75rem;
}

.comment-header {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
  padding: 0.4rem 0.6rem;
  border-radius: var(--radius) var(--radius) 0 0;
  background: var(--color-surface);
}

.avatar {
  display: grid;
  place-items: center;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  font-size: 0.8rem;
  font-weight: 600;
}

.author {
  font-weight: 700;
  color: inherit;
}

a.author:hover {
  color: var(--color-accent);
}

.date {
  color: var(--color-text-muted);
  font-size: 0.85rem;
}

.reply-button {
  margin-left: auto;
  padding: 0.2rem 0.6rem;
  font-size: 0.85rem;
}

.comment-text {
  padding: 0.6rem;
  border: 1px solid var(--color-border);
  border-top: none;
  border-radius: 0 0 var(--radius) var(--radius);
  background: #fff;
  overflow-wrap: anywhere;
}

.comment-text :deep(code) {
  padding: 0.05rem 0.25rem;
  border-radius: 3px;
  background: var(--color-surface);
  font-family: ui-monospace, monospace;
}

/* Вкладеність показуємо відступом. На вузькому екрані відступ менший,
   інакше глибокі відповіді перетворилися б на смужку в один символ. */
.replies {
  margin-left: 2rem;
  border-left: 2px solid var(--color-border);
  padding-left: 0.75rem;
}

@media (max-width: 480px) {
  .replies {
    margin-left: 0.5rem;
    padding-left: 0.5rem;
  }
}

.reply-enter-active {
  transition:
    opacity 0.25s ease,
    transform 0.25s ease;
}

.reply-enter-from {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
