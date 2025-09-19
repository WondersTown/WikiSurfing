<template>
  <div class="space-y-8 ">
    <!-- Welcome Section -->
    <div class="text-center py-8 border-b border-gray-200">
      <h1 class="text-4xl font-bold text-gray-900 mb-4">Welcome to WikiSurfing</h1>
      <p class="text-lg text-gray-600 max-w-2xl mx-auto">
        The free encyclopedia that anyone can edit. Currently, we have 
        <span class="font-semibold text-blue-600">{{ articlesCount.toLocaleString() }}</span> articles.
      </p>
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

      <!-- Sidebar -->
      <div class="space-y-6">




        <!-- Random Article -->
        <div class="bg-white border border-gray-200 rounded-lg p-6">
          <h2 class="text-xl font-bold text-gray-900 mb-4">Random Article</h2>
          <div class="text-center">
            <button 
              @click="goToRandomArticle"
              class="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Surprise Me!
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// Sample data - in a real app, this would come from an API
const articlesCount = ref(6743821)

const recentArticles = ref([
  {
    title: "黑林村",
    slug: "黑林村",
    excerpt: "...",
    date: "..."
  },
  {
    title: "黑林村瘟疫",
    slug: "黑林村瘟疫",
    excerpt: "...",
    date: "..."
  }
])




// SEO
useHead({
  title: 'WikiSurfing - The Free Encyclopedia',
  meta: [
    { name: 'description', content: 'WikiSurfing is a free encyclopedia that anyone can edit. Explore millions of articles on every topic imaginable.' }
  ]
})
</script>

