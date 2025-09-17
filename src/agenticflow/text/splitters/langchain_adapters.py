"""
LangChain Text Splitter Integration
=================================
Adapters to use LangChain's text splitting strategies with our chunking system.
"""

from typing import Any, Dict, List, Optional, Type
import structlog

from langchain_text_splitters import (
    TextSplitter as LangChainTextSplitter,
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    TokenTextSplitter,
    MarkdownHeaderTextSplitter,
    HTMLHeaderTextSplitter,
    PythonCodeTextSplitter,
    JavaScriptTextSplitter,
)

from .base import TextSplitter, TextFragment, SplitterConfig

logger = structlog.get_logger(__name__)


class LangChainSplitterAdapter(TextSplitter):
    """
    Adapter to use any LangChain TextSplitter with our chunking interface.
    
    Supports all LangChain text splitters including:
    - RecursiveCharacterTextSplitter
    - CharacterTextSplitter  
    - TokenTextSplitter
    - MarkdownHeaderTextSplitter
    - HTMLHeaderTextSplitter
    - Language-specific splitters (Python, JavaScript, etc.)
    """
    
    def __init__(
        self,
        langchain_splitter: LangChainTextSplitter,
        config: Optional[SplitterConfig] = None
    ):
        """
        Initialize with a LangChain text splitter.
        
        Args:
            langchain_splitter: Any LangChain TextSplitter instance
            config: Optional chunking config (will be merged with splitter settings)
        """
        super().__init__(config or SplitterConfig())
        self.langchain_splitter = langchain_splitter
        
        # Update config with splitter settings if available
        if hasattr(langchain_splitter, '_chunk_size'):
            self.config.chunk_size = langchain_splitter._chunk_size
        if hasattr(langchain_splitter, '_chunk_overlap'):
            self.config.chunk_overlap = langchain_splitter._chunk_overlap
        
        self.logger.debug(f"Initialized LangChain splitter adapter: {type(langchain_splitter).__name__}")
    
    async def split_text(self, text: str, source_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> List[TextFragment]:
        """
        Split text using the LangChain splitter.
        
        Args:
            text: Text to split
            metadata: Optional metadata to include in chunks
            
        Returns:
            List of TextChunk objects
        """
        if not text.strip():
            return []
        
        metadata = metadata or {}
        
        try:
            # Use LangChain splitter to split the text
            texts = self.langchain_splitter.split_text(text)
            
            fragments = []
            for i, fragment_text in enumerate(texts):
                if fragment_text.strip():  # Skip empty fragments
                    fragment_metadata = {
                        **metadata,
                        'fragment_index': i,
                        'total_fragments': len(texts),
                        'splitter_type': type(self.langchain_splitter).__name__
                    }
                    
                    fragment = TextFragment(
                        content=fragment_text,
                        start_position=text.find(fragment_text) if i == 0 else None,
                        end_position=None,  # LangChain doesn't provide positions
                        metadata=fragment_metadata
                    )
                    fragments.append(fragment)
            
            self.logger.debug(f"Split text into {len(fragments)} fragments using {type(self.langchain_splitter).__name__}")
            return fragments
        
        except Exception as e:
            self.logger.error(f"Failed to split text with LangChain splitter: {e}")
            # Fallback: return entire text as single fragment
            return [TextFragment(
                content=text,
                start_position=0,
                end_position=len(text),
                metadata={**metadata, 'error': str(e)}
            )]
    
    def get_chunk_size(self) -> int:
        """Get the chunk size used by the splitter."""
        if hasattr(self.langchain_splitter, '_chunk_size'):
            return self.langchain_splitter._chunk_size
        return self.config.chunk_size
    
    def get_chunk_overlap(self) -> int:
        """Get the chunk overlap used by the splitter."""
        if hasattr(self.langchain_splitter, '_chunk_overlap'):
            return self.langchain_splitter._chunk_overlap
        return self.config.chunk_overlap


# Convenience functions for common LangChain splitters

def create_recursive_character_splitter(
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    separators: Optional[List[str]] = None,
    keep_separator: bool = True,
    **kwargs
) -> LangChainSplitterAdapter:
    """
    Create adapter for LangChain's RecursiveCharacterTextSplitter.
    
    This is the most commonly used and versatile splitter.
    It tries to split on paragraph breaks, then sentences, then words.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
        keep_separator=keep_separator,
        **kwargs
    )
    
    config = ChunkingConfig(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    return LangChainSplitterAdapter(splitter, config)


def create_character_splitter(
    separator: str = "\n\n",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    **kwargs
) -> LangChainSplitterAdapter:
    """
    Create adapter for LangChain's CharacterTextSplitter.
    
    Splits on a single character/string separator.
    """
    splitter = CharacterTextSplitter(
        separator=separator,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        **kwargs
    )
    
    config = ChunkingConfig(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    return LangChainSplitterAdapter(splitter, config)


def create_token_splitter(
    encoding_name: str = "gpt2",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    **kwargs
) -> LangChainSplitterAdapter:
    """
    Create adapter for LangChain's TokenTextSplitter.
    
    Splits text based on token count using tiktoken.
    """
    try:
        splitter = TokenTextSplitter(
            encoding_name=encoding_name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            **kwargs
        )
        
        config = ChunkingConfig(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        return LangChainSplitterAdapter(splitter, config)
    
    except ImportError:
        raise ImportError("tiktoken required for TokenTextSplitter. Install with: pip install tiktoken")


def create_markdown_header_splitter(
    headers_to_split_on: List[tuple],
    strip_headers: bool = True,
    **kwargs
) -> LangChainSplitterAdapter:
    """
    Create adapter for LangChain's MarkdownHeaderTextSplitter.
    
    Splits markdown based on headers and creates hierarchical metadata.
    
    Args:
        headers_to_split_on: List of tuples like [("#", "Header 1"), ("##", "Header 2")]
    """
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=strip_headers,
        **kwargs
    )
    
    # MarkdownHeaderTextSplitter doesn't have chunk_size/overlap
    config = ChunkingConfig()
    
    return LangChainSplitterAdapter(splitter, config)


def create_html_header_splitter(
    headers_to_split_on: List[tuple],
    **kwargs
) -> LangChainSplitterAdapter:
    """
    Create adapter for LangChain's HTMLHeaderTextSplitter.
    
    Splits HTML based on headers and preserves document structure.
    
    Args:
        headers_to_split_on: List of tuples like [("h1", "Header 1"), ("h2", "Header 2")]
    """
    splitter = HTMLHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        **kwargs
    )
    
    config = ChunkingConfig()
    
    return LangChainSplitterAdapter(splitter, config)


def create_python_code_splitter(
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    **kwargs
) -> LangChainSplitterAdapter:
    """
    Create adapter for LangChain's PythonCodeTextSplitter.
    
    Specialized splitter for Python code that respects language structure.
    """
    splitter = PythonCodeTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        **kwargs
    )
    
    config = ChunkingConfig(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    return LangChainSplitterAdapter(splitter, config)


def create_javascript_code_splitter(
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    **kwargs
) -> LangChainSplitterAdapter:
    """
    Create adapter for LangChain's JavaScriptTextSplitter.
    
    Specialized splitter for JavaScript code that respects language structure.
    """
    splitter = JavaScriptTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        **kwargs
    )
    
    config = ChunkingConfig(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    return LangChainSplitterAdapter(splitter, config)


# Advanced splitter factory

def create_splitter_for_content_type(
    content_type: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    **kwargs
) -> LangChainSplitterAdapter:
    """
    Create an appropriate LangChain splitter based on content type.
    
    Args:
        content_type: Type of content ('markdown', 'html', 'python', 'javascript', 'text')
        chunk_size: Target chunk size
        chunk_overlap: Overlap between chunks
        **kwargs: Additional arguments for the splitter
        
    Returns:
        Appropriate LangChainSplitterAdapter
    """
    content_type = content_type.lower()
    
    if content_type == 'markdown':
        headers = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        return create_markdown_header_splitter(headers, **kwargs)
    
    elif content_type == 'html':
        headers = [
            ("h1", "Header 1"),
            ("h2", "Header 2"),
            ("h3", "Header 3"),
        ]
        return create_html_header_splitter(headers, **kwargs)
    
    elif content_type == 'python':
        return create_python_code_splitter(chunk_size, chunk_overlap, **kwargs)
    
    elif content_type == 'javascript':
        return create_javascript_code_splitter(chunk_size, chunk_overlap, **kwargs)
    
    else:
        # Default to recursive character splitter
        return create_recursive_character_splitter(chunk_size, chunk_overlap, **kwargs)


# Document-aware splitter that uses LangChain's document loaders

class DocumentAwareSplitter(TextSplitter):
    """
    Advanced splitter that can work with LangChain's Document objects.
    
    This preserves more metadata and can handle complex document structures.
    """
    
    def __init__(
        self,
        langchain_splitter: LangChainTextSplitter,
        config: Optional[SplitterConfig] = None
    ):
        super().__init__(config or SplitterConfig())
        self.langchain_splitter = langchain_splitter
    
    async def split_text(self, text: str, source_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> List[TextFragment]:
        """Split text while preserving document metadata."""
        from langchain_core.documents import Document as LangChainDocument
        
        if not text.strip():
            return []
        
        metadata = metadata or {}
        
        try:
            # Create a LangChain document
            doc = LangChainDocument(page_content=text, metadata=metadata)
            
            # Split using LangChain's document splitting
            if hasattr(self.langchain_splitter, 'split_documents'):
                split_docs = self.langchain_splitter.split_documents([doc])
            else:
                # Fallback to text splitting
                texts = self.langchain_splitter.split_text(text)
                split_docs = [LangChainDocument(page_content=t, metadata=metadata) for t in texts]
            
            # Convert to our TextChunk format
            chunks = []
            for i, split_doc in enumerate(split_docs):
                if split_doc.page_content.strip():
                    chunk_metadata = {
                        **split_doc.metadata,
                        'chunk_index': i,
                        'total_chunks': len(split_docs),
                        'splitter_type': type(self.langchain_splitter).__name__
                    }
                    
                    chunk = TextChunk(
                        content=split_doc.page_content,
                        metadata=chunk_metadata,
                        start_position=None,
                        end_position=None
                    )
                    chunks.append(chunk)
            
            return chunks
        
        except Exception as e:
            self.logger.error(f"Document splitting failed: {e}")
            return [TextChunk(
                content=text,
                metadata={**metadata, 'error': str(e)},
                start_position=0,
                end_position=len(text)
            )]