<template>
  <div class="space-y-8 ">
    <!-- Welcome Section -->
    <div class="text-center py-8 border-b border-gray-200">
      <div class="mb-6">
        <img 
          src="https://github.com/WondersTown/WikiSurfing/raw/main/assets/wiki-surfing-title.png" 
          alt="Wiki Surfing" 
          class="w-48 h-auto mx-auto"
        >
      </div>
      <h1 class="text-4xl font-bold text-gray-900 mb-2">WikiSurfing</h1>
      <p class="text-lg italic text-gray-500 mb-6">For the enjoyment of surfing.</p>
      <p class="text-lg text-gray-600 max-w-2xl mx-auto mb-2">
        An endless wiki that creates new articles using AI.
      </p>
      <p class="text-base text-gray-500 max-w-2xl mx-auto">
        Click on any link to generate a new article. Each article connects to others, creating an endless browsing experience.
      </p>
      <div class="mt-6">
        <a 
          href="https://github.com/WondersTown/WikiSurfing" 
          target="_blank" 
          rel="noopener noreferrer"
          class="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-gray-800 transition-colors"
        >
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
          </svg>
          View on GitHub
        </a>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Recent Articles -->
      <div class="lg:col-span-2">
        <div class="bg-white border border-gray-200 rounded-lg p-6">
          <h2 class="text-xl font-bold text-gray-900 mb-4">Recent Articles</h2>
          <div class="space-y-3">
            <div v-for="article in recentArticles" :key="article.slug" class="border-l-4 border-blue-500 pl-4">
              <h3 class="font-semibold text-blue-600 hover:text-blue-700">
                <NuxtLink :to="`/article/${article.slug}`">{{ article.title }}</NuxtLink>
              </h3>
              <p class="text-sm text-gray-600">{{ article.excerpt }}</p>
              <p class="text-xs text-gray-500 mt-1">{{ article.date }}</p>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
const recentArticles = ref([
  {
    title: "黑林村瘟疫",
    slug: "黑林村瘟疫",
    excerpt: "...",
    date: "..."
  }
])




// SEO
useHead({
  title: 'WikiSurfing - Endless AI-Generated Wiki',
  meta: [
    { name: 'description', content: 'Wiki Surfing is an endless wiki that creates new articles using AI. Click on any link to generate a new article. Each article connects to others, creating an endless browsing experience.' }
  ]
})
</script>

