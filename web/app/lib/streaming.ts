import { ref, type Ref, onBeforeUnmount } from 'vue'
import { getRealClient } from './real_client'
import type { Article, GenerateArticleRequest } from './api/types.gen'
import { generateArticle } from './api/sdk.gen'

export interface StreamingResult {
  article: Ref<Article | null>
  abortController: Ref<AbortController | null>
  startStreaming: () => Promise<void>
  stopStreaming: () => void
}

export function useStreamingArticle({ spaceName, title, request }: { spaceName: string, title: string, request: GenerateArticleRequest }): StreamingResult {
  const article = ref<Article | null>(null)
  const abortController = ref<AbortController | null>(null)
  const realClient = getRealClient()
  const startStreaming = async () => {
    // Create new abort controller for this streaming session
    abortController.value = new AbortController()
    
    // Reset article state
    article.value = null

    try {
      const { stream } = await generateArticle({
        client: realClient,
        path: {
          space_name: spaceName,
          title: title
        },
        body: {
          ...request,
          streaming: request.streaming || true // Ensure streaming is enabled
        },
        signal: abortController.value.signal
      })

      for await (const event of stream) {
        // Update article with streamed data
        if (event && typeof event === 'object') {
          article.value = event
        }
      }
      
      // Clear abort controller when streaming completes successfully
      abortController.value = null
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('Streaming aborted')
      } else {
        console.error('Streaming failed:', error)
        // Clear abort controller on error
        abortController.value = null
        throw error
      }
    }
  }

  const stopStreaming = () => {
    if (abortController.value) {
      abortController.value.abort()
      abortController.value = null
    }
  }

  // Cleanup on component unmount
  onBeforeUnmount(() => {
    stopStreaming()
  })

  return {
    article,
    abortController,
    startStreaming,
    stopStreaming,
  }
}
