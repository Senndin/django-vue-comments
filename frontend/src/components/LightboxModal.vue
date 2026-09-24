<script setup>
/**
 * Модальне вікно перегляду вкладення (R18a, R24).
 *
 * Замість Lightbox2 (він тягне jQuery) — свій компонент на 60 рядків: затемнене тло,
 * поява з анімацією, закриття по Esc, кліку по тлу і кнопці.
 */
import { onMounted, onUnmounted, ref } from 'vue'

defineProps({
  title: { type: String, default: 'Attachment' },
})

const emit = defineEmits(['close'])

const closeButton = ref(null)
let previouslyFocused = null

function onKeydown(event) {
  if (event.key === 'Escape') emit('close')
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
  // Сторінка під вікном не має прокручуватися разом із ним.
  document.body.style.overflow = 'hidden'
  previouslyFocused = document.activeElement
  closeButton.value?.focus()
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
  // Повертаємо фокус туди, звідки вікно відкрили, — інакше клавіатура «губиться».
  previouslyFocused?.focus?.()
})
</script>

<template>
  <div class="backdrop" role="dialog" aria-modal="true" :aria-label="title" @click="emit('close')">
    <!-- Клік усередині вікна не має його закривати, тому подія не йде далі. -->
    <div class="window" @click.stop>
      <header>
        <h3>{{ title }}</h3>
        <button ref="closeButton" type="button" aria-label="Close" @click="emit('close')">✕</button>
      </header>
      <div class="content">
        <slot />
      </div>
    </div>
  </div>
</template>

<style scoped>
.backdrop {
  position: fixed;
  inset: 0;
  z-index: 10;
  display: grid;
  place-items: center;
  padding: 1rem;
  background: rgb(0 0 0 / 65%);
}

.window {
  display: flex;
  flex-direction: column;
  max-width: min(90vw, 40rem);
  max-height: 90vh;
  border-radius: var(--radius);
  background: #fff;
  box-shadow: 0 10px 40px rgb(0 0 0 / 35%);
}

header {
  display: flex;
  gap: 1rem;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--color-border);
}

h3 {
  margin: 0;
  font-size: 1rem;
}

.content {
  padding: 0.75rem;
  overflow: auto;
}
</style>
