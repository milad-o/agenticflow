"""
Concrete implementations of different chunking strategies.
"""

import re
from typing import Any, Dict, List, Optional

from langchain_core.embeddings import Embeddings

from .base import TextChunker, TextChunk, ChunkMetadata, ChunkBoundary, ChunkingConfig


class FixedSizeChunker(TextChunker):
    """Fixed-size text chunker with configurable overlap."""
    
    async def chunk_text(
        self, 
        text: str, 
        text_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[TextChunk]:
        """Chunk text into fixed-size pieces."""
        if not text:
            return []
        
        chunks = []
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap
        
        # Calculate step size (chunk_size - overlap)
        step = chunk_size - overlap if overlap < chunk_size else chunk_size
        
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_content = text[start:end]
            
            # Smart boundary adjustment
            if self.config.smart_overlap and end < len(text):
                # Try to end at sentence boundary
                last_period = chunk_content.rfind('.')
                last_newline = chunk_content.rfind('\n')
                boundary_pos = max(last_period, last_newline)
                
                if boundary_pos > chunk_size * 0.7:  # Don't shrink too much
                    end = start + boundary_pos + 1
                    chunk_content = text[start:end]
            
            # Create chunk metadata
            chunk_metadata = ChunkMetadata(
                chunk_id=self._create_chunk_id(text_id, chunk_index),
                source_text_id=text_id,
                chunk_index=chunk_index,
                start_position=start,
                end_position=end,
                word_count=len(chunk_content.split()),
                character_count=len(chunk_content),
                boundary_type=self.config.boundary_type,
                language=self._detect_language(chunk_content),
                custom_metadata=metadata
            )
            
            # Create chunk
            chunk = TextChunk(
                content=chunk_content.strip() if self.config.strip_whitespace else chunk_content,
                metadata=chunk_metadata
            )
            chunks.append(chunk)
            
            # Move to next chunk
            start += step
            chunk_index += 1
            
            # Break if we've processed all text
            if end >= len(text):
                break
        
        self.logger.debug(f"Created {len(chunks)} fixed-size chunks from text of {len(text)} characters")
        return self._update_chunk_totals(chunks)


class SentenceChunker(TextChunker):
    """Sentence-based chunker that groups sentences into chunks."""
    
    async def chunk_text(
        self, 
        text: str, 
        text_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[TextChunk]:
        """Chunk text based on sentence boundaries."""
        if not text:
            return []
        
        # Split into sentences using regex
        sentences = self._split_sentences(text)
        if not sentences:
            return []
        
        chunks = []
        chunk_index = 0
        current_chunk = ""
        current_start = 0
        sentence_start = 0
        
        for i, sentence in enumerate(sentences):
            # Check if adding this sentence would exceed chunk size
            potential_chunk = current_chunk + sentence
            
            if len(potential_chunk) > self.config.chunk_size and current_chunk:
                # Create chunk from current content
                chunk_metadata = ChunkMetadata(
                    chunk_id=self._create_chunk_id(text_id, chunk_index),
                    source_text_id=text_id,
                    chunk_index=chunk_index,
                    start_position=current_start,
                    end_position=current_start + len(current_chunk),
                    word_count=len(current_chunk.split()),
                    character_count=len(current_chunk),
                    boundary_type=ChunkBoundary.SENTENCE,
                    language=self._detect_language(current_chunk),
                    custom_metadata=metadata
                )
                
                chunk = TextChunk(
                    content=current_chunk.strip() if self.config.strip_whitespace else current_chunk,
                    metadata=chunk_metadata
                )
                chunks.append(chunk)
                
                # Start new chunk
                chunk_index += 1
                current_start = sentence_start
                current_chunk = sentence
            else:
                current_chunk = potential_chunk
            
            # Update sentence position for next iteration
            if i == 0:
                sentence_start = len(sentence)
            else:
                sentence_start += len(sentence)
        
        # Add remaining content as final chunk
        if current_chunk:
            chunk_metadata = ChunkMetadata(
                chunk_id=self._create_chunk_id(text_id, chunk_index),
                source_text_id=text_id,
                chunk_index=chunk_index,
                start_position=current_start,
                end_position=current_start + len(current_chunk),
                word_count=len(current_chunk.split()),
                character_count=len(current_chunk),
                boundary_type=ChunkBoundary.SENTENCE,
                language=self._detect_language(current_chunk),
                custom_metadata=metadata
            )
            
            chunk = TextChunk(
                content=current_chunk.strip() if self.config.strip_whitespace else current_chunk,
                metadata=chunk_metadata
            )
            chunks.append(chunk)
        
        self.logger.debug(f"Created {len(chunks)} sentence-based chunks from {len(sentences)} sentences")
        return self._update_chunk_totals(chunks)
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting - can be enhanced with NLTK or spaCy
        sentence_endings = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')
        sentences = sentence_endings.split(text)
        return [s.strip() for s in sentences if s.strip()]


class RecursiveChunker(TextChunker):
    """Recursive chunker that tries different separators hierarchically."""
    
    def __init__(self, config: ChunkingConfig):
        super().__init__(config)
        self.separators = config.custom_separators or [
            "\n\n", "\n", " ", ""
        ]
    
    async def chunk_text(
        self, 
        text: str, 
        text_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[TextChunk]:
        """Recursively chunk text using hierarchical separators."""
        if not text:
            return []
        
        chunks = self._recursive_split(text, self.separators)
        
        # Convert to TextChunk objects
        result_chunks = []
        for i, chunk_text in enumerate(chunks):
            chunk_metadata = ChunkMetadata(
                chunk_id=self._create_chunk_id(text_id, i),
                source_text_id=text_id,
                chunk_index=i,
                start_position=text.find(chunk_text),
                end_position=text.find(chunk_text) + len(chunk_text),
                word_count=len(chunk_text.split()),
                character_count=len(chunk_text),
                boundary_type=ChunkBoundary.CHARACTER,
                language=self._detect_language(chunk_text),
                custom_metadata=metadata
            )
            
            chunk = TextChunk(
                content=chunk_text.strip() if self.config.strip_whitespace else chunk_text,
                metadata=chunk_metadata
            )
            result_chunks.append(chunk)
        
        self.logger.debug(f"Created {len(result_chunks)} recursive chunks")
        return self._update_chunk_totals(result_chunks)
    
    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        """Recursively split text using hierarchical separators."""
        if not separators:
            return [text] if text else []
        
        separator = separators[0]
        remaining_separators = separators[1:]
        
        if separator == "":
            # Character-level splitting as last resort
            if len(text) <= self.config.chunk_size:
                return [text]
            
            chunks = []
            for i in range(0, len(text), self.config.chunk_size):
                chunks.append(text[i:i + self.config.chunk_size])
            return chunks
        
        # Split by current separator
        splits = text.split(separator)
        chunks = []
        current_chunk = ""
        
        for split in splits:
            if len(current_chunk + separator + split) <= self.config.chunk_size:
                if current_chunk:
                    current_chunk += separator + split
                else:
                    current_chunk = split
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                
                # If single split is still too large, recurse
                if len(split) > self.config.chunk_size:
                    chunks.extend(self._recursive_split(split, remaining_separators))
                    current_chunk = ""
                else:
                    current_chunk = split
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks


class MarkdownChunker(TextChunker):
    """Markdown-aware chunker that respects document structure."""
    
    async def chunk_text(
        self, 
        text: str, 
        text_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[TextChunk]:
        """Chunk markdown text by structure."""
        if not text:
            return []
        
        sections = self._parse_markdown_sections(text)
        chunks = []
        
        for i, (header, content, level) in enumerate(sections):
            if not content.strip():
                continue
            
            # Include header in chunk if configured
            chunk_content = content
            if self.config.include_headers and header:
                chunk_content = f"{header}\n{content}"
            
            # Split large sections further if needed
            if len(chunk_content) > self.config.max_chunk_size:
                sub_chunks = await self._split_large_section(chunk_content, text_id, i, metadata)
                chunks.extend(sub_chunks)
            else:
                chunk_metadata = ChunkMetadata(
                    chunk_id=self._create_chunk_id(text_id, i),
                    source_text_id=text_id,
                    chunk_index=i,
                    start_position=text.find(content),
                    end_position=text.find(content) + len(content),
                    word_count=len(chunk_content.split()),
                    character_count=len(chunk_content),
                    boundary_type=ChunkBoundary.SECTION,
                    language=self._detect_language(chunk_content),
                    headers={"level": level, "header": header} if header else None,
                    custom_metadata=metadata
                )
                
                chunk = TextChunk(
                    content=chunk_content.strip() if self.config.strip_whitespace else chunk_content,
                    metadata=chunk_metadata
                )
                chunks.append(chunk)
        
        self.logger.debug(f"Created {len(chunks)} markdown chunks")
        return self._update_chunk_totals(chunks)
    
    def _parse_markdown_sections(self, text: str) -> List[tuple]:
        """Parse markdown into sections with headers."""
        lines = text.split('\n')
        sections = []
        current_header = None
        current_content = []
        current_level = 0
        
        for line in lines:
            # Check for markdown headers
            if line.startswith('#'):
                # Save previous section
                if current_content:
                    sections.append((
                        current_header, 
                        '\n'.join(current_content), 
                        current_level
                    ))
                
                # Start new section
                current_level = len(line) - len(line.lstrip('#'))
                current_header = line.strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Add final section
        if current_content:
            sections.append((
                current_header, 
                '\n'.join(current_content), 
                current_level
            ))
        
        return sections
    
    async def _split_large_section(
        self, 
        content: str, 
        text_id: Optional[str], 
        base_index: int,
        metadata: Optional[Dict[str, Any]]
    ) -> List[TextChunk]:
        """Split large markdown sections into smaller chunks."""
        # Use recursive chunker for large sections
        recursive_chunker = RecursiveChunker(self.config)
        return await recursive_chunker.chunk_text(content, f"{text_id}_sec_{base_index}", metadata)


class SemanticChunker(TextChunker):
    """Semantic chunker using embeddings to determine chunk boundaries."""
    
    def __init__(self, config: ChunkingConfig, embeddings: Optional[Embeddings] = None):
        super().__init__(config)
        self.embeddings = embeddings
    
    async def chunk_text(
        self, 
        text: str, 
        text_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[TextChunk]:
        """Chunk text using semantic similarity."""
        if not self.embeddings:
            # Fallback to sentence chunker if no embeddings available
            self.logger.warning("No embeddings available for semantic chunking, falling back to sentence chunker")
            sentence_chunker = SentenceChunker(self.config)
            return await sentence_chunker.chunk_text(text, text_id, metadata)
        
        if not text:
            return []
        
        # Split into sentences first
        sentences = self._split_sentences(text)
        if len(sentences) <= 1:
            # Single sentence, return as is
            chunk_metadata = ChunkMetadata(
                chunk_id=self._create_chunk_id(text_id, 0),
                source_text_id=text_id,
                chunk_index=0,
                start_position=0,
                end_position=len(text),
                word_count=len(text.split()),
                character_count=len(text),
                boundary_type=ChunkBoundary.SENTENCE,
                language=self._detect_language(text),
                custom_metadata=metadata
            )
            
            chunk = TextChunk(content=text, metadata=chunk_metadata)
            return [chunk]
        
        try:
            # Generate embeddings for sentences
            embeddings = await self.embeddings.aembed_documents(sentences)
            
            # Find semantic boundaries
            boundaries = self._find_semantic_boundaries(sentences, embeddings)
            
            # Create chunks based on boundaries
            chunks = []
            for i, (start, end) in enumerate(boundaries):
                chunk_sentences = sentences[start:end]
                chunk_content = " ".join(chunk_sentences)
                
                chunk_metadata = ChunkMetadata(
                    chunk_id=self._create_chunk_id(text_id, i),
                    source_text_id=text_id,
                    chunk_index=i,
                    start_position=text.find(chunk_content),
                    end_position=text.find(chunk_content) + len(chunk_content),
                    word_count=len(chunk_content.split()),
                    character_count=len(chunk_content),
                    boundary_type=ChunkBoundary.SENTENCE,
                    language=self._detect_language(chunk_content),
                    custom_metadata=metadata
                )
                
                chunk = TextChunk(
                    content=chunk_content.strip() if self.config.strip_whitespace else chunk_content,
                    metadata=chunk_metadata
                )
                chunks.append(chunk)
            
            self.logger.debug(f"Created {len(chunks)} semantic chunks from {len(sentences)} sentences")
            return self._update_chunk_totals(chunks)
        
        except Exception as e:
            self.logger.error(f"Semantic chunking failed: {e}, falling back to sentence chunker")
            sentence_chunker = SentenceChunker(self.config)
            return await sentence_chunker.chunk_text(text, text_id, metadata)
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        sentence_endings = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')
        sentences = sentence_endings.split(text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _find_semantic_boundaries(self, sentences: List[str], embeddings: List[List[float]]) -> List[tuple]:
        """Find semantic boundaries using embedding similarity."""
        boundaries = []
        current_start = 0
        current_size = 0
        
        for i in range(len(sentences) - 1):
            current_size += len(sentences[i])
            
            # Calculate similarity between consecutive sentences
            similarity = self._cosine_similarity(embeddings[i], embeddings[i + 1])
            
            # Check if we should create a boundary
            should_split = (
                similarity < self.config.semantic_threshold or 
                current_size > self.config.max_chunk_size
            )
            
            if should_split and current_size >= self.config.min_chunk_size:
                boundaries.append((current_start, i + 1))
                current_start = i + 1
                current_size = 0
        
        # Add final boundary
        if current_start < len(sentences):
            boundaries.append((current_start, len(sentences)))
        
        return boundaries
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)