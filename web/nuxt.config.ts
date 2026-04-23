// https://nuxt.com/docs/api/configuration/nuxt-config
const apiUrl = process.env.API_URL || 'http://localhost:8000/api'

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  css: ['~/assets/css/main.css'],

  runtimeConfig: {
    apiUrl
  },

  routeRules: {
    '/api': { proxy: apiUrl },
    '/api/**': { proxy: `${apiUrl}/**` }
  },

  modules: [
    '@nuxt/eslint',
    '@nuxt/image',
    '@nuxt/scripts',
    '@nuxt/ui',
    '@nuxtjs/mdc'
  ]
})
