"""
Text processing utilities for AgenticFlow.

Provides advanced text chunking, processing, and analysis capabilities
for memory systems, document handling, and content management.
"""

from .chunking import (
    # Core classes
    TextChunk,
    ChunkMetadata,
    ChunkingConfig,
    ChunkingStrategy,
    ChunkBoundary,
    
    # Chunkers
    TextChunker,
    FixedSizeChunker,
    SemanticChunker,
    SentenceChunker,
    RecursiveChunker,
    MarkdownChunker,
    
    # Factory and manager
    ChunkerFactory,
    ChunkingManager,
    get_chunking_manager,
    
    # Convenience functions
    chunk_text,
    smart_chunk_text
)

__all__ = [
    # Core classes
    "TextChunk",
    "ChunkMetadata", 
    "ChunkingConfig",
    "ChunkingStrategy",
    "ChunkBoundary",
    
    # Chunkers
    "TextChunker",
    "FixedSizeChunker",
    "SemanticChunker",
    "SentenceChunker", 
    "RecursiveChunker",
    "MarkdownChunker",
    
    # Factory and manager
    "ChunkerFactory",
    "ChunkingManager",
    "get_chunking_manager",
    
    # Convenience functions
    "chunk_text",
    "smart_chunk_text"
]
