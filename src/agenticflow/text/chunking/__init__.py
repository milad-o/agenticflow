"""Text chunking utilities for AgenticFlow."""

# Import core components
from .base import (
    ChunkingStrategy,
    ChunkBoundary,
    ChunkMetadata,
    TextChunk,
    ChunkingConfig,
    TextChunker
)

# Import concrete strategies
from .strategies import (
    FixedSizeChunker,
    SentenceChunker,
    RecursiveChunker,
    MarkdownChunker,
    SemanticChunker
)

# Import factory and manager
from .factory import ChunkerFactory
from .manager import (
    ChunkingManager,
    get_chunking_manager,
    chunk_text,
    smart_chunk_text
)

__all__ = [
    # Core types
    'ChunkingStrategy',
    'ChunkBoundary',
    'ChunkMetadata',
    'TextChunk',
    'ChunkingConfig',
    
    # Base classes
    'TextChunker',
    
    # Concrete chunkers
    'FixedSizeChunker',
    'SentenceChunker',
    'RecursiveChunker',
    'MarkdownChunker',
    'SemanticChunker',
    
    # Factory and management
    'ChunkerFactory',
    'ChunkingManager',
    'get_chunking_manager',
    
    # Convenience functions
    'chunk_text',
    'smart_chunk_text'
]