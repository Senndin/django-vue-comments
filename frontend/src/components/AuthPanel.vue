<script setup>
/** Панель входу: реєстрація, вхід і вихід (T10, A1). */
import { computed, ref } from 'vue'

import { ApiError } from '@/api/http.js'
import { useAuth } from '@/composables/useAuth.js'

const { user, isAuthenticated, login, register, logout } = useAuth()

const mode = ref('login')
const open = ref(false)
const form = ref({ username: '', email: '', password: '' })
const error = ref('')
const busy = ref(false)

const isRegistration = computed(() => mode.value === 'register')

function describe(apiError) {
  if (!(apiError instanceof ApiError)) return 'Network error. Please try again.'
  if (apiError.status === 401) return 'Wrong user name or password.'
  if (typeof apiError.data === 'object' && apiError.data !== null) {
    return Object.entries(apiError.data)
      .map(([field, messages]) => `${field}: ${[messages].flat().join(' ')}`)
      .join('\n')
  }
  return 'Something went wrong. Please try again.'
}

async function submit() {
  error.value = ''
  busy.value = true
  try {
    if (isRegistration.value) await register(form.value)
    else await login(form.value)
    form.value = { username: '', email: '', password: '' }
    open.value = false
  } catch (apiError) {
    error.value = describe(apiError)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="auth">
    <template v-if="isAuthenticated">
      <span class="signed-in">
        Signed in as <strong>{{ user.username }}</strong>
      </span>
      <button type="button" @click="logout">Log out</button>
    </template>

    <template v-else>
      <button type="button" @click="open = !open">{{ open ? 'Hide' : 'Sign in' }}</button>

      <form v-if="open" class="auth-form" novalidate @submit.prevent="submit">
        <div class="tabs">
          <button type="button" :class="{ active: !isRegistration }" @click="mode = 'login'">
            Log in
          </button>
          <button type="button" :class="{ active: isRegistration }" @click="mode = 'register'">
            Register
          </button>
        </div>

        <input
          v-model="form.username"
          type="text"
          placeholder="User name"
          autocomplete="username"
        />
        <input
          v-if="isRegistration"
          v-model="form.email"
          type="email"
          placeholder="E-mail"
          autocomplete="email"
        />
        <input
          v-model="form.password"
          type="password"
          placeholder="Password"
          autocomplete="current-password"
        />

        <button type="submit" :disabled="busy">
          {{ isRegistration ? 'Create account' : 'Log in' }}
        </button>

        <p v-if="error" class="error">{{ error }}</p>
      </form>
    </template>
  </div>
</template>

<style scoped>
.auth {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  justify-content: flex-end;
  position: relative;
}

.signed-in {
  font-size: 0.9rem;
}

.auth-form {
  position: absolute;
  top: 2.5rem;
  right: 0;
  z-index: 5;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  width: 15rem;
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: #fff;
  box-shadow: 0 8px 24px rgb(0 0 0 / 12%);
}

.tabs {
  display: flex;
  gap: 0.25rem;
}

.tabs button {
  flex: 1;
  font-size: 0.85rem;
}

.tabs .active {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

input {
  padding: 0.35rem 0.5rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font: inherit;
}

.error {
  margin: 0;
  color: var(--color-error);
  font-size: 0.8rem;
  white-space: pre-line;
}
</style>
