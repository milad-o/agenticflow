"""
Text processing utilities for AgenticFlow.

Provides comprehensive text splitting, processing, and analysis capabilities
for memory systems, document handling, and content management.

Features:
- Advanced text splitters for various content types
- LangChain integration for seamless interoperability  
- Smart content detection and splitter selection
- Code-aware splitting with language detection
- Semantic splitting with embeddings
- Performance metrics and optimization
"""

# New comprehensive splitters module
from .splitters import (
    # Core types and classes
    TextSplitter,
    TextFragment,
    SplitterConfig,
    SplitterType,
    ContentType,
    BoundaryType,
    LanguageType,
    
    # Splitter implementations
    RecursiveSplitter,
    SentenceSplitter,
    MarkdownSplitter,
    CodeSplitter,
    TokenSplitter,
    SemanticSplitter,
    
    # Factory and utilities
    SplitterFactory,
    create_splitter,
    create_smart_splitter,
    get_available_splitters,
    
    # Management system
    SplitterManager,
    get_splitter_manager,
    initialize_manager,
    managed_split_text,
    smart_split_text,
    get_manager_stats,
    clear_manager_cache,
    
    # Convenience functions
    split_text,
    smart_split,
    get_splitter_info,
    
    # LangChain integration (if available)
    LangChainSplitterAdapter,
    create_recursive_character_splitter,
    create_langchain_token_splitter,
    LANGCHAIN_AVAILABLE,
    
    # Legacy compatibility aliases
    TextChunk,
    ChunkMetadata,
    ChunkingConfig,
    ChunkingStrategy,
    ChunkBoundary,
    TextChunker,
)

# Note: Legacy chunking has been replaced with the comprehensive splitters module
# All chunking functionality is now available through the splitters interface

__all__ = [
    # Core types and classes
    "TextSplitter",
    "TextFragment",
    "SplitterConfig",
    "SplitterType",
    "ContentType",
    "BoundaryType",
    "LanguageType",
    
    # Splitter implementations
    "RecursiveSplitter",
    "SentenceSplitter", 
    "MarkdownSplitter",
    "CodeSplitter",
    "TokenSplitter",
    "SemanticSplitter",
    
    # Factory and utilities
    "SplitterFactory",
    "create_splitter",
    "create_smart_splitter",
    "get_available_splitters",
    
    # Management system
    "SplitterManager",
    "get_splitter_manager",
    "initialize_manager",
    "managed_split_text",
    "smart_split_text",
    "get_manager_stats",
    "clear_manager_cache",
    
    # Convenience functions
    "split_text",
    "smart_split",
    "get_splitter_info",
    
    # LangChain integration
    "LangChainSplitterAdapter",
    "create_recursive_character_splitter",
    "create_langchain_token_splitter",
    "LANGCHAIN_AVAILABLE",
    
    # Legacy compatibility (mapped to new splitters)
    "TextChunk",  # Alias for TextFragment
    "ChunkMetadata",  # Dict[str, Any]
    "ChunkingConfig",  # Alias for SplitterConfig
    "ChunkingStrategy",  # Alias for SplitterType
    "ChunkBoundary",  # Alias for BoundaryType
    "TextChunker",  # Alias for TextSplitter
]
