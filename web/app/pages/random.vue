<template>
  <div class="text-center py-16">
    <div class="max-w-md mx-auto">
      <div class="animate-spin w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-6"></div>
      <h1 class="text-2xl font-bold text-gray-900 mb-4">Finding a Random Article...</h1>
      <p class="text-gray-600">Please wait while we select a random article for you.</p>
    </div>
  </div>
</template>

<script setup>
const randomArticles = [
  'artificial-intelligence',
  'quantum-computing', 
  'climate-change',
  'renaissance-art',
  'world-war-ii',
  'solar-system',
  'leonardo-da-vinci',
  'quantum-mechanics',
  'dna-structure',
  'blockchain-technology'
]

onMounted(() => {
  // Simulate a brief loading time for better UX
  setTimeout(() => {
    const randomSlug = randomArticles[Math.floor(Math.random() * randomArticles.length)]
    navigateTo(`/article/${randomSlug}`)
  }, 1000)
})

// SEO
useHead({
  title: 'Random Article - WikiClone',
  meta: [
    { name: 'description', content: 'Discover something new! Get redirected to a random article on WikiClone.' }
  ]
})
</script>
