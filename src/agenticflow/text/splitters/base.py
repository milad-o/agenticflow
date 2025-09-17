"""
Base classes and types for comprehensive text splitting system.
"""

import re
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union, Pattern
import structlog

logger = structlog.get_logger(__name__)


class SplitterType(str, Enum):
    """Available text splitting types."""
    FIXED_SIZE = "fixed_size"
    SENTENCE = "sentence"
    RECURSIVE = "recursive"
    SEMANTIC = "semantic"
    TOKEN = "token"
    MARKDOWN = "markdown"
    HTML = "html"
    CODE = "code"
    PARAGRAPH = "paragraph"
    SECTION = "section"
    CUSTOM = "custom"
    LANGCHAIN = "langchain"


class ContentType(str, Enum):
    """Content types for specialized splitting."""
    PLAIN_TEXT = "plain_text"
    MARKDOWN = "markdown"
    HTML = "html"
    CODE = "code"
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    PDF_TEXT = "pdf_text"
    DOCUMENT = "document"


class LanguageType(str, Enum):
    """Programming language types for code splitting."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    RUBY = "ruby"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    SCALA = "scala"
    HTML = "html"
    CSS = "css"
    SQL = "sql"
    YAML = "yaml"
    JSON = "json"
    XML = "xml"


class BoundaryType(str, Enum):
    """Text boundary types for splitting."""
    CHARACTER = "character"
    WORD = "word"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    LINE = "line"
    SECTION = "section"
    TOKEN = "token"
    SEMANTIC = "semantic"


@dataclass
class TextFragment:
    """
    A fragment of text with rich metadata and positioning information.
    
    Enhanced version of the original TextChunk with additional capabilities.
    """
    content: str
    start_position: Optional[int] = None
    end_position: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    # Core properties
    fragment_id: Optional[str] = None
    source_id: Optional[str] = None
    fragment_index: int = 0
    total_fragments: int = 1
    
    # Content analysis
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    line_count: Optional[int] = None
    
    # Overlap tracking
    overlap_start: int = 0
    overlap_end: int = 0
    
    # Content classification
    boundary_type: BoundaryType = BoundaryType.CHARACTER
    content_type: ContentType = ContentType.PLAIN_TEXT
    language: Optional[str] = None
    
    # Structure preservation
    headers: Optional[Dict[str, str]] = field(default_factory=dict)
    structure_path: Optional[List[str]] = field(default_factory=list)
    
    # Quality metrics
    semantic_coherence: Optional[float] = None
    readability_score: Optional[float] = None
    
    # Advanced features
    embedding: Optional[List[float]] = None
    similarity_scores: Optional[Dict[str, float]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Calculate derived properties."""
        if self.fragment_id is None:
            self.fragment_id = f"fragment_{uuid.uuid4().hex[:8]}"
        
        if self.word_count is None:
            self.word_count = len(self.content.split())
        
        if self.character_count is None:
            self.character_count = len(self.content)
        
        if self.line_count is None:
            self.line_count = len(self.content.splitlines())
    
    def __len__(self) -> int:
        """Return character length of fragment."""
        return len(self.content)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert fragment to dictionary."""
        return {
            "content": self.content,
            "start_position": self.start_position,
            "end_position": self.end_position,
            "metadata": self.metadata,
            "fragment_id": self.fragment_id,
            "source_id": self.source_id,
            "fragment_index": self.fragment_index,
            "total_fragments": self.total_fragments,
            "word_count": self.word_count,
            "character_count": self.character_count,
            "line_count": self.line_count,
            "overlap_start": self.overlap_start,
            "overlap_end": self.overlap_end,
            "boundary_type": self.boundary_type.value,
            "content_type": self.content_type.value,
            "language": self.language,
            "headers": self.headers,
            "structure_path": self.structure_path,
            "semantic_coherence": self.semantic_coherence,
            "readability_score": self.readability_score,
            "embedding": self.embedding,
            "similarity_scores": self.similarity_scores
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TextFragment":
        """Create fragment from dictionary."""
        # Handle enum conversions
        if "boundary_type" in data and isinstance(data["boundary_type"], str):
            data["boundary_type"] = BoundaryType(data["boundary_type"])
        
        if "content_type" in data and isinstance(data["content_type"], str):
            data["content_type"] = ContentType(data["content_type"])
        
        return cls(**data)
    
    def get_preview(self, max_length: int = 100) -> str:
        """Get a preview of the fragment content."""
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."


@dataclass
class SplitterConfig:
    """
    Comprehensive configuration for text splitting.
    """
    # Basic settings
    splitter_type: SplitterType = SplitterType.RECURSIVE
    chunk_size: int = 1000
    chunk_overlap: int = 200
    boundary_type: BoundaryType = BoundaryType.WORD
    
    # Content handling
    content_type: ContentType = ContentType.PLAIN_TEXT
    language: Optional[LanguageType] = None
    encoding: str = "utf-8"
    
    # Size constraints
    min_chunk_size: int = 50
    max_chunk_size: int = 2000
    target_chunk_count: Optional[int] = None
    
    # Quality settings
    semantic_threshold: float = 0.8
    readability_threshold: Optional[float] = None
    coherence_threshold: Optional[float] = None
    
    # Overlap configuration
    overlap_method: str = "symmetric"  # symmetric, forward, backward, smart
    smart_overlap: bool = True
    overlap_at_boundaries: bool = True
    
    # Text processing
    strip_whitespace: bool = True
    normalize_whitespace: bool = True
    preserve_formatting: bool = False
    preserve_structure: bool = True
    
    # Content structure
    include_headers: bool = True
    preserve_code_blocks: bool = True
    preserve_lists: bool = True
    preserve_tables: bool = True
    
    # Custom patterns
    custom_separators: Optional[List[str]] = field(default_factory=list)
    custom_patterns: Optional[List[Pattern[str]]] = field(default_factory=list)
    exclusion_patterns: Optional[List[Pattern[str]]] = field(default_factory=list)
    
    # Advanced features
    enable_embedding: bool = False
    embedding_model: Optional[str] = None
    calculate_similarity: bool = False
    detect_language: bool = True
    analyze_readability: bool = False
    
    # Performance settings
    parallel_processing: bool = False
    max_workers: Optional[int] = None
    batch_size: int = 100
    
    # Debug and monitoring
    debug_mode: bool = False
    collect_metrics: bool = True
    log_performance: bool = False
    
    def __post_init__(self):
        """Validate and process configuration."""
        # Ensure min <= chunk_size <= max
        if self.chunk_size < self.min_chunk_size:
            self.chunk_size = self.min_chunk_size
        
        if self.max_chunk_size < self.chunk_size:
            self.max_chunk_size = self.chunk_size
        
        # Ensure overlap is reasonable
        if self.chunk_overlap >= self.chunk_size:
            self.chunk_overlap = min(self.chunk_size // 2, 500)
        
        # Compile regex patterns if provided as strings
        if self.custom_patterns:
            compiled_patterns = []
            for pattern in self.custom_patterns:
                if isinstance(pattern, str):
                    compiled_patterns.append(re.compile(pattern))
                else:
                    compiled_patterns.append(pattern)
            self.custom_patterns = compiled_patterns
        
        if self.exclusion_patterns:
            compiled_patterns = []
            for pattern in self.exclusion_patterns:
                if isinstance(pattern, str):
                    compiled_patterns.append(re.compile(pattern))
                else:
                    compiled_patterns.append(pattern)
            self.exclusion_patterns = compiled_patterns


class TextSplitter(ABC):
    """
    Abstract base class for advanced text splitting.
    
    Enhanced from the original TextChunker with comprehensive features.
    """
    
    def __init__(self, config: SplitterConfig):
        """Initialize splitter with configuration."""
        self.config = config
        self.logger = logger.bind(splitter=self.__class__.__name__)
        
        # Performance tracking
        self._split_count = 0
        self._total_processing_time = 0.0
        self._metrics = {}
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize splitter components."""
        # Override in subclasses for component setup
        pass
    
    @abstractmethod
    async def split_text(
        self,
        text: str,
        source_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[TextFragment]:
        """
        Split text into fragments.
        
        Args:
            text: Text to split
            source_id: Optional source identifier
            metadata: Optional metadata to include
            
        Returns:
            List of text fragments
        """
        pass
    
    async def split_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[List[TextFragment]]:
        """
        Split multiple documents.
        
        Args:
            documents: List of documents with 'content' and optional 'metadata'
            
        Returns:
            List of fragment lists, one per document
        """
        results = []
        for i, doc in enumerate(documents):
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            source_id = doc.get("id", f"doc_{i}")
            
            fragments = await self.split_text(content, source_id, metadata)
            results.append(fragments)
        
        return results
    
    def create_fragment_id(self, source_id: Optional[str], index: int) -> str:
        """Create unique fragment ID."""
        if source_id:
            return f"{source_id}_fragment_{index}"
        return f"fragment_{index}_{uuid.uuid4().hex[:8]}"
    
    def calculate_overlap(
        self,
        current_fragment: str,
        previous_fragment: Optional[str] = None,
        next_fragment: Optional[str] = None
    ) -> Tuple[int, int]:
        """Calculate overlap positions for a fragment."""
        overlap_start = 0
        overlap_end = 0
        
        if self.config.chunk_overlap <= 0:
            return overlap_start, overlap_end
        
        # Smart overlap at boundaries
        if self.config.smart_overlap:
            return self._calculate_smart_overlap(
                current_fragment, previous_fragment, next_fragment
            )
        
        # Simple overlap
        if previous_fragment and self.config.overlap_method in ["symmetric", "forward"]:
            overlap_size = min(self.config.chunk_overlap, len(current_fragment) // 4)
            overlap_text = current_fragment[:overlap_size]
            if overlap_text in previous_fragment[-overlap_size * 2:]:
                overlap_start = len(overlap_text)
        
        if next_fragment and self.config.overlap_method in ["symmetric", "backward"]:
            overlap_size = min(self.config.chunk_overlap, len(current_fragment) // 4)
            overlap_text = current_fragment[-overlap_size:]
            if overlap_text in next_fragment[:overlap_size * 2]:
                overlap_end = len(overlap_text)
        
        return overlap_start, overlap_end
    
    def _calculate_smart_overlap(
        self,
        current_fragment: str,
        previous_fragment: Optional[str] = None,
        next_fragment: Optional[str] = None
    ) -> Tuple[int, int]:
        """Calculate smart overlap at natural boundaries."""
        overlap_start = 0
        overlap_end = 0
        
        # Find sentence boundaries for smart overlap
        sentence_endings = ['.', '!', '?', '\n\n']
        
        if previous_fragment:
            # Look for sentence boundary in overlap region
            overlap_region = current_fragment[:self.config.chunk_overlap]
            for i, char in enumerate(overlap_region):
                if char in sentence_endings:
                    overlap_start = i + 1
                    break
        
        if next_fragment:
            # Look for sentence boundary in overlap region
            start_pos = len(current_fragment) - self.config.chunk_overlap
            overlap_region = current_fragment[start_pos:]
            for i in range(len(overlap_region) - 1, -1, -1):
                if overlap_region[i] in sentence_endings:
                    overlap_end = len(overlap_region) - i - 1
                    break
        
        return overlap_start, overlap_end
    
    def detect_content_type(self, text: str) -> ContentType:
        """Detect content type from text."""
        text_sample = text[:1000].lower()
        
        # Check for markup languages
        if '<html' in text_sample or '<!doctype html' in text_sample:
            return ContentType.HTML
        elif text_sample.count('#') > 3 or '```' in text_sample:
            return ContentType.MARKDOWN
        elif text_sample.startswith('{') and text_sample.endswith('}'):
            return ContentType.JSON
        elif '<?xml' in text_sample or '<root' in text_sample:
            return ContentType.XML
        
        # Check for code patterns
        code_patterns = ['def ', 'class ', 'function ', 'import ', 'from ']
        if any(pattern in text_sample for pattern in code_patterns):
            return ContentType.CODE
        
        return ContentType.PLAIN_TEXT
    
    def detect_language(self, text: str) -> Optional[str]:
        """Detect text language."""
        if not self.config.detect_language:
            return None
        
        # Simple language detection
        text_sample = text.lower()[:500]
        
        # English indicators
        english_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with']
        english_count = sum(1 for word in english_words if word in text_sample)
        
        if english_count >= 3:
            return 'en'
        
        # Add more language detection logic as needed
        return None
    
    def calculate_readability(self, text: str) -> Optional[float]:
        """Calculate readability score."""
        if not self.config.analyze_readability:
            return None
        
        # Simple readability approximation (Flesch Reading Ease)
        words = text.split()
        sentences = text.count('.') + text.count('!') + text.count('?')
        
        if not words or not sentences:
            return None
        
        avg_sentence_length = len(words) / sentences
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Simplified Flesch formula
        score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_word_length)
        return max(0, min(100, score))
    
    def update_fragment_totals(self, fragments: List[TextFragment]) -> List[TextFragment]:
        """Update total_fragments metadata for all fragments."""
        total = len(fragments)
        for i, fragment in enumerate(fragments):
            fragment.fragment_index = i
            fragment.total_fragments = total
        return fragments
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        avg_time = (
            self._total_processing_time / self._split_count
            if self._split_count > 0 else 0
        )
        
        return {
            "split_count": self._split_count,
            "total_processing_time": self._total_processing_time,
            "average_processing_time": avg_time,
            "custom_metrics": self._metrics.copy()
        }
    
    def reset_metrics(self):
        """Reset performance metrics."""
        self._split_count = 0
        self._total_processing_time = 0.0
        self._metrics.clear()


# Legacy compatibility aliases
ChunkingStrategy = SplitterType  # For backward compatibility
ChunkBoundary = BoundaryType
ChunkMetadata = Dict[str, Any]  # Simplified
TextChunk = TextFragment  # Direct alias
ChunkingConfig = SplitterConfig
TextChunker = TextSplitter