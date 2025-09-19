<template>
  <!-- Article Content with TOC -->
  <div v-if="article" class="flex gap-8">
    <!-- Table of Contents -->
    <aside class="hidden md:block w-32 ">
      <div class="sticky top-4">
        <nav class="space-y-2">
          <!-- Page title link to scroll to top -->
          <a href="#top"
            class="block text-sm text-gray-600 hover:text-blue-600 transition-colors py-1 border-l-2 border-transparent hover:border-blue-600 pl-3 font-medium">
            {{ article?.title }}
          </a>
          <!-- Section links from MDC TOC -->
          <a v-for="tocItem in article?.toc?.links" :key="tocItem.id" :href="`#${tocItem.id}`"
            class="block text-sm text-gray-600 hover:text-blue-600 transition-colors py-1 border-l-2 border-transparent hover:border-blue-600 pl-3"
            :style="{ paddingLeft: `${tocItem.depth * 0.5 + 0.75}rem` }">
            {{ tocItem.text }}
          </a>
        </nav>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 min-w-0">
      <!-- Article Header -->
      <div id="top" class="mb-8">
        <h1 class="text-4xl font-bold text-gray-900 mb-4">{{ article.title }}</h1>
      </div>

      <!-- Article Content -->
      <article class="prose max-w-none">
        <MDC :value="article.content" />
      </article>
    </main>
  </div>
</template>

<script setup lang="ts">
import type { Article } from '~/lib/api/types.gen'
import { parseMarkdown } from '@nuxtjs/mdc/runtime'
import type { Toc } from '@nuxtjs/mdc'

// Types
interface ProcessedArticle {
  title: string
  content: string
  toc: Toc | null
}

// Props
interface Props {
  apiArticle: Article
  isGenerating?: boolean
}

const props = defineProps<Props>()

// Function to replace link keys with markdown links
const replaceLinkKeys = (content: string, links: { [key: string]: Array<string> } | undefined): string => {
  if (!links || !content) return content
  
  let processedContent = content

  // Remove single lines of ---
  processedContent = processedContent.replace(/^---$/gm, '')
  
  // If is_generating is true, replace <em>...</em> with **...**
  if (props.isGenerating) {
    processedContent = processedContent.replace(/<em>(.*?)<\/em>/g, '**$1**')
    return processedContent
  }
  
  // Collect all items with their corresponding keys and sort by length (longest first)
  const allItems: Array<{ item: string, key: string }> = []
  
  Object.keys(links).forEach(key => {
    const linkItems = [...links[key] || [], key]
    linkItems.forEach(item => {
      if (item && item.trim()) {
        allItems.push({ item: item.trim(), key })
      }
    })
  })
  
  // Sort by length descending to prioritize longest matches
  allItems.sort((a, b) => b.item.length - a.item.length)
  
  // Keep track of replaced positions to avoid multiple replacements
  const replacedRanges: Array<{ start: number, end: number }> = []
  
  allItems.forEach(({ item, key }) => {
    let searchIndex = 0
    
    while (true) {
      const index = processedContent.indexOf(item, searchIndex)
      if (index === -1) break
      
      const endIndex = index + item.length
      
      // Check if this range overlaps with any already replaced range
      const overlaps = replacedRanges.some(range => 
        (index >= range.start && index < range.end) || 
        (endIndex > range.start && endIndex <= range.end) ||
        (index <= range.start && endIndex >= range.end)
      )
      
      if (!overlaps) {
        // Replace the item with markdown link
        const linkText = `[${item}](/article/${encodeURIComponent(key)})`
        processedContent = processedContent.substring(0, index) + linkText + processedContent.substring(endIndex)
        
        // Update replaced ranges with the new link position
        const lengthDiff = linkText.length - item.length
        replacedRanges.push({ start: index, end: index + linkText.length })
        
        // Adjust existing ranges that come after this replacement
        replacedRanges.forEach(range => {
          if (range.start > index) {
            range.start += lengthDiff
            range.end += lengthDiff
          }
        })
        
        searchIndex = index + linkText.length
      } else {
        searchIndex = index + 1
      }
    }
  })
  
  return processedContent
}

// Convert API Article to markdown format and parse with MDC
const processArticle = async (apiArticle: Article): Promise<ProcessedArticle> => {
  if (!apiArticle) return { title: '', content: '', toc: null }
  
  let markdown = ''
  
  // Add summary if available
  if (apiArticle.summary) {
    const processedSummary = replaceLinkKeys(apiArticle.summary, { [apiArticle.title]: apiArticle.alt_title ?? [], ...apiArticle.links })
    markdown += `${processedSummary}\n\n`
  }
  
  // Add sections
  if (apiArticle.sections && apiArticle.sections.length > 0) {
    apiArticle.sections.forEach(section => {
      const processedContent = replaceLinkKeys(section.content, { [apiArticle.title]: apiArticle.alt_title ?? [], ...apiArticle.links })
      markdown += `## ${section.title}\n\n${processedContent}\n\n`
    })
  }
  
  // Parse markdown with MDC to get TOC
  const parsed = await parseMarkdown(markdown)
  
  return {
    title: apiArticle.title,
    content: markdown,
    toc: parsed.toc || null
  }
}

// Process article with MDC to get content and TOC
const { data: article } = await useLazyAsyncData(
  `processed-article-${props.apiArticle.title}`,
  async () => {
    const processed = await processArticle(props.apiArticle)
    return {
      title: props.apiArticle.title,
      content: processed.content,
      toc: processed.toc
    }
  },
  {
    watch: [() => props.apiArticle]
  }
)
</script>
