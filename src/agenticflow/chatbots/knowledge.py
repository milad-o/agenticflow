"""
Knowledge Management System
===========================

Enhanced document loading, chunking, and metadata tracking for chatbots
with comprehensive source tracking and citation capabilities.
"""

import hashlib
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple

from ..text.splitters.manager import split_text
from ..text import SplitterType


@dataclass
class DocumentMetadata:
    """Metadata for a source document."""
    
    # Source information
    source_name: str  # Human-readable name
    file_path: str  # Original file path
    source_type: str  # File type (txt, md, pdf, etc.)
    
    # Content information  
    total_length: int  # Total character count
    total_chunks: int  # Number of chunks created
    language: str = "en"  # Document language
    
    # Timestamps
    created_at: float = 0.0  # When document was first processed
    modified_at: float = 0.0  # When file was last modified
    processed_at: float = 0.0  # When document was last processed
    
    # Additional metadata
    author: Optional[str] = None
    title: Optional[str] = None
    domain: Optional[str] = None  # Subject domain (science, law, etc.)
    tags: List[str] = None
    custom_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.custom_metadata is None:
            self.custom_metadata = {}
        if self.processed_at == 0.0:
            self.processed_at = time.time()


@dataclass
class ChunkMetadata:
    """Metadata for a text chunk."""
    
    # Chunk identification
    chunk_id: str  # Unique identifier
    document_id: str  # Parent document identifier
    chunk_index: int  # Position within document (0-based)
    
    # Content information
    start_char: int  # Start character position in original document
    end_char: int  # End character position in original document
    chunk_length: int  # Character count of this chunk
    
    # Source reference
    source_name: str  # Human-readable source name
    file_path: str  # Original file path
    section: Optional[str] = None  # Section/chapter if detected
    page_number: Optional[int] = None  # Page number if available
    
    # Context information
    preceding_text: str = ""  # Text before chunk (for context)
    following_text: str = ""  # Text after chunk (for context)
    
    # Quality metrics
    readability_score: float = 0.0  # Readability score (0-1)
    information_density: float = 0.0  # Information density score (0-1)
    similarity_to_query: float = 0.0  # Set during retrieval
    
    # Additional metadata
    tags: List[str] = None
    custom_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.custom_metadata is None:
            self.custom_metadata = {}


@dataclass
class RetrievalResult:
    """Result from knowledge retrieval with full metadata."""
    
    # Content
    content: str  # The retrieved text chunk
    chunk_metadata: ChunkMetadata  # Full chunk metadata
    
    # Retrieval metrics
    similarity_score: float  # Similarity to query (0-1)
    retrieval_method: str  # How this was retrieved (semantic, keyword, etc.)
    confidence: float = 1.0  # Confidence in relevance (0-1)
    
    # Citation information
    citation_text: str = ""  # Formatted citation
    source_snippet: str = ""  # Short source description
    
    def get_citation(self, style: str = "inline") -> str:
        """Generate citation in specified style."""
        chunk = self.chunk_metadata
        
        if style == "inline":
            citation = f"[Source: {chunk.source_name}"
            if chunk.chunk_index > 0:
                citation += f", chunk {chunk.chunk_index + 1}"
            if chunk.section:
                citation += f", section: {chunk.section}"
            citation += "]"
            return citation
            
        elif style == "footnotes":
            return f"{chunk.source_name}, chunk {chunk.chunk_index + 1}"
            
        elif style == "detailed":
            citation = f"{chunk.source_name}"
            if chunk.section:
                citation += f", Section: {chunk.section}"
            if chunk.page_number:
                citation += f", Page: {chunk.page_number}"
            citation += f", Position: {chunk.start_char}-{chunk.end_char}"
            citation += f" (Similarity: {self.similarity_score:.2f})"
            return citation
            
        elif style == "academic":
            # Academic-style citation (simplified)
            citation = f"{chunk.source_name}"
            if chunk.section:
                citation += f", {chunk.section}"
            return citation
            
        return self.citation_text or self.source_snippet


