"""Web-based tools for agents, inspired by the hierarchical agent teams notebook."""

import aiohttp
import asyncio
from typing import List, Dict, Any
from ..core.agent import Tool


class TavilySearchTool(Tool):
    """Tavily search tool for web research."""

    def __init__(self, api_key: str = None, max_results: int = 5):
        """Initialize Tavily search tool.

        Args:
            api_key: Tavily API key (uses TAVILY_API_KEY env var if None)
            max_results: Maximum number of search results
        """
        async def tavily_search(query: str) -> str:
            """Search the web using Tavily.

            Args:
                query: Search query

            Returns:
                Search results as formatted string
            """
            try:
                import os
                from tavily import TavilyClient

                client = TavilyClient(api_key=api_key or os.getenv("TAVILY_API_KEY"))
                results = client.search(query, max_results=max_results)

                formatted_results = []
                for result in results.get("results", []):
                    formatted_results.append(
                        f"Title: {result.get('title', 'N/A')}\n"
                        f"URL: {result.get('url', 'N/A')}\n"
                        f"Content: {result.get('content', 'N/A')}\n"
                    )

                return "\n---\n".join(formatted_results)

            except ImportError:
                raise ImportError("Tavily library not installed. Install with: pip install tavily-python")
            except Exception as e:
                raise Exception(f"Tavily search error: {str(e)}")

        super().__init__(
            name="tavily_search",
            description="Search the web using Tavily for current information",
            func=tavily_search,
            parameters={
                "query": {"type": "string", "description": "The search query"}
            },
        )


class WebScrapeTool(Tool):
    """Web scraping tool for detailed information extraction."""

    def __init__(self):
        """Initialize web scraping tool."""
        async def scrape_webpages(urls: List[str]) -> str:
            """Scrape web pages for detailed information.

            Args:
                urls: List of URLs to scrape

            Returns:
                Scraped content formatted as string
            """
            try:
                async with aiohttp.ClientSession() as session:
                    scraped_content = []

                    for url in urls:
                        try:
                            async with session.get(url, timeout=10) as response:
                                if response.status == 200:
                                    html_content = await response.text()

                                    # Simple text extraction (in real implementation, use BeautifulSoup)
                                    from bs4 import BeautifulSoup
                                    soup = BeautifulSoup(html_content, 'html.parser')

                                    # Remove script and style elements
                                    for script in soup(["script", "style"]):
                                        script.decompose()

                                    # Get text content
                                    text = soup.get_text()

                                    # Clean up whitespace
                                    lines = (line.strip() for line in text.splitlines())
                                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                                    text = ' '.join(chunk for chunk in chunks if chunk)

                                    # Limit text length
                                    if len(text) > 2000:
                                        text = text[:2000] + "..."

                                    scraped_content.append(
                                        f'<Document url="{url}">\n{text}\n</Document>'
                                    )
                                else:
                                    scraped_content.append(f'<Document url="{url}">Failed to fetch: HTTP {response.status}</Document>')

                        except Exception as e:
                            scraped_content.append(f'<Document url="{url}">Error: {str(e)}</Document>')

                    return "\n\n".join(scraped_content)

            except ImportError:
                raise ImportError("Required libraries not installed. Install with: pip install aiohttp beautifulsoup4")
            except Exception as e:
                raise Exception(f"Web scraping error: {str(e)}")

        super().__init__(
            name="scrape_webpages",
            description="Scrape web pages for detailed content extraction",
            func=scrape_webpages,
            parameters={
                "urls": {"type": "array", "description": "List of URLs to scrape"}
            },
        )