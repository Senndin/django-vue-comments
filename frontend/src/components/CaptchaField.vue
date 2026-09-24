<script setup>
/** Поле CAPTCHA: картинка, введення і кнопка оновлення (R8, A15). */
import { onMounted, ref } from 'vue'

import { fetchCaptcha } from '@/api/captcha.js'

defineProps({
  modelValue: { type: String, required: true },
  error: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'update:captchaKey'])

const imageUrl = ref('')
const loading = ref(false)

async function refresh() {
  loading.value = true
  try {
    const challenge = await fetchCaptcha()
    imageUrl.value = challenge.image_url
    emit('update:captchaKey', challenge.key)
    emit('update:modelValue', '')
  } finally {
    loading.value = false
  }
}

onMounted(refresh)
// Форма оновлює картинку після відправки й після помилки — ключ одноразовий.
defineExpose({ refresh })
</script>

<template>
  <div class="field">
    <label for="captcha">CAPTCHA</label>
    <div class="captcha">
      <img v-if="imageUrl" :src="imageUrl" alt="Characters to type in" width="172" height="56" />
      <button type="button" :disabled="loading" title="Get another image" @click="refresh">
        ↻
      </button>
      <input
        id="captcha"
        :value="modelValue"
        type="text"
        autocomplete="off"
        placeholder="Type the characters"
        @input="emit('update:modelValue', $event.target.value)"
      />
    </div>
    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<style scoped>
.captcha {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}

img {
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: #fff;
}

input {
  flex: 1 1 10rem;
}
</style>