class KnowledgeManager:
    """
    Manages knowledge sources with enhanced metadata tracking and retrieval.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path("./.knowledge_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        self.documents: Dict[str, DocumentMetadata] = {}
        self.chunks: List[Tuple[str, ChunkMetadata]] = []  # (content, metadata)
        self.document_hash_cache: Dict[str, str] = {}
    
    def load_knowledge_source(
        self,
        source_path: Union[str, Path],
        source_name: str,
        file_patterns: List[str] = None,
        chunk_size: int = 400,
        chunk_overlap: int = 100,
        metadata: Dict[str, Any] = None
    ) -> List[Tuple[str, ChunkMetadata]]:
        """
        Load a knowledge source with full metadata tracking.
        
        Returns:
            List of (content, metadata) tuples for each chunk
        """
        if file_patterns is None:
            file_patterns = ["*.txt", "*.md"]
        
        source_path = Path(source_path)
        document_chunks = []
        
        # Find all matching files
        files_to_process = []
        if source_path.is_file():
            files_to_process = [source_path]
        else:
            for pattern in file_patterns:
                files_to_process.extend(source_path.glob(pattern))
        
        print(f"📚 Loading knowledge source '{source_name}' from {source_path}")
        print(f"  🔍 Found {len(files_to_process)} files to process")
        
        for file_path in files_to_process:
            chunks = self._process_document(
                file_path=file_path,
                source_name=source_name,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                metadata=metadata or {}
            )
            document_chunks.extend(chunks)
            print(f"  📄 {file_path.name}: {len(chunks)} chunks")
        
        self.chunks.extend(document_chunks)
        print(f"  ✅ Loaded {len(document_chunks)} total chunks")
        
        return document_chunks
    
    def _process_document(
        self,
        file_path: Path,
        source_name: str,
        chunk_size: int,
        chunk_overlap: int,
        metadata: Dict[str, Any]
    ) -> List[Tuple[str, ChunkMetadata]]:
        """Process a single document into chunks with metadata."""
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
        except Exception as e:
            print(f"  ⚠️ Error reading {file_path}: {e}")
            return []
        
        if not content:
            return []
        
        # Check if we've already processed this document
        content_hash = hashlib.md5(content.encode()).hexdigest()
        document_id = f"{source_name}_{file_path.name}_{content_hash[:8]}"
        
        cache_file = self.cache_dir / f"{document_id}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                
                # Reconstruct chunks from cached data
                chunks = []
                for chunk_data in cached_data['chunks']:
                    chunk_metadata = ChunkMetadata(**chunk_data['metadata'])
                    chunks.append((chunk_data['content'], chunk_metadata))
                
                # Update document registry
                self.documents[document_id] = DocumentMetadata(**cached_data['document_metadata'])
                print(f"    🚀 Loaded from cache: {len(chunks)} chunks")
                return chunks
                
            except Exception as e:
                print(f"    ⚠️ Cache read error: {e}")
        
        # Create document metadata
        file_stats = file_path.stat()
        doc_metadata = DocumentMetadata(
            source_name=source_name,
            file_path=str(file_path),
            source_type=file_path.suffix[1:] if file_path.suffix else "txt",
            total_length=len(content),
            total_chunks=0,  # Will be updated
            created_at=time.time(),
            modified_at=file_stats.st_mtime,
            processed_at=time.time(),
            custom_metadata=metadata
        )
        
        # Detect title and section information
        lines = content.split('\n')
        title = self._extract_title(lines)
        if title:
            doc_metadata.title = title
        
        # Split into chunks
        text_chunks = split_text(
            text=content,
            splitter_type=SplitterType.RECURSIVE,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Create chunk metadata
        chunks = []
        char_position = 0
        
        for i, chunk in enumerate(text_chunks):
            chunk_content = chunk.content if hasattr(chunk, 'content') else str(chunk)
            
            # Find the actual position in the original text
            start_char = content.find(chunk_content, char_position)
            if start_char == -1:
                start_char = char_position
            end_char = start_char + len(chunk_content)
            
            # Extract context
            context_size = 50
            preceding_text = content[max(0, start_char - context_size):start_char]
            following_text = content[end_char:end_char + context_size]
            
            # Detect section if possible
            section = self._detect_section(content, start_char)
            
            # Create chunk metadata
            chunk_metadata = ChunkMetadata(
                chunk_id=f"{document_id}_{i:03d}",
                document_id=document_id,
                chunk_index=i,
                start_char=start_char,
                end_char=end_char,
                chunk_length=len(chunk_content),
                source_name=source_name,
                file_path=str(file_path),
                section=section,
                preceding_text=preceding_text,
                following_text=following_text,
                readability_score=self._calculate_readability(chunk_content),
                information_density=self._calculate_information_density(chunk_content),
                custom_metadata=metadata
            )
            
            chunks.append((chunk_content, chunk_metadata))
            char_position = end_char
        
        # Update document metadata
        doc_metadata.total_chunks = len(chunks)
        self.documents[document_id] = doc_metadata
        
        # Cache the results
        cache_data = {
            'document_metadata': asdict(doc_metadata),
            'chunks': [
                {'content': content, 'metadata': asdict(metadata)}
                for content, metadata in chunks
            ]
        }
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"    ⚠️ Cache write error: {e}")
        
        return chunks
    
    def _extract_title(self, lines: List[str]) -> Optional[str]:
        """Extract title from document lines."""
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line and (
                line.startswith('#') or  # Markdown header
                line.isupper() or  # ALL CAPS title
                (len(line) < 100 and ':' not in line and '.' not in line)  # Short line without punctuation
            ):
                return line.lstrip('#').strip()
        return None
    
    def _detect_section(self, content: str, position: int) -> Optional[str]:
        """Detect which section the position falls into."""
        # Look backwards for section headers
        before_text = content[:position]
        lines = before_text.split('\n')
        
        for line in reversed(lines[-20:]):  # Check last 20 lines before position
            line = line.strip()
            if line.startswith('#') or (line.isupper() and len(line) < 100):
                return line.lstrip('#').strip()
        
        return None
    
    def _calculate_readability(self, text: str) -> float:
        """Calculate readability score (simplified)."""
        if not text:
            return 0.0
        
        # Simple readability metric based on sentence and word length
        sentences = text.split('.')
        words = text.split()
        
        if len(sentences) == 0 or len(words) == 0:
            return 0.0
        
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Normalize to 0-1 scale (lower scores = more readable)
        score = max(0, min(1, 1 - (avg_sentence_length / 20 + avg_word_length / 10)))
        return score
    
    def _calculate_information_density(self, text: str) -> float:
        """Calculate information density score (simplified)."""
        if not text:
            return 0.0
        
        # Simple metric based on unique words, numbers, and capitalized words
        words = text.split()
        if not words:
            return 0.0
        
        unique_words = len(set(word.lower() for word in words))
        numbers = sum(1 for word in words if any(c.isdigit() for c in word))
        capitalized = sum(1 for word in words if word[0].isupper())
        
        density = (unique_words / len(words)) + (numbers / len(words)) + (capitalized / len(words))
        return min(1.0, density)
    
    def get_chunks_with_metadata_filter(
        self,
        metadata_filters: Dict[str, Any]
    ) -> List[Tuple[str, ChunkMetadata]]:
        """Get chunks that match metadata filters."""
        filtered_chunks = []
        
        for content, chunk_meta in self.chunks:
            matches = True
            
            # Check each filter
            for key, expected_value in metadata_filters.items():
                if key == "source_name":
                    if chunk_meta.source_name != expected_value:
                        matches = False
                        break
                elif key == "domain":
                    doc = self.documents.get(chunk_meta.document_id)
                    if not doc or doc.domain != expected_value:
                        matches = False
                        break
                elif key == "min_readability":
                    if chunk_meta.readability_score < expected_value:
                        matches = False
                        break
                elif key == "section":
                    if chunk_meta.section != expected_value:
                        matches = False
                        break
                # Add more filter types as needed
            
            if matches:
                filtered_chunks.append((content, chunk_meta))
        
        return filtered_chunks
    
    def create_retrieval_result(
        self,
        content: str,
        chunk_metadata: ChunkMetadata,
        similarity_score: float,
        retrieval_method: str = "unknown"
    ) -> RetrievalResult:
        """Create a RetrievalResult with citation information."""
        
        # Update chunk metadata with retrieval info
        chunk_metadata.similarity_to_query = similarity_score
        
        result = RetrievalResult(
            content=content,
            chunk_metadata=chunk_metadata,
            similarity_score=similarity_score,
            retrieval_method=retrieval_method,
            confidence=similarity_score,  # Simple confidence based on similarity
            source_snippet=f"{chunk_metadata.source_name} (chunk {chunk_metadata.chunk_index + 1})"
        )
        
        return result
    
    def get_knowledge_summary(self) -> Dict[str, Any]:
        """Get summary of loaded knowledge."""
        return {
            "total_documents": len(self.documents),
            "total_chunks": len(self.chunks),
            "sources": list(set(chunk[1].source_name for chunk in self.chunks)),
            "document_types": list(set(doc.source_type for doc in self.documents.values())),
            "average_chunk_length": sum(len(chunk[0]) for chunk in self.chunks) / max(1, len(self.chunks)),
            "cache_dir": str(self.cache_dir)
        }