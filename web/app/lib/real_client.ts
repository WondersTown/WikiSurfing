import { createClient, createConfig } from './api/client'
import type { ClientOptions } from './api/types.gen'

let _client: ReturnType<typeof createClient> | null = null

// Get base URL based on environment
const getBaseUrl = () => {
  // Check if we're in a browser environment (client-side)
  if (typeof window !== 'undefined') {
    // Client-side: use relative URL which will be proxied by Nuxt
    return '/api'
  } else {
    // Server-side: use API URL from Nuxt runtime config
    const config = useRuntimeConfig()
    return config.apiUrl
  }
}

// Lazy client creation - use this function instead of direct import
export const getRealClient = () => {
  if (!_client) {
    _client = createClient(createConfig<ClientOptions>({
      baseUrl: getBaseUrl()
    }))
  }
  return _client
}
