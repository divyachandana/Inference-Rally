import { resolve } from 'node:path';
import { defineConfig } from 'vite';

// Dev server on :5173 proxies the game API to the Python server on :8000.
// `npm run build` emits frontend/dist, which the Python server also serves directly.
// Two pages: the game hub (index.html) and the game itself (play.html?game=rally|sf).
export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
  build: {
    target: 'es2022',
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      input: {
        hub: resolve(import.meta.dirname, 'index.html'),
        play: resolve(import.meta.dirname, 'play.html'),
      },
    },
  },
});
