"""Research agents inspired by the hierarchical agent teams notebook."""

import asyncio
from typing import Optional
from ..core.agent import Agent
from ..core.state import AgentMessage, MessageType
from ..tools.web_tools import TavilySearchTool, WebScrapeTool
from langchain_core.messages import AIMessage
from langgraph.types import Command


class SearchAgent(Agent):
    """Search agent that uses web search tools to find information."""

    def __init__(self, name: str = "search_agent", tavily_api_key: Optional[str] = None):
        """Initialize search agent.

        Args:
            name: Agent name
            tavily_api_key: Optional Tavily API key
        """
        super().__init__(
            name=name,
            description="Agent specialized in web search using Tavily",
            keywords=["search", "find", "research", "web", "query"],
        )

        # Add search tool
        search_tool = TavilySearchTool(api_key=tavily_api_key)
        self.add_tool(search_tool)

    async def execute(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Execute search based on the message content."""
        try:
            # Extract search query from message
            query = self._extract_search_query(message.content)

            # Perform search
            search_results = await self.use_tool("tavily_search", query=query)

            # Return results as Command with LangGraph-native message
            return Command(
                goto="supervisor" if hasattr(self, 'supervisor') and self.supervisor else "orchestrator",
                update={"messages": [AIMessage(content=f"Search results for '{query}':\n\n{search_results}", name=self.name)]}
            )

        except Exception as e:
            return Command(
                goto="supervisor" if hasattr(self, 'supervisor') and self.supervisor else "orchestrator",
                update={"messages": [AIMessage(content=f"Search failed: {str(e)}", name=self.name)]}
            )

    def _extract_search_query(self, content: str) -> str:
        """Extract search query from message content.

        Args:
            content: Message content

        Returns:
            Extracted search query
        """
        # Simple extraction - in practice this could use LLM reasoning
        content_lower = content.lower()

        # Look for explicit search patterns
        search_patterns = [
            "search for",
            "find information about",
            "look up",
            "research",
            "what is",
            "tell me about",
        ]

        for pattern in search_patterns:
            if pattern in content_lower:
                # Extract everything after the pattern
                start_index = content_lower.find(pattern) + len(pattern)
                return content[start_index:].strip()

        # If no pattern found, use the entire message as query
        return content.strip()


class WebScraperAgent(Agent):
    """Web scraper agent that extracts detailed content from URLs."""

    def __init__(self, name: str = "web_scraper_agent"):
        """Initialize web scraper agent.

        Args:
            name: Agent name
        """
        super().__init__(
            name=name,
            description="Agent specialized in web scraping for detailed content extraction",
            keywords=["scrape", "extract", "webpage", "url", "content", "details"],
        )

        # Add scraping tool
        scraper_tool = WebScrapeTool()
        self.add_tool(scraper_tool)

    async def execute(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Execute web scraping based on the message content."""
        try:
            # Extract URLs from message
            urls = self._extract_urls(message.content)

            if not urls:
                return Command(
                    goto="supervisor" if hasattr(self, 'supervisor') and self.supervisor else "orchestrator",
                    update={"messages": [AIMessage(content="No URLs found in the message to scrape.", name=self.name)]}
                )

            # Scrape the URLs
            scraped_content = await self.use_tool("scrape_webpages", urls=urls)

            # Return results as Command with LangGraph-native message
            return Command(
                goto="supervisor" if hasattr(self, 'supervisor') and self.supervisor else "orchestrator",
                update={"messages": [AIMessage(content=f"Scraped content from {len(urls)} URL(s):\n\n{scraped_content}", name=self.name)]}
            )

        except Exception as e:
            return Command(
                goto="supervisor" if hasattr(self, 'supervisor') and self.supervisor else "orchestrator",
                update={"messages": [AIMessage(content=f"Web scraping failed: {str(e)}", name=self.name)]}
            )

    def _extract_urls(self, content: str) -> list[str]:
        """Extract URLs from message content.

        Args:
            content: Message content

        Returns:
            List of extracted URLs
        """
        import re

        # Simple URL regex pattern
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

        urls = re.findall(url_pattern, content)

        # Also look for common patterns like "scrape these pages: url1, url2"
        # For now, just return the regex matches
        return urls


class ResearchCoordinatorAgent(Agent):
    """Coordinator agent that manages research workflow."""

    def __init__(self, name: str = "research_coordinator"):
        """Initialize research coordinator agent.

        Args:
            name: Agent name
        """
        super().__init__(
            name=name,
            description="Coordinates research tasks between search and scraper agents",
            keywords=["coordinate", "research", "manage", "workflow"],
        )

    async def execute(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Coordinate research workflow."""
        # This agent would typically delegate to other agents in a team
        # For now, provide a coordination response
        return Command(
            goto="supervisor" if hasattr(self, 'supervisor') and self.supervisor else "orchestrator",
            update={"messages": [AIMessage(content=f"Research coordination: Analyzing request '{message.content}' and planning research strategy.", name=self.name)]}
        )