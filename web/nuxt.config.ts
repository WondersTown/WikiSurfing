// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  css: ['~/assets/css/main.css'],

  runtimeConfig: {
    apiUrl: process.env.API_URL || 'http://localhost:8000/api'
  },

  modules: [
    '@nuxt/eslint',
    '@nuxt/image',
    '@nuxt/scripts',
    '@nuxt/ui',
    '@nuxtjs/mdc'
  ],

  nitro: {
    devProxy: {
      '/api': {
        target: process.env.API_URL || 'http://localhost:8000/api',
        changeOrigin: true,
        prependPath: true,
        // Support Server-Sent Events
        ws: false,
        headers: {
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive'
        }
      }
    }
  }
})