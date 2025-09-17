"""
High-level chunking manager and interface.
"""

import re
from typing import Any, Dict, List, Optional

import structlog
from langchain_core.embeddings import Embeddings

from .base import TextChunk, ChunkingConfig, ChunkingStrategy
from .factory import ChunkerFactory

logger = structlog.get_logger(__name__)


class ChunkingManager:
    """High-level manager for text chunking operations."""
    
    def __init__(
        self, 
        config: Optional[ChunkingConfig] = None, 
        embeddings: Optional[Embeddings] = None
    ):
        """Initialize chunking manager."""
        self.config = config or ChunkingConfig()
        self.embeddings = embeddings
        self.logger = logger.bind(component="chunking_manager")
    
    async def chunk_text(
        self,
        text: str,
        strategy: Optional[ChunkingStrategy] = None,
        config: Optional[ChunkingConfig] = None,
        text_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[TextChunk]:
        """Chunk text using specified or default strategy."""
        
        # Use provided config or default
        chunk_config = config or self.config
        
        # Override strategy if provided
        if strategy:
            chunk_config.strategy = strategy
        
        # Create chunker
        chunker = ChunkerFactory.create_chunker(chunk_config, self.embeddings)
        
        # Chunk text
        chunks = await chunker.chunk_text(text, text_id, metadata)
        
        self.logger.info(
            f"Chunked text into {len(chunks)} pieces using {chunk_config.strategy.value} strategy"
        )
        
        return chunks
    
    async def chunk_with_embeddings(
        self,
        text: str,
        strategy: Optional[ChunkingStrategy] = None,
        config: Optional[ChunkingConfig] = None,
        text_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[TextChunk]:
        """Chunk text and generate embeddings for each chunk."""
        chunks = await self.chunk_text(text, strategy, config, text_id, metadata)
        
        if not self.embeddings or not chunks:
            return chunks
        
        # Generate embeddings for all chunks
        try:
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = await self.embeddings.aembed_documents(chunk_texts)
            
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
                
            self.logger.debug(f"Generated embeddings for {len(chunks)} chunks")
        
        except Exception as e:
            self.logger.warning(f"Failed to generate embeddings for chunks: {e}")
        
        return chunks
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze text to suggest optimal chunking strategy."""
        analysis = {
            "character_count": len(text),
            "word_count": len(text.split()),
            "line_count": len(text.split('\n')),
            "paragraph_count": len([p for p in text.split('\n\n') if p.strip()]),
            "has_markdown_headers": bool(re.search(r'^#{1,6}\s+', text, re.MULTILINE)),
            "has_html_tags": bool(re.search(r'<[^>]+>', text)),
            "average_sentence_length": 0,
            "suggested_strategy": ChunkingStrategy.RECURSIVE,
            "suggested_chunk_size": 1000,
        }
        
        # Estimate sentence count and average length
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if sentences:
            analysis["sentence_count"] = len(sentences)
            analysis["average_sentence_length"] = sum(len(s) for s in sentences) / len(sentences)
        
        # Suggest strategy based on content
        analysis["suggested_strategy"] = ChunkerFactory.recommend_strategy(
            text, 
            has_embeddings=self.embeddings is not None
        )
        
        # Adjust chunk size based on content
        if analysis["average_sentence_length"] > 150:
            analysis["suggested_chunk_size"] = 1500
        elif analysis["character_count"] > 10000:
            analysis["suggested_chunk_size"] = 1200
        elif analysis["character_count"] < 1000:
            analysis["suggested_chunk_size"] = 500
        
        return analysis
    
    async def smart_chunk(
        self,
        text: str,
        text_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_embeddings: bool = True
    ) -> List[TextChunk]:
        """Smart chunking that analyzes text and chooses optimal strategy."""
        
        # Analyze text to determine best strategy
        analysis = self.analyze_text(text)
        suggested_strategy = analysis["suggested_strategy"]
        suggested_chunk_size = analysis["suggested_chunk_size"]
        
        # Create optimized config
        optimized_config = ChunkingConfig(
            strategy=suggested_strategy,
            chunk_size=suggested_chunk_size,
            chunk_overlap=min(200, suggested_chunk_size // 5),  # 20% overlap max
            min_chunk_size=max(100, suggested_chunk_size // 10),
            max_chunk_size=suggested_chunk_size * 2
        )
        
        self.logger.info(
            f"Smart chunking selected {suggested_strategy.value} strategy with {suggested_chunk_size} chunk size"
        )
        
        # Chunk with embeddings if available and requested
        if auto_embeddings and self.embeddings:
            return await self.chunk_with_embeddings(
                text, config=optimized_config, text_id=text_id, metadata=metadata
            )
        else:
            return await self.chunk_text(
                text, config=optimized_config, text_id=text_id, metadata=metadata
            )
    
    def get_chunking_stats(self, chunks: List[TextChunk]) -> Dict[str, Any]:
        """Get statistics about chunked text."""
        if not chunks:
            return {"total_chunks": 0}
        
        chunk_lengths = [len(chunk.content) for chunk in chunks]
        word_counts = [chunk.word_count() for chunk in chunks]
        
        stats = {
            "total_chunks": len(chunks),
            "total_characters": sum(chunk_lengths),
            "total_words": sum(word_counts),
            "average_chunk_size": sum(chunk_lengths) / len(chunks),
            "min_chunk_size": min(chunk_lengths),
            "max_chunk_size": max(chunk_lengths),
            "average_word_count": sum(word_counts) / len(chunks),
            "chunks_with_embeddings": sum(1 for chunk in chunks if chunk.embedding is not None),
            "embedding_coverage": sum(1 for chunk in chunks if chunk.embedding is not None) / len(chunks),
            "strategies_used": list(set(chunk.metadata.boundary_type for chunk in chunks)),
            "languages_detected": list(set(chunk.metadata.language for chunk in chunks if chunk.metadata.language))
        }
        
        return stats


# Global chunking manager instance
_global_chunking_manager: Optional[ChunkingManager] = None


def get_chunking_manager(
    config: Optional[ChunkingConfig] = None,
    embeddings: Optional[Embeddings] = None
) -> ChunkingManager:
    """Get global chunking manager instance."""
    global _global_chunking_manager
    
    if _global_chunking_manager is None or config or embeddings:
        _global_chunking_manager = ChunkingManager(config, embeddings)
    
    return _global_chunking_manager


# Convenience functions
async def chunk_text(
    text: str,
    strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    text_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    **kwargs
) -> List[TextChunk]:
    """Convenience function for quick text chunking."""
    config = ChunkingConfig(
        strategy=strategy,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        **kwargs
    )
    
    manager = get_chunking_manager(config)
    return await manager.chunk_text(text, text_id=text_id, metadata=metadata)


async def smart_chunk_text(
    text: str,
    text_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    embeddings: Optional[Embeddings] = None
) -> List[TextChunk]:
    """Convenience function for smart text chunking with automatic strategy selection."""
    manager = get_chunking_manager(embeddings=embeddings)
    return await manager.smart_chunk(text, text_id, metadata)