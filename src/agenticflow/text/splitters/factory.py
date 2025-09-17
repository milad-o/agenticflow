"""
Factory for creating text splitters.

Centralized factory for creating different types of text splitters based on configuration.
"""

from typing import Dict, List, Optional, Type
import structlog

from .base import (
    TextSplitter,
    SplitterConfig,
    SplitterType,
    ContentType,
    LanguageType
)
from .strategies import (
    RecursiveSplitter,
    SentenceSplitter,
    MarkdownSplitter,
    CodeSplitter,
    TokenSplitter,
    SemanticSplitter
)

# LangChain adapters (if available)
try:
    from .langchain_adapters import (
        LangChainSplitterAdapter,
        DocumentAwareSplitter,
        create_recursive_character_splitter,
        create_character_splitter,
        create_token_splitter as create_langchain_token_splitter,
        create_markdown_header_splitter,
        create_html_header_splitter,
        create_python_code_splitter,
        create_javascript_code_splitter,
        create_splitter_for_content_type
    )
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

logger = structlog.get_logger(__name__)


class SplitterFactory:
    """
    Factory for creating text splitters.
    
    Provides methods to create splitters based on configuration or content type.
    """
    
    # Registry of available splitter classes
    _splitters: Dict[SplitterType, Type[TextSplitter]] = {
        SplitterType.RECURSIVE: RecursiveSplitter,
        SplitterType.SENTENCE: SentenceSplitter,
        SplitterType.MARKDOWN: MarkdownSplitter,
        SplitterType.CODE: CodeSplitter,
        SplitterType.TOKEN: TokenSplitter,
        SplitterType.SEMANTIC: SemanticSplitter,
    }
    
    @classmethod
    def create_splitter(cls, config: SplitterConfig) -> TextSplitter:
        """
        Create a splitter based on configuration.
        
        Args:
            config: Splitter configuration
            
        Returns:
            Configured text splitter instance
            
        Raises:
            ValueError: If splitter type is not supported
        """
        splitter_type = config.splitter_type
        
        if splitter_type not in cls._splitters:
            raise ValueError(f"Unsupported splitter type: {splitter_type}")
        
        splitter_class = cls._splitters[splitter_type]
        
        try:
            return splitter_class(config)
        except Exception as e:
            logger.error(f"Failed to create splitter {splitter_type}: {e}")
            # Fallback to recursive splitter
            logger.info("Falling back to recursive splitter")
            return RecursiveSplitter(config)
    
    @classmethod
    def create_for_content_type(
        cls,
        content_type: ContentType,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        **kwargs
    ) -> TextSplitter:
        """
        Create an appropriate splitter for the given content type.
        
        Args:
            content_type: Type of content to split
            chunk_size: Target chunk size
            chunk_overlap: Overlap between chunks
            **kwargs: Additional configuration options
            
        Returns:
            Configured text splitter
        """
        # Determine splitter type based on content
        if content_type == ContentType.MARKDOWN:
            splitter_type = SplitterType.MARKDOWN
        elif content_type == ContentType.CODE:
            splitter_type = SplitterType.CODE
        elif content_type == ContentType.HTML:
            # Use recursive splitter with HTML-specific separators
            splitter_type = SplitterType.RECURSIVE
            kwargs.setdefault('custom_separators', ['</p>', '</div>', '</h1>', '</h2>', '</h3>'])
        else:
            # Default to recursive for most content types
            splitter_type = SplitterType.RECURSIVE
        
        config = SplitterConfig(
            splitter_type=splitter_type,
            content_type=content_type,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            **kwargs
        )
        
        return cls.create_splitter(config)
    
    @classmethod
    def create_for_language(
        cls,
        language: LanguageType,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        **kwargs
    ) -> TextSplitter:
        """
        Create a code splitter for the specified programming language.
        
        Args:
            language: Programming language type
            chunk_size: Target chunk size
            chunk_overlap: Overlap between chunks
            **kwargs: Additional configuration options
            
        Returns:
            Configured code splitter
        """
        config = SplitterConfig(
            splitter_type=SplitterType.CODE,
            content_type=ContentType.CODE,
            language=language,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            **kwargs
        )
        
        return cls.create_splitter(config)
    
    @classmethod
    def create_semantic_splitter(
        cls,
        embedding_model: str = "all-MiniLM-L6-v2",
        semantic_threshold: float = 0.8,
        chunk_size: int = 1000,
        **kwargs
    ) -> TextSplitter:
        """
        Create a semantic splitter with embeddings.
        
        Args:
            embedding_model: Model name for embeddings
            semantic_threshold: Similarity threshold for grouping
            chunk_size: Target chunk size
            **kwargs: Additional configuration options
            
        Returns:
            Configured semantic splitter
        """
        config = SplitterConfig(
            splitter_type=SplitterType.SEMANTIC,
            enable_embedding=True,
            embedding_model=embedding_model,
            semantic_threshold=semantic_threshold,
            chunk_size=chunk_size,
            **kwargs
        )
        
        return cls.create_splitter(config)
    
    @classmethod
    def create_token_splitter(
        cls,
        model_name: str = "gpt-3.5-turbo",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        **kwargs
    ) -> TextSplitter:
        """
        Create a token-based splitter.
        
        Args:
            model_name: Model name for tokenization
            chunk_size: Target token count per chunk
            chunk_overlap: Token overlap between chunks
            **kwargs: Additional configuration options
            
        Returns:
            Configured token splitter
        """
        config = SplitterConfig(
            splitter_type=SplitterType.TOKEN,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            custom_separators=[model_name],  # Pass model name this way
            **kwargs
        )
        
        return cls.create_splitter(config)
    
    @classmethod
    def get_available_splitters(cls) -> List[SplitterType]:
        """
        Get list of available splitter types.
        
        Returns:
            List of supported splitter types
        """
        return list(cls._splitters.keys())
    
    @classmethod
    def register_splitter(cls, splitter_type: SplitterType, splitter_class: Type[TextSplitter]):
        """
        Register a custom splitter class.
        
        Args:
            splitter_type: Type identifier for the splitter
            splitter_class: Splitter class to register
        """
        if not issubclass(splitter_class, TextSplitter):
            raise ValueError("Splitter class must inherit from TextSplitter")
        
        cls._splitters[splitter_type] = splitter_class
        logger.info(f"Registered custom splitter: {splitter_type}")
    
    # LangChain convenience methods
    @classmethod
    def create_langchain_splitter(
        cls,
        splitter_name: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        **kwargs
    ) -> Optional[TextSplitter]:
        """
        Create a LangChain-based splitter.
        
        Args:
            splitter_name: Name of LangChain splitter
            chunk_size: Target chunk size
            chunk_overlap: Overlap between chunks
            **kwargs: Additional arguments for the LangChain splitter
            
        Returns:
            LangChain splitter adapter or None if not available
        """
        if not LANGCHAIN_AVAILABLE:
            logger.warning("LangChain not available for splitter creation")
            return None
        
        try:
            if splitter_name == "recursive_character":
                return create_recursive_character_splitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    **kwargs
                )
            elif splitter_name == "character":
                return create_character_splitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    **kwargs
                )
            elif splitter_name == "token":
                return create_langchain_token_splitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    **kwargs
                )
            elif splitter_name == "markdown_header":
                headers = kwargs.pop('headers', [
                    ("#", "Header 1"),
                    ("##", "Header 2"),
                    ("###", "Header 3")
                ])
                return create_markdown_header_splitter(headers, **kwargs)
            elif splitter_name == "html_header":
                headers = kwargs.pop('headers', [
                    ("h1", "Header 1"),
                    ("h2", "Header 2"),
                    ("h3", "Header 3")
                ])
                return create_html_header_splitter(headers, **kwargs)
            elif splitter_name == "python_code":
                return create_python_code_splitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    **kwargs
                )
            elif splitter_name == "javascript_code":
                return create_javascript_code_splitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    **kwargs
                )
            else:
                logger.warning(f"Unknown LangChain splitter: {splitter_name}")
                return None
        
        except Exception as e:
            logger.error(f"Failed to create LangChain splitter {splitter_name}: {e}")
            return None
    
    @classmethod
    def create_smart_splitter(
        cls,
        text_sample: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        **kwargs
    ) -> TextSplitter:
        """
        Create an intelligent splitter based on text analysis.
        
        Args:
            text_sample: Sample of text to analyze
            chunk_size: Target chunk size
            chunk_overlap: Overlap between chunks
            **kwargs: Additional configuration options
            
        Returns:
            Best-fit splitter for the content
        """
        # Analyze the text sample
        content_type = cls._analyze_content_type(text_sample)
        language = cls._analyze_programming_language(text_sample) if content_type == ContentType.CODE else None
        
        # Create appropriate splitter
        if content_type == ContentType.CODE and language:
            return cls.create_for_language(language, chunk_size, chunk_overlap, **kwargs)
        else:
            return cls.create_for_content_type(content_type, chunk_size, chunk_overlap, **kwargs)
    
    @classmethod
    def _analyze_content_type(cls, text: str) -> ContentType:
        """Analyze text to determine content type."""
        text_sample = text[:2000].lower()
        
        # Check for markdown
        if '# ' in text_sample or '## ' in text_sample or '```' in text_sample:
            return ContentType.MARKDOWN
        
        # Check for HTML
        if '<html' in text_sample or '<!doctype' in text_sample or '</div>' in text_sample:
            return ContentType.HTML
        
        # Check for code
        code_indicators = ['def ', 'function', 'class ', 'import ', 'from ', 'const ', 'var ', 'let ']
        if any(indicator in text_sample for indicator in code_indicators):
            return ContentType.CODE
        
        # Check for JSON
        if text_sample.strip().startswith('{') and '"' in text_sample:
            return ContentType.JSON
        
        # Check for XML
        if '<?xml' in text_sample or text_sample.strip().startswith('<'):
            return ContentType.XML
        
        return ContentType.PLAIN_TEXT
    
    @classmethod
    def _analyze_programming_language(cls, text: str) -> Optional[LanguageType]:
        """Analyze code to determine programming language."""
        text_sample = text[:1000].lower()
        
        # Python indicators
        if 'def ' in text_sample and 'import ' in text_sample:
            return LanguageType.PYTHON
        
        # JavaScript indicators
        if 'function' in text_sample and ('const ' in text_sample or 'let ' in text_sample):
            return LanguageType.JAVASCRIPT
        
        # Java indicators
        if 'class ' in text_sample and 'public ' in text_sample:
            return LanguageType.JAVA
        
        # TypeScript indicators
        if 'interface ' in text_sample or ': string' in text_sample or ': number' in text_sample:
            return LanguageType.TYPESCRIPT
        
        return None


# Convenience functions
def create_splitter(
    splitter_type: SplitterType,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    **kwargs
) -> TextSplitter:
    """
    Create a splitter with the specified type.
    
    Args:
        splitter_type: Type of splitter to create
        chunk_size: Target chunk size
        chunk_overlap: Overlap between chunks
        **kwargs: Additional configuration options
        
    Returns:
        Configured text splitter
    """
    config = SplitterConfig(
        splitter_type=splitter_type,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        **kwargs
    )
    return SplitterFactory.create_splitter(config)


def create_smart_splitter(
    text_sample: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    **kwargs
) -> TextSplitter:
    """
    Create an intelligent splitter based on text analysis.
    
    Args:
        text_sample: Sample of text to analyze
        chunk_size: Target chunk size
        chunk_overlap: Overlap between chunks
        **kwargs: Additional configuration options
        
    Returns:
        Best-fit splitter for the content
    """
    return SplitterFactory.create_smart_splitter(text_sample, chunk_size, chunk_overlap, **kwargs)


def get_available_splitters() -> List[SplitterType]:
    """Get list of available splitter types."""
    return SplitterFactory.get_available_splitters()