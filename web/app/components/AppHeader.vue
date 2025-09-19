<template>
  <header class="border-b border-gray-200">
    <div class="max-w-7xl mx-auto px-4 py-2">
      <div class="flex items-center justify-between">
        <!-- Logo and Navigation -->
        <div class="flex items-center space-x-6">
          <NuxtLink to="/" class="flex items-center space-x-2">
            <span class="text-lg font-semibold text-gray-900">WikiSurfing</span>
          </NuxtLink>
          
        </div>

        <!-- Mobile Menu Button -->
        <button class="md:hidden text-gray-600 hover:text-gray-900">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
</script>

<style scoped>
@reference "@/assets/css/main.css";
</style>
