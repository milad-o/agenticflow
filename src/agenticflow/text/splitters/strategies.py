"""
Advanced text splitting strategies.

Comprehensive collection of text splitters for different content types and use cases.
"""

import asyncio
import re
import time
from typing import Any, Dict, List, Optional, Tuple
import structlog

from .base import (
    TextSplitter,
    TextFragment,
    SplitterConfig,
    SplitterType,
    ContentType,
    BoundaryType,
    LanguageType
)

logger = structlog.get_logger(__name__)


class RecursiveSplitter(TextSplitter):
    """
    Recursive text splitter that tries multiple separators in order.
    
    This is the most versatile splitter, trying to split on:
    1. Paragraph breaks (\n\n)
    2. Sentence endings (.!?)
    3. Line breaks (\n)
    4. Words
    5. Characters (fallback)
    """
    
    def __init__(self, config: SplitterConfig):
        super().__init__(config)
        
        # Default separators in order of preference
        self.separators = [
            "\n\n",  # Paragraph breaks
            "\n",    # Line breaks
            " ",     # Word boundaries
            ""       # Character fallback
        ]
        
        # Content-specific separators
        if config.content_type == ContentType.MARKDOWN:
            self.separators = ["\n## ", "\n### ", "\n\n", "\n", " ", ""]
        elif config.content_type == ContentType.HTML:
            self.separators = ["</p>", "</div>", "\n\n", "\n", " ", ""]
        elif config.content_type == ContentType.CODE:
            self.separators = ["\n\nclass ", "\n\ndef ", "\n\n", "\n", " ", ""]
        
        # Add custom separators if provided
        if config.custom_separators:
            self.separators = config.custom_separators + self.separators
    
    async def split_text(
        self,
        text: str,
        source_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[TextFragment]:
        """Split text recursively using multiple separators."""
        start_time = time.time()
        
        if not text.strip():
            return []
        
        # Clean text if configured
        if self.config.strip_whitespace:
            text = text.strip()
        
        if self.config.normalize_whitespace:
            text = re.sub(r'\s+', ' ', text)
        
        # Start recursive splitting
        fragments = await self._recursive_split(text, 0)
        
        # Post-process fragments
        processed_fragments = []
        for i, fragment in enumerate(fragments):
            fragment.fragment_id = self.create_fragment_id(source_id, i)
            fragment.source_id = source_id
            fragment.content_type = self.detect_content_type(fragment.content)
            fragment.language = self.detect_language(fragment.content)
            fragment.readability_score = self.calculate_readability(fragment.content)
            
            if metadata:
                fragment.metadata.update(metadata)
            
            processed_fragments.append(fragment)
        
        # Update totals and calculate overlaps
        processed_fragments = self.update_fragment_totals(processed_fragments)
        
        # Calculate overlaps
        for i, fragment in enumerate(processed_fragments):
            prev_frag = processed_fragments[i-1].content if i > 0 else None
            next_frag = processed_fragments[i+1].content if i < len(processed_fragments)-1 else None
            fragment.overlap_start, fragment.overlap_end = self.calculate_overlap(
                fragment.content, prev_frag, next_frag
            )
        
        # Performance tracking
        self._split_count += 1
        self._total_processing_time += time.time() - start_time
        
        return processed_fragments
    
    async def _recursive_split(self, text: str, separator_index: int) -> List[TextFragment]:
        """Recursively split text using separators."""
        # Base case: if text is small enough, return as single fragment
        if len(text) <= self.config.chunk_size:
            return [TextFragment(content=text)]
        
        # Try current separator
        if separator_index >= len(self.separators):
            # Fallback: force split by character count
            return self._force_split(text)
        
        separator = self.separators[separator_index]
        
        if separator == "":
            # Character-level splitting
            return self._force_split(text)
        
        # Split by separator
        splits = text.split(separator)
        
        fragments = []
        current_chunk = ""
        
        for split in splits:
            # Add separator back (except for the last split)
            test_chunk = current_chunk + separator + split if current_chunk else split
            
            if len(test_chunk) <= self.config.chunk_size:
                current_chunk = test_chunk
            else:
                # Current chunk is full, process it
                if current_chunk:
                    fragments.extend(await self._recursive_split(current_chunk, separator_index + 1))
                
                # Start new chunk with current split
                if len(split) <= self.config.chunk_size:
                    current_chunk = split
                else:
                    # Split is too large, recursively split it
                    fragments.extend(await self._recursive_split(split, separator_index + 1))
                    current_chunk = ""
        
        # Add remaining chunk
        if current_chunk:
            fragments.extend(await self._recursive_split(current_chunk, separator_index + 1))
        
        return fragments
    
    def _force_split(self, text: str) -> List[TextFragment]:
        """Force split text by character count."""
        fragments = []
        start = 0
        
        while start < len(text):
            end = min(start + self.config.chunk_size, len(text))
            
            # Try to avoid splitting in the middle of a word
            if end < len(text) and not text[end].isspace():
                # Look for a space near the end
                for i in range(end, max(end - 100, start), -1):
                    if text[i].isspace():
                        end = i
                        break
            
            chunk_text = text[start:end]
            fragment = TextFragment(
                content=chunk_text,
                start_position=start,
                end_position=end,
                boundary_type=BoundaryType.CHARACTER
            )
            fragments.append(fragment)
            
            # Apply overlap
            start = end - self.config.chunk_overlap if self.config.chunk_overlap > 0 else end
        
        return fragments


class SentenceSplitter(TextSplitter):
    """
    Sentence-based text splitter.
    
    Splits text at sentence boundaries while maintaining chunk size constraints.
    """
    
    def __init__(self, config: SplitterConfig):
        super().__init__(config)
        
        # Sentence boundary patterns
        self.sentence_pattern = re.compile(r'[.!?]+\s+')
        self.quote_aware_pattern = re.compile(r'[.!?]+(?=\s+[A-Z]|$)')
    
    async def split_text(
        self,
        text: str,
        source_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[TextFragment]:
        """Split text by sentences."""
        start_time = time.time()
        
        if not text.strip():
            return []
        
        # Find sentence boundaries
        sentences = self._split_into_sentences(text)
        
        fragments = []
        current_chunk = ""
        current_sentences = []
        
        for sentence in sentences:
            # Check if adding this sentence would exceed chunk size
            test_chunk = (current_chunk + " " + sentence).strip()
            
            if len(test_chunk) <= self.config.chunk_size or not current_chunk:
                current_chunk = test_chunk
                current_sentences.append(sentence)
            else:
                # Create fragment from current chunk
                if current_chunk:
                    fragment = self._create_sentence_fragment(
                        current_chunk, current_sentences, source_id, metadata
                    )
                    fragments.append(fragment)
                
                # Start new chunk
                current_chunk = sentence
                current_sentences = [sentence]
        
        # Add remaining chunk
        if current_chunk:
            fragment = self._create_sentence_fragment(
                current_chunk, current_sentences, source_id, metadata
            )
            fragments.append(fragment)
        
        # Apply sentence-level overlap
        if self.config.chunk_overlap > 0:
            fragments = self._apply_sentence_overlap(fragments)
        
        # Post-process
        fragments = self.update_fragment_totals(fragments)
        
        # Performance tracking
        self._split_count += 1
        self._total_processing_time += time.time() - start_time
        
        return fragments
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Handle common abbreviations
        text = re.sub(r'\b(Dr|Mr|Mrs|Ms|Prof|etc|vs|Inc|Ltd)\.\s+', r'\1.\u2026', text)
        
        # Split on sentence boundaries
        sentences = self.quote_aware_pattern.split(text)
        
        # Restore abbreviations
        sentences = [s.replace('\u2026', ' ') for s in sentences if s.strip()]
        
        return sentences
    
    def _create_sentence_fragment(
        self,
        content: str,
        sentences: List[str],
        source_id: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ) -> TextFragment:
        """Create a fragment from sentences."""
        fragment = TextFragment(
            content=content,
            boundary_type=BoundaryType.SENTENCE,
            metadata=metadata.copy() if metadata else {}
        )
        
        fragment.metadata['sentence_count'] = len(sentences)
        fragment.content_type = self.detect_content_type(content)
        fragment.language = self.detect_language(content)
        fragment.readability_score = self.calculate_readability(content)
        
        return fragment
    
    def _apply_sentence_overlap(self, fragments: List[TextFragment]) -> List[TextFragment]:
        """Apply sentence-level overlap between fragments."""
        if len(fragments) <= 1:
            return fragments
        
        overlapped_fragments = [fragments[0]]
        
        for i in range(1, len(fragments)):
            current = fragments[i]
            previous = fragments[i-1]
            
            # Try to overlap by complete sentences
            prev_sentences = self._split_into_sentences(previous.content)
            overlap_sentences = prev_sentences[-min(2, len(prev_sentences)):]  # Last 1-2 sentences
            
            if overlap_sentences:
                overlap_text = " ".join(overlap_sentences)
                current.content = overlap_text + " " + current.content
                current.overlap_start = len(overlap_text)
            
            overlapped_fragments.append(current)
        
        return overlapped_fragments


class MarkdownSplitter(TextSplitter):
    """
    Markdown-aware text splitter.
    
    Splits markdown content while preserving structure and hierarchy.
    """
    
    def __init__(self, config: SplitterConfig):
        super().__init__(config)
        
        # Markdown structure patterns
        self.header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        self.code_block_pattern = re.compile(r'```[\s\S]*?```', re.MULTILINE)
        self.list_pattern = re.compile(r'^\s*[-*+]\s+', re.MULTILINE)
    
    async def split_text(
        self,
        text: str,
        source_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[TextFragment]:
        """Split markdown text preserving structure."""
        start_time = time.time()
        
        if not text.strip():
            return []
        
        # Parse markdown structure
        sections = self._parse_markdown_sections(text)
        
        fragments = []
        for section in sections:
            # Split large sections further if needed
            section_fragments = await self._split_markdown_section(section, source_id, metadata)
            fragments.extend(section_fragments)
        
        # Update totals
        fragments = self.update_fragment_totals(fragments)
        
        # Performance tracking
        self._split_count += 1
        self._total_processing_time += time.time() - start_time
        
        return fragments
    
    def _parse_markdown_sections(self, text: str) -> List[Dict[str, Any]]:
        """Parse markdown into hierarchical sections."""
        lines = text.split('\n')
        sections = []
        current_section = {
            'level': 0,
            'header': None,
            'content': [],
            'line_start': 0
        }
        
        for i, line in enumerate(lines):
            header_match = self.header_pattern.match(line)
            
            if header_match:
                # Save current section if it has content
                if current_section['content'] or current_section['header']:
                    current_section['content'] = '\n'.join(current_section['content'])
                    sections.append(current_section)
                
                # Start new section
                level = len(header_match.group(1))
                header = header_match.group(2)
                
                current_section = {
                    'level': level,
                    'header': header,
                    'content': [],
                    'line_start': i
                }
            else:
                current_section['content'].append(line)
        
        # Add last section
        if current_section['content'] or current_section['header']:
            current_section['content'] = '\n'.join(current_section['content'])
            sections.append(current_section)
        
        return sections
    
    async def _split_markdown_section(
        self,
        section: Dict[str, Any],
        source_id: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ) -> List[TextFragment]:
        """Split a markdown section into fragments."""
        content = section['content']
        header = section['header']
        
        # Include header in content if configured
        if header and self.config.include_headers:
            header_text = f"{'#' * section['level']} {header}\n\n"
            content = header_text + content
        
        fragments = []
        
        if len(content) <= self.config.chunk_size:
            # Section fits in one fragment
            fragment = TextFragment(
                content=content,
                boundary_type=BoundaryType.SECTION,
                content_type=ContentType.MARKDOWN,
                headers={'h' + str(section['level']): header} if header else {},
                structure_path=[header] if header else []
            )
            fragments.append(fragment)
        else:
            # Need to split section further
            # Use recursive splitter for content
            recursive_splitter = RecursiveSplitter(self.config)
            sub_fragments = await recursive_splitter.split_text(content, source_id, metadata)
            
            # Add markdown-specific metadata to each fragment
            for fragment in sub_fragments:
                fragment.content_type = ContentType.MARKDOWN
                fragment.boundary_type = BoundaryType.SECTION
                if header:
                    fragment.headers['h' + str(section['level'])] = header
                    fragment.structure_path = [header]
            
            fragments.extend(sub_fragments)
        
        return fragments


class CodeSplitter(TextSplitter):
    """
    Code-aware text splitter.
    
    Splits code while preserving function and class boundaries.
    """
    
    def __init__(self, config: SplitterConfig):
        super().__init__(config)
        
        # Language-specific patterns
        self.language_patterns = {
            LanguageType.PYTHON: {
                'function': re.compile(r'^def\s+\w+.*?:', re.MULTILINE),
                'class': re.compile(r'^class\s+\w+.*?:', re.MULTILINE),
                'import': re.compile(r'^(import|from)\s+.*', re.MULTILINE),
            },
            LanguageType.JAVASCRIPT: {
                'function': re.compile(r'function\s+\w+.*?\{', re.MULTILINE),
                'class': re.compile(r'class\s+\w+.*?\{', re.MULTILINE),
                'import': re.compile(r'^(import|export)\s+.*', re.MULTILINE),
            },
            LanguageType.JAVA: {
                'function': re.compile(r'(public|private|protected)?\s*(static)?\s*\w+\s+\w+\s*\(.*?\)\s*\{', re.MULTILINE),
                'class': re.compile(r'(public|private)?\s*class\s+\w+.*?\{', re.MULTILINE),
                'import': re.compile(r'^import\s+.*', re.MULTILINE),
            }
        }
    
    async def split_text(
        self,
        text: str,
        source_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[TextFragment]:
        """Split code text preserving structure."""
        start_time = time.time()
        
        if not text.strip():
            return []
        
        # Detect programming language if not specified
        language = self.config.language or self._detect_programming_language(text)
        
        # Parse code structure
        code_blocks = self._parse_code_structure(text, language)
        
        fragments = []
        for block in code_blocks:
            block_fragments = await self._split_code_block(block, source_id, metadata)
            fragments.extend(block_fragments)
        
        # Update totals
        fragments = self.update_fragment_totals(fragments)
        
        # Performance tracking
        self._split_count += 1
        self._total_processing_time += time.time() - start_time
        
        return fragments
    
    def _detect_programming_language(self, code: str) -> Optional[LanguageType]:
        """Detect programming language from code patterns."""
        code_sample = code[:1000].lower()
        
        # Python indicators
        if 'def ' in code_sample and 'import ' in code_sample:
            return LanguageType.PYTHON
        
        # JavaScript indicators
        if 'function' in code_sample and ('const ' in code_sample or 'let ' in code_sample):
            return LanguageType.JAVASCRIPT
        
        # Java indicators
        if 'class ' in code_sample and 'public ' in code_sample:
            return LanguageType.JAVA
        
        return None
    
    def _parse_code_structure(self, code: str, language: Optional[LanguageType]) -> List[Dict[str, Any]]:
        """Parse code into structured blocks."""
        if not language or language not in self.language_patterns:
            # Fallback: split by function-like patterns
            return [{'content': code, 'type': 'unknown', 'name': None}]
        
        patterns = self.language_patterns[language]
        blocks = []
        lines = code.split('\n')
        current_block = {'content': [], 'type': 'code', 'name': None, 'start_line': 0}
        
        for i, line in enumerate(lines):
            # Check for function/class definitions
            for block_type, pattern in patterns.items():
                if pattern.match(line.strip()):
                    # Save current block
                    if current_block['content']:
                        current_block['content'] = '\n'.join(current_block['content'])
                        blocks.append(current_block)
                    
                    # Start new block
                    current_block = {
                        'content': [line],
                        'type': block_type,
                        'name': self._extract_name(line, block_type),
                        'start_line': i
                    }
                    continue
            
            current_block['content'].append(line)
        
        # Add last block
        if current_block['content']:
            current_block['content'] = '\n'.join(current_block['content'])
            blocks.append(current_block)
        
        return blocks
    
    def _extract_name(self, line: str, block_type: str) -> Optional[str]:
        """Extract name from function/class definition."""
        if block_type == 'function':
            # Simple pattern to extract function name
            match = re.search(r'(?:def|function)\s+(\w+)', line)
            return match.group(1) if match else None
        elif block_type == 'class':
            match = re.search(r'class\s+(\w+)', line)
            return match.group(1) if match else None
        
        return None
    
    async def _split_code_block(
        self,
        block: Dict[str, Any],
        source_id: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ) -> List[TextFragment]:
        """Split a code block into fragments."""
        content = block['content']
        
        fragments = []
        
        if len(content) <= self.config.chunk_size:
            # Block fits in one fragment
            fragment = TextFragment(
                content=content,
                boundary_type=BoundaryType.SECTION,
                content_type=ContentType.CODE,
                metadata={
                    **(metadata or {}),
                    'code_type': block['type'],
                    'code_name': block['name'],
                    'start_line': block.get('start_line', 0)
                }
            )
            fragments.append(fragment)
        else:
            # Split large block
            # Try to preserve logical boundaries
            lines = content.split('\n')
            current_chunk = []
            current_size = 0
            
            for line in lines:
                line_size = len(line) + 1  # +1 for newline
                
                if current_size + line_size <= self.config.chunk_size or not current_chunk:
                    current_chunk.append(line)
                    current_size += line_size
                else:
                    # Create fragment from current chunk
                    fragment = TextFragment(
                        content='\n'.join(current_chunk),
                        boundary_type=BoundaryType.LINE,
                        content_type=ContentType.CODE,
                        metadata={
                            **(metadata or {}),
                            'code_type': block['type'],
                            'code_name': block['name'],
                            'start_line': block.get('start_line', 0)
                        }
                    )
                    fragments.append(fragment)
                    
                    # Start new chunk
                    current_chunk = [line]
                    current_size = line_size
            
            # Add remaining chunk
            if current_chunk:
                fragment = TextFragment(
                    content='\n'.join(current_chunk),
                    boundary_type=BoundaryType.LINE,
                    content_type=ContentType.CODE,
                    metadata={
                        **(metadata or {}),
                        'code_type': block['type'],
                        'code_name': block['name'],
                        'start_line': block.get('start_line', 0)
                    }
                )
                fragments.append(fragment)
        
        return fragments


class TokenSplitter(TextSplitter):
    """
    Token-based text splitter.
    
    Splits text based on token count using tiktoken or similar tokenizer.
    """
    
    def __init__(self, config: SplitterConfig):
        super().__init__(config)
        self.tokenizer = None
        
        try:
            import tiktoken
            model = config.custom_separators[0] if config.custom_separators else "gpt-3.5-turbo"
            self.tokenizer = tiktoken.encoding_for_model(model)
        except ImportError:
            logger.warning("tiktoken not available, falling back to word-based tokenization")
        except Exception as e:
            logger.warning(f"Failed to initialize tiktoken: {e}")
    
    async def split_text(
        self,
        text: str,
        source_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[TextFragment]:
        """Split text by token count."""
        start_time = time.time()
        
        if not text.strip():
            return []
        
        if self.tokenizer:
            fragments = await self._split_by_tokens(text, source_id, metadata)
        else:
            fragments = await self._split_by_words(text, source_id, metadata)
        
        # Update totals
        fragments = self.update_fragment_totals(fragments)
        
        # Performance tracking
        self._split_count += 1
        self._total_processing_time += time.time() - start_time
        
        return fragments
    
    async def _split_by_tokens(
        self,
        text: str,
        source_id: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ) -> List[TextFragment]:
        """Split using actual tokenizer."""
        tokens = self.tokenizer.encode(text)
        
        fragments = []
        start_idx = 0
        
        while start_idx < len(tokens):
            # Determine end index
            end_idx = min(start_idx + self.config.chunk_size, len(tokens))
            
            # Extract chunk tokens
            chunk_tokens = tokens[start_idx:end_idx]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            
            # Create fragment
            fragment = TextFragment(
                content=chunk_text,
                boundary_type=BoundaryType.TOKEN,
                metadata={
                    **(metadata or {}),
                    'token_count': len(chunk_tokens),
                    'token_start': start_idx,
                    'token_end': end_idx
                }
            )
            fragments.append(fragment)
            
            # Apply overlap
            start_idx = end_idx - self.config.chunk_overlap if self.config.chunk_overlap > 0 else end_idx
        
        return fragments
    
    async def _split_by_words(
        self,
        text: str,
        source_id: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ) -> List[TextFragment]:
        """Fallback word-based splitting."""
        words = text.split()
        
        fragments = []
        start_idx = 0
        
        while start_idx < len(words):
            end_idx = min(start_idx + self.config.chunk_size, len(words))
            
            chunk_words = words[start_idx:end_idx]
            chunk_text = ' '.join(chunk_words)
            
            fragment = TextFragment(
                content=chunk_text,
                boundary_type=BoundaryType.WORD,
                metadata={
                    **(metadata or {}),
                    'word_count': len(chunk_words),
                    'word_start': start_idx,
                    'word_end': end_idx
                }
            )
            fragments.append(fragment)
            
            start_idx = end_idx - self.config.chunk_overlap if self.config.chunk_overlap > 0 else end_idx
        
        return fragments


class SemanticSplitter(TextSplitter):
    """
    Semantic text splitter.
    
    Splits text based on semantic similarity between sentences/paragraphs.
    """
    
    def __init__(self, config: SplitterConfig):
        super().__init__(config)
        self.embeddings_model = None
        
        # Initialize embeddings if configured
        if config.enable_embedding and config.embedding_model:
            self._initialize_embeddings(config.embedding_model)
    
    def _initialize_embeddings(self, model_name: str):
        """Initialize embeddings model."""
        try:
            # Try to use sentence transformers
            from sentence_transformers import SentenceTransformer
            self.embeddings_model = SentenceTransformer(model_name)
        except ImportError:
            logger.warning("sentence-transformers not available for semantic splitting")
    
    async def split_text(
        self,
        text: str,
        source_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[TextFragment]:
        """Split text based on semantic similarity."""
        start_time = time.time()
        
        if not text.strip() or not self.embeddings_model:
            # Fallback to sentence splitting
            sentence_splitter = SentenceSplitter(self.config)
            return await sentence_splitter.split_text(text, source_id, metadata)
        
        # Split into sentences first
        sentences = self._split_into_sentences(text)
        
        if len(sentences) <= 1:
            return [TextFragment(content=text, boundary_type=BoundaryType.SEMANTIC)]
        
        # Calculate semantic similarity between sentences
        similarities = await self._calculate_semantic_similarities(sentences)
        
        # Group sentences based on similarity
        groups = self._group_by_similarity(sentences, similarities)
        
        # Create fragments from groups
        fragments = []
        for i, group in enumerate(groups):
            content = ' '.join(group['sentences'])
            
            fragment = TextFragment(
                content=content,
                boundary_type=BoundaryType.SEMANTIC,
                metadata={
                    **(metadata or {}),
                    'semantic_coherence': group['avg_similarity'],
                    'sentence_count': len(group['sentences'])
                }
            )
            fragments.append(fragment)
        
        # Update totals
        fragments = self.update_fragment_totals(fragments)
        
        # Performance tracking
        self._split_count += 1
        self._total_processing_time += time.time() - start_time
        
        return fragments
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        import re
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    async def _calculate_semantic_similarities(self, sentences: List[str]) -> List[float]:
        """Calculate semantic similarities between adjacent sentences."""
        if not self.embeddings_model or len(sentences) <= 1:
            return [1.0] * (len(sentences) - 1)
        
        # Get embeddings for all sentences
        embeddings = self.embeddings_model.encode(sentences)
        
        # Calculate cosine similarities between adjacent sentences
        similarities = []
        for i in range(len(embeddings) - 1):
            similarity = self._cosine_similarity(embeddings[i], embeddings[i + 1])
            similarities.append(similarity)
        
        return similarities
    
    def _cosine_similarity(self, a, b):
        """Calculate cosine similarity between two vectors."""
        import numpy as np
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def _group_by_similarity(
        self, 
        sentences: List[str], 
        similarities: List[float]
    ) -> List[Dict[str, Any]]:
        """Group sentences based on semantic similarity."""
        groups = []
        current_group = [sentences[0]]
        current_similarities = []
        
        for i, similarity in enumerate(similarities):
            if similarity >= self.config.semantic_threshold and \
               len(' '.join(current_group + [sentences[i + 1]])) <= self.config.chunk_size:
                # Add to current group
                current_group.append(sentences[i + 1])
                current_similarities.append(similarity)
            else:
                # Start new group
                avg_similarity = sum(current_similarities) / len(current_similarities) if current_similarities else 1.0
                groups.append({
                    'sentences': current_group,
                    'avg_similarity': avg_similarity
                })
                
                current_group = [sentences[i + 1]]
                current_similarities = []
        
        # Add last group
        if current_group:
            avg_similarity = sum(current_similarities) / len(current_similarities) if current_similarities else 1.0
            groups.append({
                'sentences': current_group,
                'avg_similarity': avg_similarity
            })
        
        return groups