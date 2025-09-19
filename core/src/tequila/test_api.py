import asyncio
import httpx
import json
from rich.live import Live
from rich.text import Text
from rich.panel import Panel
from dotenv import load_dotenv

# Import the Article class and response models
from tequila.article import Article
from tequila.api import ProtoWithContextResponse, ProtoWithRelatedResponse, GenerateArticleRequest

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:8000"
SPACE_NAME = "default"  # Default space name

async def test_gen_article_without_proto():
    """Test generating an article from scratch without existing proto."""
    
    # Use a new article title that doesn't exist yet
    new_article_title = "黑林村瘟疫"
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        print(f"Testing article generation without existing proto for '{new_article_title}'...")
        
        # Use Rich Live display for streaming output
        with Live(
            Text("Starting..."), refresh_per_second=10, vertical_overflow="crop"
        ) as live:
            # Prepare request body
            request_data = GenerateArticleRequest(
                lang="中文",
                style_inst="中世纪欧洲风格，注意地名不能叫做'欧洲'",
                streaming=True
            )
            
            # Generate article without proto/context
            async with client.stream(
                "POST",
                f"{BASE_URL}/spaces/{SPACE_NAME}/articles/{new_article_title}/generate",
                json=request_data.model_dump()
            ) as response:
                if response.status_code != 200:
                    print(f"Error generating article: {response.status_code}")
                    error_content = await response.aread()
                    print(error_content.decode())
                    return
                
                current_article = None
                async for line in response.aiter_lines():
                    if line.startswith('data: '):
                        try:
                            # Parse the JSON data
                            json_data = line[6:]  # Remove 'data: ' prefix
                            article_data = json.loads(json_data)
                            
                            # Parse as Article object
                            current_article = Article.model_validate(article_data)
                            
                            # Update the display with the current content
                            content_panel = Panel(
                                current_article.content,
                                title=f"Generated Article: {new_article_title}",
                                title_align="left",
                                border_style="green",
                            )
                            live.update(content_panel)
                        except (json.JSONDecodeError, Exception) as e:
                            # Skip invalid JSON lines or parsing errors
                            continue
            
            print(f"\nArticle generation completed for '{new_article_title}'!")
            if current_article:
                print(f"Final content length: {len(current_article.content)} characters")
                print(f"Article has {len(current_article.sections)} sections")
                return current_article
            return None

async def test_gen_article_pipeline():
    """Test script that replicates the original gen_article_pipeline logic using FastAPI endpoints."""
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        # First, try to get the proto with context for "黑林村"
        print("Getting proto with context for '黑林村'...")
        response = await client.get(f"{BASE_URL}/spaces/{SPACE_NAME}/articles/黑林村/proto/context")
        
        context = None
        if response.status_code == 200:
            proto_response = ProtoWithContextResponse.model_validate(response.json())
            context = proto_response.context
            print(f"Successfully got proto and context for '{proto_response.proto.title}'")
        elif response.status_code == 404:
            print("Proto not found, will generate without context")
        else:
            print(f"Error getting proto with context: {response.status_code}")
            print(response.text)
            return
        
        print("Starting article generation with streaming...")
        
        # Use Rich Live display for streaming output
        with Live(
            Text("Starting..."), refresh_per_second=10, vertical_overflow="crop"
        ) as live:
            # Prepare request body
            request_data = GenerateArticleRequest(
                lang="中文",
                style_inst="中世纪欧洲风格，注意地名不能叫做'欧洲'",
                streaming=True,
                context=context
            )
                
            async with client.stream(
                 "POST",
                 f"{BASE_URL}/spaces/{SPACE_NAME}/articles/黑林村/generate",
                 json=request_data.model_dump()
            ) as response:
                if response.status_code != 200:
                    print(f"Error generating article: {response.status_code}")
                    error_content = await response.aread()
                    print(error_content.decode())
                    return
                
                current_article = None
                async for line in response.aiter_lines():
                    if line.startswith('data: '):
                        try:
                            # Parse the JSON data
                            json_data = line[6:]  # Remove 'data: ' prefix
                            article_data = json.loads(json_data)
                            
                            # Parse as Article object
                            current_article = Article.model_validate(article_data)
                            
                            # Update the display with the current content
                            content_panel = Panel(
                                current_article.content,
                                title="Generated Article",
                                title_align="left",
                                border_style="blue",
                            )
                            live.update(content_panel)
                        except (json.JSONDecodeError, Exception) as e:
                            # Skip invalid JSON lines or parsing errors
                            continue
            
            print(f"\nArticle generation completed!")
            if current_article:
                print(f"Final content length: {len(current_article.content)} characters")
                print(f"Article has {len(current_article.sections)} sections")

