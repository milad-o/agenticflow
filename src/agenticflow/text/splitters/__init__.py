"""
AgenticFlow Text Splitters
==========================

Comprehensive text splitting system for various content types and use cases.

This module provides:
- Advanced text splitting strategies (recursive, sentence-based, semantic, etc.)
- Content-aware splitters (markdown, code, HTML)
- LangChain integration for seamless interoperability
- Smart splitter selection based on content analysis
- Rich metadata and performance tracking

Basic Usage:
    >>> from agenticflow.text.splitters import create_smart_splitter
    >>> 
    >>> # Automatically choose the best splitter for your content
    >>> splitter = create_smart_splitter("# My Document\n\nThis is content...")
    >>> fragments = await splitter.split_text(text)
    >>> 
    >>> # Or create specific splitters
    >>> from agenticflow.text.splitters import SplitterFactory
    >>> recursive_splitter = SplitterFactory.create_for_content_type(
    ...     ContentType.MARKDOWN, chunk_size=500
    ... )

Advanced Usage:
    >>> from agenticflow.text.splitters import *
    >>> 
    >>> # Create semantic splitter with embeddings
    >>> semantic = SplitterFactory.create_semantic_splitter(
    ...     embedding_model="all-MiniLM-L6-v2",
    ...     semantic_threshold=0.8
    ... )
    >>> 
    >>> # Code-aware splitting
    >>> code_splitter = SplitterFactory.create_for_language(
    ...     LanguageType.PYTHON, chunk_size=800
    ... )
    >>> 
    >>> # LangChain integration
    >>> langchain_splitter = SplitterFactory.create_langchain_splitter(
    ...     "recursive_character", chunk_size=1000
    ... )

Content Types Supported:
- Plain text
- Markdown with structure preservation
- HTML with tag awareness
- Source code with language-specific parsing
- JSON and XML
- Academic papers and documents

Features:
- Smart overlap calculation
- Content type detection
- Language detection
- Readability analysis
- Performance metrics
- Semantic coherence scoring
- Structure preservation
"""

# Core base classes and types
from .base import (
    TextSplitter,
    TextFragment,
    SplitterConfig,
    SplitterType,
    ContentType,
    BoundaryType,
    LanguageType,
    
    # Legacy compatibility
    ChunkingStrategy,
    ChunkBoundary,
    ChunkMetadata,
    TextChunk,
    ChunkingConfig,
    TextChunker,
)

# Splitter strategies
from .strategies import (
    RecursiveSplitter,
    SentenceSplitter,
    MarkdownSplitter,
    CodeSplitter,
    TokenSplitter,
    SemanticSplitter,
)

# Factory and utilities
from .factory import (
    SplitterFactory,
    create_splitter,
    create_smart_splitter,
    get_available_splitters,
)

# Management system
from .manager import (
    SplitterManager,
    SplitterPerformanceMetrics,
    SplitterCache,
    get_splitter_manager,
    initialize_manager,
    split_text as managed_split_text,
    smart_split_text,
    get_manager_stats,
    clear_manager_cache,
)

# LangChain integration (if available)
try:
    from .langchain_adapters import (
        LangChainSplitterAdapter,
        DocumentAwareSplitter,
        create_recursive_character_splitter,
        create_character_splitter,
        create_token_splitter as create_langchain_token_splitter,
        create_markdown_header_splitter,
        create_html_header_splitter,
        create_python_code_splitter,
        create_javascript_code_splitter,
        create_splitter_for_content_type,
    )
    LANGCHAIN_AVAILABLE = True
except ImportError:
    # Set to None for graceful degradation
    LangChainSplitterAdapter = None
    DocumentAwareSplitter = None
    create_recursive_character_splitter = None
    create_character_splitter = None
    create_langchain_token_splitter = None
    create_markdown_header_splitter = None
    create_html_header_splitter = None
    create_python_code_splitter = None
    create_javascript_code_splitter = None
    create_splitter_for_content_type = None
    LANGCHAIN_AVAILABLE = False


