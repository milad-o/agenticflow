"""
Text-Based Retrievers

Implements various text-based search strategies that can work with any text corpus
or data source containing textual content.
"""

import re
import math
import time
from typing import Any, Dict, List, Optional, Set
from collections import Counter, defaultdict

import structlog
from pydantic import BaseModel

from .base import DataSourceRetriever, RetrieverResult, RetrieverConfig, RetrieverType
from ..memory.core import MemoryDocument

logger = structlog.get_logger(__name__)


class KeywordRetrieverConfig(RetrieverConfig):
    """Configuration for keyword-based retrieval."""
    
    case_sensitive: bool = False
    whole_words_only: bool = False
    boost_exact_matches: bool = True
    min_word_length: int = 2


class FullTextRetrieverConfig(RetrieverConfig):
    """Configuration for full-text search retrieval."""
    
    use_stemming: bool = True
    remove_stopwords: bool = True
    boost_title_matches: bool = True
    phrase_search: bool = True


class BM25RetrieverConfig(RetrieverConfig):
    """Configuration for BM25 retrieval."""
    
    k1: float = 1.2  # Term frequency saturation parameter
    b: float = 0.75  # Length normalization parameter
    epsilon: float = 0.25  # IDF normalization parameter
    use_stemming: bool = True
    remove_stopwords: bool = True


class FuzzyRetrieverConfig(RetrieverConfig):
    """Configuration for fuzzy text retrieval."""
    
    max_edit_distance: int = 2
    algorithm: str = "levenshtein"  # "levenshtein", "damerau", "jaro_winkler"
    fuzzy_threshold: float = 0.8
    boost_exact_matches: bool = True


class RegexRetrieverConfig(RetrieverConfig):
    """Configuration for regex-based retrieval."""
    
    ignore_case: bool = True
    multiline: bool = True
    dotall: bool = False
    compile_patterns: bool = True


class KeywordRetriever(DataSourceRetriever):
    """Simple keyword-based text retrieval."""
    
    def __init__(self, data_source: Any, config: KeywordRetrieverConfig = None):
        config = config or KeywordRetrieverConfig()
        super().__init__(data_source, config)
        self.config: KeywordRetrieverConfig = config
    
    def _get_retriever_type(self) -> str:
        return RetrieverType.KEYWORD
    
    async def _retrieve_impl(
        self,
        query: str,
        limit: int,
        **kwargs
    ) -> List[RetrieverResult]:
        """Implement keyword-based retrieval."""
        
        # Get documents from data source
        documents = await self._get_documents_from_data_source()
        
        # Prepare query terms
        query_terms = self._prepare_query_terms(query)
        if not query_terms:
            return []
        
        # Score documents
        scored_results = []
        for doc in documents:
            score = self._calculate_keyword_score(doc.content, query_terms, query)
            if score > 0:
                result = RetrieverResult(
                    document=doc,
                    score=score,
                    retriever_type=self.retriever_type
                )
                scored_results.append(result)
        
        # Sort by score and return top results
        scored_results.sort(key=lambda x: x.score, reverse=True)
        return scored_results[:limit]
    
    def _prepare_query_terms(self, query: str) -> List[str]:
        """Prepare query terms for searching."""
        if not self.config.case_sensitive:
            query = query.lower()
        
        # Simple tokenization
        terms = re.findall(r'\b\w+\b', query)
        
        # Filter by minimum word length
        terms = [t for t in terms if len(t) >= self.config.min_word_length]
        
        return terms
    
    def _calculate_keyword_score(self, content: str, query_terms: List[str], original_query: str) -> float:
        """Calculate keyword-based relevance score."""
        if not self.config.case_sensitive:
            content = content.lower()
        
        score = 0.0
        
        # Exact query match gets highest boost
        if self.config.boost_exact_matches and original_query.lower() in content.lower():
            score += 2.0
        
        # Score based on term matches
        content_words = set(re.findall(r'\b\w+\b', content))
        
        for term in query_terms:
            if self.config.whole_words_only:
                if term in content_words:
                    score += 1.0
            else:
                if term in content:
                    score += 1.0
            
            # Bonus for multiple occurrences
            occurrences = content.count(term)
            if occurrences > 1:
                score += math.log(occurrences) * 0.5
        
        # Normalize by content length to avoid bias toward longer documents
        if len(content) > 0:
            score = score / math.log(len(content) + 1)
        
        return score
    
    async def _get_documents_from_data_source(self) -> List[MemoryDocument]:
        """Extract documents from data source."""
        documents = []
        
        if hasattr(self.data_source, 'get_messages'):
            # Memory instance
            messages = await self.data_source.get_messages()
            for i, msg in enumerate(messages):
                doc = MemoryDocument(
                    id=f"msg_{i}",
                    content=msg.content if hasattr(msg, 'content') else str(msg),
                    metadata={},
                    timestamp=time.time()
                )
                documents.append(doc)
        
        elif hasattr(self.data_source, 'documents'):
            # Direct access to documents list (like our demo class)
            documents = self.data_source.documents
        
        elif hasattr(self.data_source, 'search'):
            # Try to get all documents via search with empty query
            try:
                all_results = await self.data_source.search("", limit=1000)
                # Convert results to documents if needed
                for result in all_results:
                    if isinstance(result, MemoryDocument):
                        documents.append(result)
                    else:
                        # Try to extract content from result
                        content = getattr(result, 'content', str(result))
                        doc_id = getattr(result, 'id', f"doc_{len(documents)}")
                        metadata = getattr(result, 'metadata', {})
                        timestamp = getattr(result, 'timestamp', time.time())
                        
                        doc = MemoryDocument(
                            id=doc_id,
                            content=content,
                            metadata=metadata,
                            timestamp=timestamp
                        )
                        documents.append(doc)
            except Exception as e:
                self.logger.warning(f"Failed to get documents via search: {e}")
        
        return documents


