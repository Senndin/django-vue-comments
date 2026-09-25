<script setup>
/**
 * Форма нового коментаря або відповіді (R5–R9, R16, R21–R23).
 *
 * Перевірки проходять двічі: тут — щоб показати помилку одразу, і на сервері — бо
 * саме його рішення остаточне. Помилки сервера розкладаються під ті самі поля.
 */
import { ref, watch } from 'vue'

import { ApiError } from '@/api/http.js'
import { createComment, previewComment } from '@/api/comments.js'
import CaptchaField from '@/components/CaptchaField.vue'
import CommentPreview from '@/components/CommentPreview.vue'
import HtmlToolbar from '@/components/HtmlToolbar.vue'
import { useAuth } from '@/composables/useAuth.js'
import {
  validateAttachment,
  validateCaptcha,
  validateEmail,
  validateHomePage,
  validateText,
  validateUserName,
} from '@/utils/validators.js'

const props = defineProps({
  // Коментар, на який відповідаємо; `null` — це новий заголовний коментар.
  replyTo: { type: Object, default: null },
})

const emit = defineEmits(['created', 'cancel-reply'])

const { user, isAuthenticated } = useAuth()

/** Порожня форма. У того, хто ввійшов, підпис одразу з акаунта (A1). */
function blankForm() {
  return {
    user_name: user.value?.username ?? '',
    email: user.value?.email ?? '',
    home_page: '',
    text: '',
    captcha_value: '',
  }
}

const form = ref(blankForm())
const captchaKey = ref('')
const attachment = ref(null)
const errors = ref({})
const preview = ref('')
const sending = ref(false)

// Ім'я та e-mail того, хто ввійшов, підставляються з акаунта і не редагуються (A1).
// Сервер усе одно бере їх із токена, тут це лише узгоджений вигляд форми.
watch(
  user,
  (account) => {
    form.value.user_name = account?.username ?? ''
    form.value.email = account?.email ?? ''
  },
  { immediate: true },
)

const textarea = ref(null)
const captchaField = ref(null)
const fileInput = ref(null)

function validate() {
  const found = {
    user_name: validateUserName(form.value.user_name),
    email: validateEmail(form.value.email),
    home_page: validateHomePage(form.value.home_page),
    text: validateText(form.value.text),
    captcha_value: validateCaptcha(form.value.captcha_value),
    attachment: validateAttachment(attachment.value),
  }
  errors.value = Object.fromEntries(Object.entries(found).filter(([, message]) => message))
  return !Object.keys(errors.value).length
}

/** Помилки DRF приходять як `{"поле": ["повідомлення", …]}` — розкладаємо їх під поля. */
function showServerErrors(error) {
  if (!(error instanceof ApiError)) {
    errors.value = { form: 'Network error. Please try again.' }
    return
  }
  if (typeof error.data !== 'object' || error.data === null) {
    errors.value = { form: 'Something went wrong. Please try again.' }
    return
  }
  errors.value = Object.fromEntries(
    Object.entries(error.data).map(([field, messages]) => [
      field,
      Array.isArray(messages) ? messages.join(' ') : String(messages),
    ]),
  )
}

function selectFile(event) {
  attachment.value = event.target.files?.[0] ?? null
  errors.value = { ...errors.value, attachment: validateAttachment(attachment.value) || undefined }
}

async function showPreview() {
  const textError = validateText(form.value.text)
  if (textError) {
    errors.value = { ...errors.value, text: textError }
    return
  }
  try {
    const result = await previewComment(form.value.text)
    preview.value = result.html
    errors.value = { ...errors.value, text: undefined }
  } catch (error) {
    preview.value = ''
    showServerErrors(error)
  }
}

function reset() {
  // Саме `blankForm`, а не порожні рядки: інакше після відправки поля підпису
  // лишалися б і порожніми, і заблокованими — другий коментар надіслати неможливо.
  form.value = blankForm()
  attachment.value = null
  if (fileInput.value) fileInput.value.value = ''
  preview.value = ''
  errors.value = {}
}

async function submit() {
  if (!validate()) return

  sending.value = true
  try {
    const payload = new FormData()
    for (const [field, value] of Object.entries(form.value)) {
      if (value) payload.append(field, value)
    }
    payload.append('captcha_key', captchaKey.value)
    if (attachment.value) payload.append('attachment', attachment.value)
    if (props.replyTo) payload.append('parent', String(props.replyTo.id))

    const comment = await createComment(payload)
    reset()
    emit('created', comment)
  } catch (error) {
    showServerErrors(error)
  } finally {
    sending.value = false
    // Ключ CAPTCHA одноразовий: після будь-якої спроби потрібна нова картинка.
    captchaField.value?.refresh()
  }
}
</script>

