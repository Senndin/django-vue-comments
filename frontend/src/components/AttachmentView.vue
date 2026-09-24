<script setup>
/** Вкладення коментаря: мініатюра або файл, що відкривається у модальному вікні (R16, R18a). */
import { ref } from 'vue'

import { fetchTextFile } from '@/api/attachments.js'
import LightboxModal from '@/components/LightboxModal.vue'

const props = defineProps({
  url: { type: String, required: true },
  type: { type: String, required: true },
  authorName: { type: String, default: '' },
})

const open = ref(false)
const textContent = ref('')
const error = ref('')

async function show() {
  error.value = ''
  if (props.type === 'text' && !textContent.value) {
    try {
      textContent.value = await fetchTextFile(props.url)
    } catch {
      error.value = 'Failed to load the file.'
    }
  }
  open.value = true
}
</script>

<template>
  <div class="attachment">
    <button type="button" class="opener" @click="show">
      <img v-if="type === 'image'" :src="url" :alt="`Attachment by ${authorName}`" loading="lazy" />
      <span v-else class="file">📄 Attached text file</span>
    </button>

    <Transition name="lightbox">
      <LightboxModal
        v-if="open"
        :title="type === 'image' ? 'Image' : 'Text file'"
        @close="open = false"
      >
        <img v-if="type === 'image'" :src="url" :alt="`Attachment by ${authorName}`" />
        <p v-else-if="error" class="error">{{ error }}</p>
        <pre v-else>{{ textContent }}</pre>
      </LightboxModal>
    </Transition>
  </div>
</template>

<style scoped>
.attachment {
  margin-top: 0.5rem;
}

.opener {
  padding: 0;
  border: none;
  background: none;
  cursor: zoom-in;
}

.opener img {
  max-width: 100%;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  transition: transform 0.15s ease;
}

.opener:hover img {
  transform: scale(1.02);
}

.file {
  display: inline-block;
  padding: 0.3rem 0.6rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: 0.9rem;
}

pre {
  margin: 0;
  font-family: ui-monospace, monospace;
  font-size: 0.9rem;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.error {
  margin: 0;
  color: var(--color-error);
}

/* Поява вікна: тло проявляється, саме вікно трохи «виїжджає» (R18a, R24). */
.lightbox-enter-active,
.lightbox-leave-active {
  transition: opacity 0.2s ease;
}

.lightbox-enter-from,
.lightbox-leave-to {
  opacity: 0;
}

.lightbox-enter-active :deep(.window),
.lightbox-leave-active :deep(.window) {
  transition:
    transform 0.2s ease,
    opacity 0.2s ease;
}

.lightbox-enter-from :deep(.window),
.lightbox-leave-to :deep(.window) {
  transform: translateY(12px) scale(0.98);
  opacity: 0;
}
</style>