class FullTextRetriever(KeywordRetriever):
    """Full-text search retrieval with advanced text processing."""
    
    def __init__(self, data_source: Any, config: FullTextRetrieverConfig = None):
        # Convert to KeywordRetrieverConfig for base functionality
        keyword_config = KeywordRetrieverConfig(
            similarity_threshold=config.similarity_threshold if config else 0.7,
            max_results=config.max_results if config else 10,
            case_sensitive=False,
            whole_words_only=True
        )
        super().__init__(data_source, keyword_config)
        self.config: FullTextRetrieverConfig = config or FullTextRetrieverConfig()
        
        # Load stopwords if needed
        self.stopwords = self._load_stopwords() if self.config.remove_stopwords else set()
    
    def _get_retriever_type(self) -> str:
        return RetrieverType.FULLTEXT
    
    def _load_stopwords(self) -> Set[str]:
        """Load common English stopwords."""
        return {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'would', 'you', 'your', 'i', 'me',
            'my', 'we', 'our', 'they', 'them', 'their', 'this', 'these',
            'those', 'but', 'or', 'if', 'can', 'could', 'should', 'do', 'does'
        }
    
    async def _retrieve_impl(
        self,
        query: str,
        limit: int,
        **kwargs
    ) -> List[RetrieverResult]:
        """Implement full-text retrieval."""
        
        # Get documents from data source
        documents = await self._get_documents_from_data_source()
        
        # Process query
        query_terms = self._process_text(query)
        if not query_terms:
            return []
        
        # Score documents
        scored_results = []
        for doc in documents:
            score = self._calculate_fulltext_score(doc.content, query_terms, query)
            if score > 0:
                result = RetrieverResult(
                    document=doc,
                    score=score,
                    retriever_type=self.retriever_type
                )
                scored_results.append(result)
        
        scored_results.sort(key=lambda x: x.score, reverse=True)
        return scored_results[:limit]
    
    def _process_text(self, text: str) -> List[str]:
        """Process text for full-text search."""
        # Convert to lowercase
        text = text.lower()
        
        # Extract words
        words = re.findall(r'\b\w+\b', text)
        
        # Remove stopwords
        if self.config.remove_stopwords:
            words = [w for w in words if w not in self.stopwords]
        
        # Simple stemming (just remove common suffixes)
        if self.config.use_stemming:
            words = [self._simple_stem(w) for w in words]
        
        return words
    
    def _simple_stem(self, word: str) -> str:
        """Simple stemming by removing common suffixes."""
        suffixes = ['ing', 'ed', 'er', 'est', 'ly', 's']
        for suffix in suffixes:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                return word[:-len(suffix)]
        return word
    
    def _calculate_fulltext_score(self, content: str, query_terms: List[str], original_query: str) -> float:
        """Calculate full-text relevance score."""
        content_terms = self._process_text(content)
        content_counter = Counter(content_terms)
        
        score = 0.0
        
        # TF-IDF-like scoring
        for term in query_terms:
            tf = content_counter.get(term, 0)
            if tf > 0:
                # Term frequency with diminishing returns
                score += math.log(1 + tf)
        
        # Phrase search boost
        if self.config.phrase_search and original_query.lower() in content.lower():
            score += 1.0
        
        # Title boost (if content has structure)
        if self.config.boost_title_matches:
            # Simple heuristic: boost if query appears in first 100 characters
            if original_query.lower() in content.lower()[:100]:
                score += 0.5
        
        return score
    


