"""Simple tools for agents."""

import os
from typing import Annotated
from langchain_core.tools import tool

@tool
def create_file(
    content: Annotated[str, "Content to write to the file"],
    filename: Annotated[str, "Name of the file to create"]
) -> str:
    """Create a file with the given content."""
    try:
        # Ensure artifacts directory exists inside examples
        artifacts_dir = "examples/artifacts"
        os.makedirs(artifacts_dir, exist_ok=True)
        
        # Create file in artifacts directory
        filepath = os.path.join(artifacts_dir, filename)
        with open(filepath, "w") as f:
            f.write(content)
        return f"✅ Created file '{filepath}' with content: '{content[:100]}...'"
    except Exception as e:
        return f"❌ Error creating file: {e}"

@tool
def search_web(
    query: Annotated[str, "Search query for the web"]
) -> str:
    """Search the web for information."""
    try:
        from langchain_tavily import TavilySearch
        search = TavilySearch(max_results=3)
        results = search.invoke(query)
        return f"🔍 Web search results for '{query}':\n{results}"
    except Exception as e:
        return f"❌ Error searching web: {e}"
