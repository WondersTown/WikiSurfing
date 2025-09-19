<template>
  <div>

  <!-- Loading State (initial load) -->
  <div v-if="pending" class="flex justify-center items-center py-16">
    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    <span class="ml-3 text-gray-600">Loading article...</span>
  </div>

  <!-- Error State (failed to load article or proto) -->
  <div v-else-if="error" class="text-center py-16">
    <h1 class="text-3xl font-bold text-gray-900 mb-4">Error Loading Article</h1>
    <p class="text-gray-600 mb-8">{{ error.message || 'Failed to load the article' }}</p>
    <div class="text-center">
      <a href="#" class="text-blue-600 hover:text-blue-800 underline" @click="refresh()" >
        Try Again
      </a>
    </div>
  </div>

  <!-- Not Found (neither article nor proto exists) -->
  <div v-else-if="!apiResponse" class="text-center py-16">
    <h1 class="text-3xl font-bold text-gray-900 mb-4">Article Not Found</h1>
    <p class="text-gray-600 mb-8">The article you're looking for doesn't exist yet.</p>
    <div class="text-center">
      <a href="#" class="text-gray-600 hover:text-gray-800 underline" @click="$router.go(-1)">
        Go Back
      </a>
    </div>
  </div>

  <!-- Generation Status (when generating) -->
  <div v-else-if="isGenerating && !streamingArticle" class="max-w-4xl mx-auto py-4 text-center">
    <div class="flex justify-center items-center mb-4">
      <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-green-600"></div>
      <span class="ml-3 text-green-600 font-medium">Generating article...</span>
      <button class="ml-4 text-red-600 hover:text-red-800 underline text-sm" @click="enhancedStopStreaming" >
        Stop
      </button>
    </div>
  </div>

  <!-- Streaming Content (when generating and have partial content) -->
  <div v-else-if="isGenerating && streamingArticle">
    <!-- Generation Status Bar -->
    <div class="max-w-4xl mx-auto py-4 text-center border-b border-gray-200 mb-6">
      <div class="flex justify-center items-center">
        <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-green-600"></div>
        <span class="ml-2 text-green-600 font-medium text-sm">Generating article...</span>
        <button class="ml-4 text-red-600 hover:text-red-800 underline text-sm" @click="enhancedStopStreaming" >
          Stop
        </button>
      </div>
    </div>
    <!-- Partial Article Content -->
    <ArticleRenderer :api-article="streamingArticle" :is-generating="isGenerating" />
  </div>

  <!-- Generation Failed State -->
  <div v-else-if="generationFailed" class="text-center py-16">
    <h1 class="text-3xl font-bold text-gray-900 mb-4">Generation Failed</h1>
    <p class="text-gray-600 mb-8">Failed to generate the article</p>
    <div class="text-center space-x-4">
      <button class="text-blue-600 hover:text-blue-800 underline" @click="enhancedStartStreaming()" >
        Try Again
      </button>
      <a href="#" class="text-gray-600 hover:text-gray-800 underline" @click="$router.go(-1)" >
        Go Back
      </a>
    </div>
  </div>

  <!-- Full Article Content (either original article or completed generation) -->
  <div v-else-if="displayArticle && displayArticle.kind === 'article'">
    <!-- Regenerate Button -->
    <div class="max-w-4xl mx-auto py-4 text-center border-b border-gray-200 mb-6">
      <button 
        class="text-blue-600 hover:text-blue-800 underline disabled:text-gray-400 disabled:cursor-not-allowed text-sm"
        :disabled="isGenerating"
        @click="enhancedStartStreaming()" 
      >
        {{ isGenerating ? 'Regenerating...' : 'Regenerate Article' }}
      </button>
    </div>
    <!-- Article Content -->
    <ArticleRenderer :api-article="displayArticle" :is-generating="isGenerating" />
  </div>

  <!-- Proto Article Content (show proto with generate button) -->
  <div v-else-if="displayArticle && displayArticle.kind === 'proto_article'" class="max-w-4xl mx-auto py-8">
    <div class="text-center mb-8">
      <h1 class="text-4xl font-bold text-gray-900 mb-4">{{ displayArticle.title }}</h1>
      <div v-if="displayArticle.alt_title && displayArticle.alt_title.length > 0" class="mb-4">
        <p class="text-sm text-gray-600 mb-2">Also known as:</p>
        <div class="flex flex-wrap justify-center gap-2">
          <span v-for="altTitle in displayArticle.alt_title" :key="altTitle" 
                class="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm">
            {{ altTitle }}
          </span>
        </div>
      </div>
    </div>
    
    <div class="text-center mb-8">
      <p class="text-gray-600 italic">
        This article exists as a template but hasn't been fully written yet.
      </p>
    </div>
    
    <div class="text-center space-x-4">
      <button 
        class="text-green-600 hover:text-green-800 underline disabled:text-gray-400 disabled:cursor-not-allowed"
        :disabled="isGenerating"
        @click="enhancedStartStreaming()" 
      >
        {{ isGenerating ? 'Generating...' : 'Create Full Article' }}
      </button>
      <a href="#" class="text-gray-600 hover:text-gray-800 underline" @click="$router.go(-1)">
        Go Back
      </a>
    </div>
  </div>

  </div>
