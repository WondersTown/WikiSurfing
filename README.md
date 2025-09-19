<div align="center">

<a href="https://wikisurf.ing">
  <img src="assets/wiki-surfing-title.png" alt="Wiki Surfing" width="200">
</a>

*For the enjoyment of surfing.*

</div>

**[Wiki Surfing](https://wikisurf.ing)** is an endless wiki that creates new articles using AI. 

Click on any link to generate a new article. Each article connects to others, creating an endless browsing experience.

## Architecture Guide

> [!WARNING]
> **Early Development Notice**  
> This project is in very early stages of development. This section may be outdated or incomplete. Please expect frequent changes and potential breaking updates.

Wiki Surfing is an AI-powered endless wiki generator built with a modern full-stack architecture. The project consists of two main components: a Python backend API (`core`) and a Nuxt.js frontend (`web`).

### 🚀 Getting Started

#### Backend Setup

Set environment:
```
OPENROUTER_API_KEY=your_openrouter_api_key
```

```bash
cd core
pdm install
pdm run python src/tequila/api.py
```

#### Frontend Setup  
Set environment:
```
API_URL=http://localhost:8000/api
```

```bash
cd web
pnpm install
pnpm dev
```


### 🔧 Technology Stack

**Backend (Core)**
- **FastAPI**: Modern Python web framework for building APIs
- **Pydantic AI**: AI model integration and validation
- **NetworkX**: Graph processing for article relationships
- **PDM**: Python dependency management

**Frontend (Web)**
- **Nuxt.js**: Vue.js framework with SSR/SSG capabilities
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS v4**: Utility-first CSS framework
- **Nuxt UI**: Component library

### 🔄 Core Components

#### 1. Article Generation Pipeline (`pipeline.py`)
- **`_gen_article()`**: Main article generation function
- **`_get_proto_with_context()`**: Retrieves article context
- **`_get_proto_with_related_articles()`**: Finds related articles using PageRank

#### 2. Data Models (`article.py`)
- **`ProtoArticle`**: Article prototype/template
- **`Article`**: Complete article with content
- **`write_article()`**: AI-powered article generation

#### 3. API Layer (`api.py`)
- RESTful endpoints for article operations
- Streaming support for real-time generation
- OpenAPI/Swagger documentation

#### 4. Storage Layer (`storage/`)
- **`docs.py`**: Document CRUD operations
- **`space.py`**: Workspace/namespace management

#### 5. Frontend Components (`web/app/components/`)
- **`ArticleRenderer.vue`**: Renders wiki articles with markdown support
- **`AppHeader.vue`**: Navigation header
- **`AppFooter.vue`**: Footer component

### 🔗 API Integration

The frontend communicates with the backend through:
- **Proxy Configuration**: Nuxt proxies `/api` requests to the FastAPI backend
- **OpenAPI Client**: Auto-generated TypeScript client from OpenAPI spec
- **Server-Sent Events**: Real-time streaming for article generation

### 📊 Content Generation Flow

1. **User Request**: Frontend sends article request to API
2. **Context Retrieval**: System finds related articles and context
3. **AI Generation**: LLM generates article content using prompts
4. **Link Parsing**: Extracts and processes internal links
5. **Storage**: Persists article to storage layer
6. **Rendering**: Frontend renders markdown with custom components