class BM25Retriever(DataSourceRetriever):
    """BM25 (Best Matching 25) retrieval algorithm."""
    
    def __init__(self, data_source: Any, config: BM25RetrieverConfig = None):
        config = config or BM25RetrieverConfig()
        super().__init__(data_source, config)
        self.config: BM25RetrieverConfig = config
        
        # Document corpus for IDF calculation
        self.corpus = []
        self.document_frequencies = {}
        self.average_doc_length = 0.0
        self._corpus_built = False
    
    def _get_retriever_type(self) -> str:
        return RetrieverType.BM25
    
    async def _retrieve_impl(
        self,
        query: str,
        limit: int,
        **kwargs
    ) -> List[RetrieverResult]:
        """Implement BM25 retrieval."""
        
        # Build corpus if not already built
        if not self._corpus_built:
            await self._build_corpus()
        
        # Process query
        query_terms = self._process_text(query)
        if not query_terms:
            return []
        
        # Calculate BM25 scores
        scored_results = []
        for i, (doc, doc_terms) in enumerate(self.corpus):
            score = self._calculate_bm25_score(doc_terms, query_terms)
            if score > 0:
                result = RetrieverResult(
                    document=doc,
                    score=score,
                    retriever_type=self.retriever_type
                )
                scored_results.append(result)
        
        scored_results.sort(key=lambda x: x.score, reverse=True)
        return scored_results[:limit]
    
    async def _build_corpus(self):
        """Build document corpus for BM25 calculation."""
        documents = await self._get_documents_from_data_source()
        
        self.corpus = []
        doc_lengths = []
        all_terms = set()
        
        for doc in documents:
            doc_terms = self._process_text(doc.content)
            self.corpus.append((doc, Counter(doc_terms)))
            doc_lengths.append(len(doc_terms))
            all_terms.update(doc_terms)
        
        # Calculate average document length
        self.average_doc_length = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 0.0
        
        # Calculate document frequencies for IDF
        self.document_frequencies = {}
        for term in all_terms:
            df = sum(1 for _, doc_terms in self.corpus if term in doc_terms)
            self.document_frequencies[term] = df
        
        self._corpus_built = True
        self.logger.debug(f"Built BM25 corpus with {len(self.corpus)} documents")
    
    def _process_text(self, text: str) -> List[str]:
        """Process text for BM25."""
        # Simple text processing
        text = text.lower()
        words = re.findall(r'\b\w+\b', text)
        
        # Remove stopwords if configured
        if self.config.remove_stopwords:
            stopwords = {
                'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
                'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
                'to', 'was', 'will', 'with'
            }
            words = [w for w in words if w not in stopwords]
        
        return words
    
    def _calculate_bm25_score(self, doc_terms: Counter, query_terms: List[str]) -> float:
        """Calculate BM25 score for a document."""
        score = 0.0
        doc_length = sum(doc_terms.values())
        
        for term in query_terms:
            if term in doc_terms:
                # Term frequency
                tf = doc_terms[term]
                
                # Document frequency and IDF
                df = self.document_frequencies.get(term, 1)
                idf = math.log((len(self.corpus) - df + 0.5) / (df + 0.5) + self.config.epsilon)
                
                # BM25 formula
                numerator = tf * (self.config.k1 + 1)
                denominator = tf + self.config.k1 * (
                    1 - self.config.b + self.config.b * (doc_length / self.average_doc_length)
                )
                
                score += idf * (numerator / denominator)
        
        return score
    
    async def _get_documents_from_data_source(self) -> List[MemoryDocument]:
        """Extract documents from data source."""
        keyword_retriever = KeywordRetriever(self.data_source)
        return await keyword_retriever._get_documents_from_data_source()


