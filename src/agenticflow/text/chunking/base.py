"""
Base classes and types for text chunking system.
"""

import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)


class ChunkingStrategy(str, Enum):
    """Available chunking strategies."""
    FIXED_SIZE = "fixed_size"
    SENTENCE = "sentence"
    RECURSIVE = "recursive"
    SEMANTIC = "semantic"
    TOKEN = "token"
    MARKDOWN = "markdown"


class ChunkBoundary(str, Enum):
    """Chunk boundary types."""
    CHARACTER = "character"
    WORD = "word"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    SECTION = "section"


@dataclass
class ChunkMetadata:
    """Metadata for text chunks."""
    chunk_id: str
    source_text_id: Optional[str] = None
    chunk_index: int = 0
    total_chunks: int = 1
    start_position: int = 0
    end_position: int = 0
    word_count: int = 0
    character_count: int = 0
    overlap_start: int = 0
    overlap_end: int = 0
    boundary_type: ChunkBoundary = ChunkBoundary.CHARACTER
    semantic_score: Optional[float] = None
    language: Optional[str] = None
    content_type: str = "text"
    headers: Optional[Dict[str, str]] = None
    custom_metadata: Optional[Dict[str, Any]] = None


@dataclass
class TextChunk:
    """A chunk of text with metadata and optional embedding."""
    content: str
    metadata: ChunkMetadata
    embedding: Optional[List[float]] = None
    
    def __len__(self) -> int:
        """Return character length of chunk."""
        return len(self.content)
    
    def word_count(self) -> int:
        """Return word count of chunk."""
        return len(self.content.split())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary."""
        return {
            "content": self.content,
            "metadata": {
                "chunk_id": self.metadata.chunk_id,
                "source_text_id": self.metadata.source_text_id,
                "chunk_index": self.metadata.chunk_index,
                "total_chunks": self.metadata.total_chunks,
                "start_position": self.metadata.start_position,
                "end_position": self.metadata.end_position,
                "word_count": self.metadata.word_count,
                "character_count": self.metadata.character_count,
                "overlap_start": self.metadata.overlap_start,
                "overlap_end": self.metadata.overlap_end,
                "boundary_type": self.metadata.boundary_type,
                "semantic_score": self.metadata.semantic_score,
                "language": self.metadata.language,
                "content_type": self.metadata.content_type,
                "headers": self.metadata.headers,
                "custom_metadata": self.metadata.custom_metadata,
            },
            "embedding": self.embedding,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TextChunk":
        """Create chunk from dictionary."""
        metadata = ChunkMetadata(**data["metadata"])
        return cls(
            content=data["content"],
            metadata=metadata,
            embedding=data.get("embedding")
        )


@dataclass
class ChunkingConfig:
    """Configuration for text chunking."""
    strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE
    chunk_size: int = 1000
    chunk_overlap: int = 200
    boundary_type: ChunkBoundary = ChunkBoundary.WORD
    
    # Semantic chunking settings
    semantic_threshold: float = 0.8
    min_chunk_size: int = 100
    max_chunk_size: int = 2000
    
    # Token-based settings
    tokens_per_chunk: int = 500
    model_name: Optional[str] = None
    
    # Content-specific settings
    strip_whitespace: bool = True
    preserve_structure: bool = True
    include_headers: bool = True
    
    # Overlap settings
    overlap_method: str = "symmetric"  # symmetric, forward, backward
    smart_overlap: bool = True  # Adjust overlap at sentence boundaries
    
    # Custom settings
    custom_separators: Optional[List[str]] = None
    custom_regex_patterns: Optional[List[str]] = None


class TextChunker(ABC):
    """Abstract base class for text chunking."""
    
    def __init__(self, config: ChunkingConfig):
        """Initialize chunker with configuration."""
        self.config = config
        self.logger = logger.bind(chunker=self.__class__.__name__)
    
    @abstractmethod
    async def chunk_text(
        self, 
        text: str, 
        text_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[TextChunk]:
        """Chunk text into smaller pieces."""
        pass
    
    def _create_chunk_id(self, text_id: Optional[str], index: int) -> str:
        """Create unique chunk ID."""
        if text_id:
            return f"{text_id}_chunk_{index}"
        return f"chunk_{index}_{uuid.uuid4().hex[:8]}"
    
    def _calculate_overlap(
        self, 
        current_chunk: str, 
        previous_chunk: Optional[str], 
        next_chunk: Optional[str]
    ) -> Tuple[int, int]:
        """Calculate overlap positions for a chunk."""
        overlap_start = 0
        overlap_end = 0
        
        if self.config.chunk_overlap > 0:
            # Forward overlap with previous chunk
            if previous_chunk:
                overlap_text = current_chunk[:self.config.chunk_overlap]
                if overlap_text in previous_chunk:
                    overlap_start = len(overlap_text)
            
            # Backward overlap with next chunk
            if next_chunk:
                overlap_text = current_chunk[-self.config.chunk_overlap:]
                if overlap_text in next_chunk:
                    overlap_end = len(overlap_text)
        
        return overlap_start, overlap_end
    
    def _detect_language(self, text: str) -> Optional[str]:
        """Detect text language (basic implementation)."""
        # Simple language detection based on common words
        # In production, you might use langdetect or similar
        english_indicators = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to']
        words = text.lower().split()[:50]  # Check first 50 words
        
        english_count = sum(1 for word in words if word in english_indicators)
        if english_count >= 3:
            return "en"
        return None
    
    def _update_chunk_totals(self, chunks: List[TextChunk]) -> List[TextChunk]:
        """Update total_chunks metadata for all chunks."""
        total = len(chunks)
        for chunk in chunks:
            chunk.metadata.total_chunks = total
        return chunks