<template>
  <form class="comment-form" novalidate @submit.prevent="submit">
    <header class="form-header">
      <h2>{{ replyTo ? `Reply to ${replyTo.user_name}` : 'Add a comment' }}</h2>
      <button v-if="replyTo" type="button" @click="$emit('cancel-reply')">Cancel reply</button>
    </header>

    <div class="row">
      <div class="field">
        <label for="user_name">User name *</label>
        <input
          id="user_name"
          v-model="form.user_name"
          type="text"
          autocomplete="nickname"
          :disabled="isAuthenticated"
        />
        <p v-if="errors.user_name" class="error">{{ errors.user_name }}</p>
      </div>

      <div class="field">
        <label for="email">E-mail *</label>
        <input
          id="email"
          v-model="form.email"
          type="email"
          autocomplete="email"
          :disabled="isAuthenticated"
        />
        <p v-if="errors.email" class="error">{{ errors.email }}</p>
      </div>
    </div>

    <p v-if="isAuthenticated" class="hint account-hint">
      Signed in as {{ user.username }} — the name and e-mail come from your account.
    </p>

    <div class="field">
      <label for="home_page">Home page</label>
      <input id="home_page" v-model="form.home_page" type="url" placeholder="https://example.com" />
      <p v-if="errors.home_page" class="error">{{ errors.home_page }}</p>
    </div>

    <div class="field">
      <label for="text">Message *</label>
      <HtmlToolbar v-model="form.text" :textarea="textarea" />
      <textarea id="text" ref="textarea" v-model="form.text" rows="6"></textarea>
      <p class="hint">Allowed tags: &lt;a&gt;, &lt;code&gt;, &lt;i&gt;, &lt;strong&gt;.</p>
      <p v-if="errors.text" class="error">{{ errors.text }}</p>
    </div>

    <div class="field">
      <label for="attachment">Attachment</label>
      <input
        id="attachment"
        ref="fileInput"
        type="file"
        accept=".jpg,.jpeg,.gif,.png,.txt"
        @change="selectFile"
      />
      <p class="hint">Image up to 5 MB (resized to 320×240) or a TXT file up to 100 KB.</p>
      <p v-if="errors.attachment" class="error">{{ errors.attachment }}</p>
    </div>

    <CaptchaField
      ref="captchaField"
      v-model="form.captcha_value"
      :error="errors.captcha_value"
      @update:captcha-key="captchaKey = $event"
    />

    <p v-if="errors.form" class="error">{{ errors.form }}</p>

    <div class="actions">
      <button type="submit" class="primary" :disabled="sending">
        {{ sending ? 'Sending…' : 'Send' }}
      </button>
      <button type="button" @click="showPreview">Preview</button>
    </div>

    <CommentPreview v-if="preview" :html="preview" @close="preview = ''" />
  </form>
</template>

<style scoped>
.comment-form {
  margin-bottom: 1.5rem;
  padding: 1rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: #fff;
}

.form-header {
  display: flex;
  gap: 1rem;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

h2 {
  margin: 0;
  font-size: 1.15rem;
}

.row {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.row .field {
  flex: 1 1 14rem;
}

.field {
  margin-bottom: 0.75rem;
}

label {
  display: block;
  margin-bottom: 0.25rem;
  font-size: 0.9rem;
  font-weight: 600;
}

input:disabled {
  background: var(--color-surface);
  color: var(--color-text-muted);
}

input[type='text'],
input[type='email'],
input[type='url'],
textarea {
  width: 100%;
  padding: 0.4rem 0.5rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font: inherit;
}

textarea {
  resize: vertical;
}

.hint {
  margin: 0.25rem 0 0;
  color: var(--color-text-muted);
  font-size: 0.8rem;
}

.error {
  margin: 0.25rem 0 0;
  color: var(--color-error);
  font-size: 0.85rem;
}

.account-hint {
  margin-bottom: 0.5rem;
}

.actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

.primary {
  border-color: var(--color-accent);
  background: var(--color-accent);
  color: #fff;
}

.primary:hover:not(:disabled) {
  color: #fff;
  filter: brightness(1.08);
}
</style>