</template>

<script setup lang="ts">
import { getArticle, getArticleProto } from '~/lib/api/sdk.gen'
import type { Article, ProtoArticle } from '~/lib/api/types.gen'
import { getRealClient } from '~/lib/real_client'
import { useStreamingArticle } from '~/lib/streaming'

const route = useRoute()
const slug = route.params.slug as string
// Decode the slug to get the original title for API calls
const title = decodeURIComponent(slug)

// Fetch article data using the API
const { data: apiResponse, pending, error, refresh } = await useLazyAsyncData<Article | ProtoArticle | null>(
  `article-${slug}`,
  async (): Promise<Article | ProtoArticle | null> => {
    // Try to get the main article first
    try {
      const response = await getArticle({
        client: getRealClient(),
        path: {
          space_name: 'default', // You can make this dynamic if needed
          title: title
        }
      })
      
      // If successful and has data, return the article
      if (response.data) {
        return response.data
      }
    } catch (articleError) {
      // If not 404, rethrow the error
      if (articleError && typeof articleError === 'object' && 'response' in articleError) {
        const err = articleError as { response: { status: number } }
        if (err.response.status !== 404) {
          throw articleError
        }
      }
    }
    
    // If article not found (404), try the proto endpoint
    try {
      console.log('Article not found, trying proto endpoint')
      const protoResponse = await getArticleProto({
        client: getRealClient(),
        path: {
          space_name: 'default',
          title: title
        }
      })
      
      // Return proto data if available
      if (protoResponse.data) {
        return protoResponse.data
      }
    } catch (protoError) {
      // If proto also fails with non-404, we'll return null and show not found
      console.log('Proto also not found', protoError)
    }
    
    // If we get here, neither article nor proto was found
    return null
  }
)

// Article generation streaming
const { article: streamingArticle, abortController, startStreaming, stopStreaming } = useStreamingArticle({
  spaceName: 'default',
  title: title,
  request: {
    lang: '中文',
    style_inst: '中世纪欧洲风格，注意地名不能叫做\'欧洲\'',
    context: 'auto',
  }
})

// Track generation state
const generationFailed = ref(false)

// Computed to check if streaming is active based on abort controller
const isGenerating = computed(() => {
  return abortController.value !== null
})

// Enhanced streaming functions with state management
const enhancedStartStreaming = async () => {
  try {
    generationFailed.value = false
    await startStreaming()
    // When streaming completes successfully, the abort controller will be null
    // and the streamingArticle will contain the complete article
  } catch (error) {
    console.error('Generation failed:', error)
    generationFailed.value = true
  }
}

const enhancedStopStreaming = () => {
  stopStreaming()
  generationFailed.value = false
}

// Computed to get the article to display
const displayArticle = computed(() => {
  // Priority 1: If we have a completed streaming article (generation finished), show that
  if (streamingArticle.value && !isGenerating.value) {
    console.log('Returning streaming article finished')
    return streamingArticle.value
  }
  
  // Priority 2: If generating and we have partial streaming content, show that
  if (isGenerating.value && streamingArticle.value) {
    console.log('Returning streaming article generating')
    return streamingArticle.value
  }
  
  // Priority 3: Show the original API response (article or proto)
  console.log('Returning api response')
  return apiResponse.value
})



</script>

<style scoped>
@reference "@/assets/css/main.css";
</style>
