import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// Адреса бекенда в режимі розробки. У production усе віддає nginx з одного домену (етап 16).
const BACKEND = 'http://localhost:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), vueDevTools()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    // Проксі замість CORS: для браузера все приходить з одного джерела —
    // і запити до API, і картинки CAPTCHA, і вкладення, і WebSocket.
    proxy: {
      '/api': BACKEND,
      '/captcha': BACKEND,
      '/media': BACKEND,
      '/ws': { target: BACKEND, ws: true },
    },
  },
})
