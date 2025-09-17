"""
Factory for creating text chunking strategies.
"""

from typing import Optional

import structlog
from langchain_core.embeddings import Embeddings

from .base import TextChunker, ChunkingConfig, ChunkingStrategy
from .strategies import (
    FixedSizeChunker,
    SentenceChunker,
    RecursiveChunker,
    MarkdownChunker,
    SemanticChunker
)

logger = structlog.get_logger(__name__)


class ChunkerFactory:
    """Factory for creating text chunkers based on strategy."""
    
    @staticmethod
    def create_chunker(
        config: ChunkingConfig, 
        embeddings: Optional[Embeddings] = None
    ) -> TextChunker:
        """Create a chunker based on the specified strategy."""
        
        strategy_map = {
            ChunkingStrategy.FIXED_SIZE: FixedSizeChunker,
            ChunkingStrategy.SENTENCE: SentenceChunker,
            ChunkingStrategy.RECURSIVE: RecursiveChunker,
            ChunkingStrategy.MARKDOWN: MarkdownChunker,
            ChunkingStrategy.SEMANTIC: lambda c: SemanticChunker(c, embeddings),
            ChunkingStrategy.TOKEN: RecursiveChunker,  # Use recursive for token-based for now
        }
        
        if config.strategy not in strategy_map:
            logger.warning(f"Unknown chunking strategy: {config.strategy}, falling back to recursive")
            return RecursiveChunker(config)
        
        chunker_class = strategy_map[config.strategy]
        
        # Handle strategies that need special initialization
        if config.strategy == ChunkingStrategy.SEMANTIC:
            return chunker_class(config)
        else:
            return chunker_class(config)
    
    @staticmethod
    def get_available_strategies() -> list[ChunkingStrategy]:
        """Get list of available chunking strategies."""
        return list(ChunkingStrategy)
    
    @staticmethod
    def get_strategy_description(strategy: ChunkingStrategy) -> str:
        """Get description of a chunking strategy."""
        descriptions = {
            ChunkingStrategy.FIXED_SIZE: "Split text into fixed-size chunks with optional overlap",
            ChunkingStrategy.SENTENCE: "Split text at sentence boundaries, grouping into chunks",
            ChunkingStrategy.RECURSIVE: "Recursively split using hierarchical separators (paragraphs, sentences, etc.)",
            ChunkingStrategy.MARKDOWN: "Structure-aware splitting that preserves markdown sections and headers",
            ChunkingStrategy.SEMANTIC: "AI-powered semantic boundary detection using embeddings",
            ChunkingStrategy.TOKEN: "Split based on token count (currently uses recursive implementation)",
        }
        
        return descriptions.get(strategy, "Unknown strategy")
    
    @staticmethod
    def recommend_strategy(
        text: str, 
        has_embeddings: bool = False,
        content_type: str = "text"
    ) -> ChunkingStrategy:
        """Recommend optimal chunking strategy based on text characteristics."""
        
        # Check for markdown
        if "# " in text or "## " in text:
            return ChunkingStrategy.MARKDOWN
        
        # Check if semantic chunking is available and beneficial
        if has_embeddings and len(text) > 2000:
            return ChunkingStrategy.SEMANTIC
        
        # For structured content, use recursive
        if "\n\n" in text or len(text.split("\n")) > 10:
            return ChunkingStrategy.RECURSIVE
        
        # For simple text, use sentence-based
        if "." in text and len(text) > 500:
            return ChunkingStrategy.SENTENCE
        
        # Default to fixed size for everything else
        return ChunkingStrategy.FIXED_SIZE