# Version info
__version__ = "1.0.0"
__author__ = "AgenticFlow Team"


# Public API
__all__ = [
    # Core types and enums
    "TextSplitter",
    "TextFragment", 
    "SplitterConfig",
    "SplitterType",
    "ContentType",
    "BoundaryType",
    "LanguageType",
    
    # Legacy compatibility
    "ChunkingStrategy",
    "ChunkBoundary", 
    "ChunkMetadata",
    "TextChunk",
    "ChunkingConfig",
    "TextChunker",
    
    # Concrete splitter implementations
    "RecursiveSplitter",
    "SentenceSplitter",
    "MarkdownSplitter", 
    "CodeSplitter",
    "TokenSplitter",
    "SemanticSplitter",
    
    # Factory and creation utilities
    "SplitterFactory",
    "create_splitter",
    "create_smart_splitter",
    "get_available_splitters",
    
    # Management system
    "SplitterManager",
    "SplitterPerformanceMetrics",
    "SplitterCache",
    "get_splitter_manager",
    "initialize_manager",
    "managed_split_text",
    "smart_split_text",
    "get_manager_stats",
    "clear_manager_cache",
    
    # LangChain integration
    "LangChainSplitterAdapter",
    "DocumentAwareSplitter",
    "create_recursive_character_splitter",
    "create_character_splitter",
    "create_langchain_token_splitter",
    "create_markdown_header_splitter", 
    "create_html_header_splitter",
    "create_python_code_splitter",
    "create_javascript_code_splitter",
    "create_splitter_for_content_type",
    
    # Module info
    "LANGCHAIN_AVAILABLE",
]


# Helper functions for common use cases
def split_text(
    text: str,
    splitter_type: SplitterType = SplitterType.RECURSIVE,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    **kwargs
) -> list:
    """
    Quick text splitting function.
    
    Args:
        text: Text to split
        splitter_type: Type of splitter to use
        chunk_size: Target chunk size
        chunk_overlap: Overlap between chunks
        **kwargs: Additional configuration
        
    Returns:
        List of text fragments
    """
    splitter = create_splitter(
        splitter_type=splitter_type,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        **kwargs
    )
    
    # Run async function in sync context
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        # If we're already in an async context, we can't use run_until_complete
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, splitter.split_text(text))
            return future.result()
    except RuntimeError:
        # No running loop, safe to create new one
        return asyncio.run(splitter.split_text(text))


def smart_split(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    **kwargs
) -> list:
    """
    Automatically choose and apply the best splitter for the content.
    
    Args:
        text: Text to split
        chunk_size: Target chunk size  
        chunk_overlap: Overlap between chunks
        **kwargs: Additional configuration
        
    Returns:
        List of text fragments
    """
    splitter = create_smart_splitter(
        text_sample=text[:2000],  # Sample for analysis
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        **kwargs
    )
    
    # Run async function in sync context
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        # If we're already in an async context, we can't use run_until_complete
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, splitter.split_text(text))
            return future.result()
    except RuntimeError:
        # No running loop, safe to create new one
        return asyncio.run(splitter.split_text(text))


def get_splitter_info() -> dict:
    """
    Get information about available splitters and capabilities.
    
    Returns:
        Dictionary with splitter information
    """
    return {
        "version": __version__,
        "available_splitters": [s.value for s in get_available_splitters()],
        "supported_content_types": [ct.value for ct in ContentType],
        "supported_languages": [lang.value for lang in LanguageType],
        "langchain_available": LANGCHAIN_AVAILABLE,
        "features": {
            "semantic_splitting": True,
            "code_awareness": True,
            "structure_preservation": True,
            "smart_overlap": True,
            "content_detection": True,
            "performance_metrics": True,
            "async_support": True,
        }
    }