async def test_proto_endpoints():
    """Test the proto-related endpoints."""
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        # Test proto with context - should handle 404 gracefully
        print("Testing proto with context endpoint...")
        response = await client.get(f"{BASE_URL}/spaces/{SPACE_NAME}/articles/黑林村瘟疫/proto/context")
        if response.status_code == 200:
            proto_response = ProtoWithContextResponse.model_validate(response.json())
            print(f"✓ Proto with context: Got proto for '{proto_response.proto.title}' with {len(proto_response.context)} chars of context")
        elif response.status_code == 404:
            print("✓ Proto with context: Article not found (404) - this is expected for new articles")
        else:
            print(f"✗ Proto with context failed: {response.status_code}")
        
        # Test proto with related articles - should handle 404 gracefully
        print("Testing proto with related articles endpoint...")
        response = await client.get(f"{BASE_URL}/spaces/{SPACE_NAME}/articles/黑林村瘟疫/proto/related")
        if response.status_code == 200:
            proto_response = ProtoWithRelatedResponse.model_validate(response.json())
            print(f"✓ Proto with related: Got proto for '{proto_response.proto.title}' with {len(proto_response.related_articles)} related articles")
        elif response.status_code == 404:
            print("✓ Proto with related: Article not found (404) - this is expected for new articles")
        else:
            print(f"✗ Proto with related failed: {response.status_code}")

async def test_non_streaming_generation():
    """Test non-streaming article generation."""
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        # Try to get context first, but don't fail if it doesn't exist
        context = None
        response = await client.get(f"{BASE_URL}/spaces/{SPACE_NAME}/articles/黑林村/proto/context")
        if response.status_code == 200:
            proto_response = ProtoWithContextResponse.model_validate(response.json())
            context = proto_response.context
        elif response.status_code != 404:
            print(f"Unexpected error getting context: {response.status_code}")
            return
        
        # Test non-streaming generation
        print("Testing non-streaming article generation...")
        request_data = GenerateArticleRequest(
            lang="中文",
            style_inst="中世纪欧洲风格，注意地名不能叫做'欧洲'",
            streaming=False,
            context=context
        )
            
        response = await client.post(
            f"{BASE_URL}/spaces/{SPACE_NAME}/articles/黑林村/generate",
            json=request_data.model_dump()
        )
        if response.status_code == 200:
            article = Article.model_validate(response.json())
            print(f"✓ Non-streaming generation: Got article '{article.title}' with content length: {len(article.content)} characters")
            print(f"  Article has {len(article.sections)} sections")
        else:
            print(f"✗ Non-streaming generation failed: {response.status_code}")

async def main():
    """Main test function that runs all tests."""
    print("=== Tequila Wiki API Test Suite ===\n")
    
    # Test if API is running
    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
            response = await client.get(f"{BASE_URL}/")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ API is running: {data['message']}\n")
            else:
                print(f"✗ API not responding properly: {response.status_code}")
                return
        except httpx.RequestError:
            print("✗ Cannot connect to API. Make sure the FastAPI server is running on localhost:8000")
            print("  Run: python -m tequila.api")
            return
    
    # First test: Generate article without existing proto
    await test_gen_article_without_proto()
    print()
    
    # Test proto endpoints (should handle 404s gracefully)
    await test_proto_endpoints()
    print()
    
    # Test non-streaming generation (should work with or without proto)
    await test_non_streaming_generation()
    print()
    
    # Run the main pipeline test (streaming, with fallback for missing proto)
    await test_gen_article_pipeline()

if __name__ == "__main__":
    asyncio.run(main())