class FuzzyRetriever(DataSourceRetriever):
    """Fuzzy text matching retrieval."""
    
    def __init__(self, data_source: Any, config: FuzzyRetrieverConfig = None):
        config = config or FuzzyRetrieverConfig()
        super().__init__(data_source, config)
        self.config: FuzzyRetrieverConfig = config
    
    def _get_retriever_type(self) -> str:
        return RetrieverType.FUZZY
    
    async def _retrieve_impl(
        self,
        query: str,
        limit: int,
        **kwargs
    ) -> List[RetrieverResult]:
        """Implement fuzzy retrieval."""
        
        documents = await self._get_documents_from_data_source()
        
        scored_results = []
        for doc in documents:
            score = self._calculate_fuzzy_score(doc.content, query)
            if score >= self.config.fuzzy_threshold:
                result = RetrieverResult(
                    document=doc,
                    score=score,
                    retriever_type=self.retriever_type
                )
                scored_results.append(result)
        
        scored_results.sort(key=lambda x: x.score, reverse=True)
        return scored_results[:limit]
    
    def _calculate_fuzzy_score(self, content: str, query: str) -> float:
        """Calculate fuzzy matching score."""
        # Simple implementation - could be enhanced with more sophisticated algorithms
        
        # Check exact match first
        if query.lower() in content.lower():
            return 1.0
        
        # Calculate edit distance for substrings
        query = query.lower()
        content = content.lower()
        
        best_score = 0.0
        query_len = len(query)
        
        # Sliding window approach
        for i in range(len(content) - query_len + 1):
            substring = content[i:i + query_len]
            distance = self._levenshtein_distance(query, substring)
            
            if distance <= self.config.max_edit_distance:
                score = 1.0 - (distance / max(len(query), len(substring)))
                best_score = max(best_score, score)
        
        return best_score
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    async def _get_documents_from_data_source(self) -> List[MemoryDocument]:
        """Extract documents from data source."""
        keyword_retriever = KeywordRetriever(self.data_source)
        return await keyword_retriever._get_documents_from_data_source()


class RegexRetriever(DataSourceRetriever):
    """Regular expression-based retrieval."""
    
    def __init__(self, data_source: Any, config: RegexRetrieverConfig = None):
        config = config or RegexRetrieverConfig()
        super().__init__(data_source, config)
        self.config: RegexRetrieverConfig = config
        self._compiled_patterns = {}
    
    def _get_retriever_type(self) -> str:
        return RetrieverType.REGEX
    
    async def _retrieve_impl(
        self,
        query: str,
        limit: int,
        **kwargs
    ) -> List[RetrieverResult]:
        """Implement regex retrieval."""
        
        documents = await self._get_documents_from_data_source()
        
        # Compile regex pattern
        pattern = self._compile_pattern(query)
        if not pattern:
            return []
        
        scored_results = []
        for doc in documents:
            score = self._calculate_regex_score(doc.content, pattern)
            if score > 0:
                result = RetrieverResult(
                    document=doc,
                    score=score,
                    retriever_type=self.retriever_type
                )
                scored_results.append(result)
        
        scored_results.sort(key=lambda x: x.score, reverse=True)
        return scored_results[:limit]
    
    def _compile_pattern(self, query: str):
        """Compile regex pattern with caching."""
        if query in self._compiled_patterns:
            return self._compiled_patterns[query]
        
        try:
            flags = 0
            if self.config.ignore_case:
                flags |= re.IGNORECASE
            if self.config.multiline:
                flags |= re.MULTILINE
            if self.config.dotall:
                flags |= re.DOTALL
            
            pattern = re.compile(query, flags)
            
            if self.config.compile_patterns:
                self._compiled_patterns[query] = pattern
            
            return pattern
        
        except re.error as e:
            self.logger.warning(f"Invalid regex pattern '{query}': {e}")
            return None
    
    def _calculate_regex_score(self, content: str, pattern) -> float:
        """Calculate regex matching score."""
        matches = pattern.findall(content)
        if not matches:
            return 0.0
        
        # Score based on number and quality of matches
        score = len(matches)
        
        # Bonus for matches at beginning of content
        if pattern.match(content):
            score += 0.5
        
        # Normalize by content length
        score = score / math.log(len(content) + 1)
        
        return min(score, 1.0)  # Cap at 1.0
    
    async def _get_documents_from_data_source(self) -> List[MemoryDocument]:
        """Extract documents from data source."""
        keyword_retriever = KeywordRetriever(self.data_source)
        return await keyword_retriever._get_documents_from_data_source()