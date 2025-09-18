"""
Smart Retrieval System
======================

Advanced retrieval system with adaptive retry logic, sufficiency checking,
and hybrid metadata+content filtering for chatbot knowledge access.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass

from .config import RetrievalStrategy, RetrievalConfig, KnowledgeMode
from .knowledge import KnowledgeManager, RetrievalResult, ChunkMetadata
from ..retrievers.base import AsyncRetriever


logger = logging.getLogger(__name__)


@dataclass
class RetrievalAttempt:
    """Tracks information about a retrieval attempt."""
    
    attempt_number: int
    query: str
    strategy: str
    results_count: int
    max_similarity: float
    sufficiency_score: float
    filters_used: Dict[str, Any]
    success: bool
    error: Optional[str] = None


class SufficiencyChecker:
    """Checks if retrieved content is sufficient to answer a query."""
    
    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold
    
    async def check_sufficiency(
        self,
        query: str,
        results: List[RetrievalResult],
        min_results: int = 2
    ) -> Tuple[bool, float, str]:
        """
        Check if the retrieval results are sufficient to answer the query.
        
        Returns:
            (is_sufficient, confidence_score, reasoning)
        """
        if not results:
            return False, 0.0, "No retrieval results found"
        
        # Basic checks
        if len(results) < min_results:
            return False, 0.3, f"Only {len(results)} results found, minimum {min_results} needed"
        
        # Calculate sufficiency based on multiple factors
        factors = {}
        
        # 1. Similarity scores
        avg_similarity = sum(r.similarity_score for r in results) / len(results)
        max_similarity = max(r.similarity_score for r in results)
        factors['similarity'] = (avg_similarity + max_similarity) / 2
        
        # 2. Content coverage (simplified)
        total_content_length = sum(len(r.content) for r in results)
        factors['content_coverage'] = min(1.0, total_content_length / 1000)  # Normalize by expected content length
        
        # 3. Source diversity
        unique_sources = len(set(r.chunk_metadata.source_name for r in results))
        factors['source_diversity'] = min(1.0, unique_sources / 3)  # Normalize by expected source count
        
        # 4. Information density
        avg_density = sum(r.chunk_metadata.information_density for r in results) / len(results)
        factors['information_density'] = avg_density
        
        # 5. Query-content matching (simplified)
        query_words = set(query.lower().split())
        content_words = set()
        for result in results:
            content_words.update(result.content.lower().split())
        
        word_overlap = len(query_words.intersection(content_words)) / max(len(query_words), 1)
        factors['query_match'] = word_overlap
        
        # Weighted combination
        weights = {
            'similarity': 0.3,
            'content_coverage': 0.2,
            'source_diversity': 0.15,
            'information_density': 0.15,
            'query_match': 0.2
        }
        
        confidence = sum(factors[key] * weights[key] for key in factors)
        
        # Generate reasoning
        reasoning_parts = []
        for factor, score in factors.items():
            if score > 0.7:
                reasoning_parts.append(f"Good {factor.replace('_', ' ')} ({score:.2f})")
            elif score < 0.4:
                reasoning_parts.append(f"Low {factor.replace('_', ' ')} ({score:.2f})")
        
        reasoning = f"Confidence: {confidence:.2f}. " + ", ".join(reasoning_parts)
        
        return confidence >= self.threshold, confidence, reasoning


class SmartRetriever:
    """
    Smart retrieval system with adaptive strategies and retry logic.
    """
    
    def __init__(
        self,
        knowledge_manager: KnowledgeManager,
        base_retriever: Optional[AsyncRetriever],
        config: RetrievalConfig
    ):
        self.knowledge_manager = knowledge_manager
        self.base_retriever = base_retriever
        self.config = config
        self.sufficiency_checker = SufficiencyChecker(config.sufficiency_threshold)
        
        # Track retrieval attempts for debugging
        self.last_attempts: List[RetrievalAttempt] = []
    
    async def retrieve(
        self,
        query: str,
        conversation_context: Optional[str] = None,
        knowledge_mode: KnowledgeMode = KnowledgeMode.HYBRID
    ) -> Tuple[List[RetrievalResult], Dict[str, Any]]:
        """
        Perform smart retrieval with adaptive strategies and retry logic.
        
        Returns:
            (retrieval_results, metadata_info)
        """
        self.last_attempts = []
        
        logger.info(f"Starting smart retrieval for query: '{query[:50]}...'")
        
        # Determine retrieval strategy based on config and query
        strategy = self._determine_strategy(query, conversation_context)
        
        # Attempt retrieval with different approaches
        for attempt in range(self.config.max_attempts):
            try:
                results, metadata = await self._attempt_retrieval(
                    query=query,
                    attempt_number=attempt + 1,
                    strategy=strategy,
                    conversation_context=conversation_context,
                    knowledge_mode=knowledge_mode
                )
                
                # Check sufficiency if enabled
                if self.config.enable_sufficiency_check and results:
                    sufficient, confidence, reasoning = await self.sufficiency_checker.check_sufficiency(
                        query, results
                    )
                    
                    metadata['sufficiency'] = {
                        'is_sufficient': sufficient,
                        'confidence': confidence,
                        'reasoning': reasoning
                    }
                    
                    if sufficient:
                        logger.info(f"Retrieval successful after {attempt + 1} attempts")
                        return results, metadata
                    else:
                        logger.info(f"Attempt {attempt + 1} insufficient: {reasoning}")
                        
                        # If not sufficient and we have more attempts, modify strategy
                        if attempt + 1 < self.config.max_attempts:
                            strategy = self._adapt_strategy(strategy, attempt + 1, confidence)
                            continue
                
                # If sufficiency check is disabled or this is the last attempt, return what we have
                if not self.config.enable_sufficiency_check or attempt + 1 == self.config.max_attempts:
                    logger.info(f"Returning results after {attempt + 1} attempts (sufficiency check: {self.config.enable_sufficiency_check})")
                    return results, metadata
                    
            except Exception as e:
                logger.error(f"Retrieval attempt {attempt + 1} failed: {e}")
                
                # Record failed attempt
                self.last_attempts.append(RetrievalAttempt(
                    attempt_number=attempt + 1,
                    query=query,
                    strategy=strategy.value if hasattr(strategy, 'value') else str(strategy),
                    results_count=0,
                    max_similarity=0.0,
                    sufficiency_score=0.0,
                    filters_used={},
                    success=False,
                    error=str(e)
                ))
                
                if attempt + 1 == self.config.max_attempts:
                    return [], {'error': f"All retrieval attempts failed: {e}"}
        
        return [], {'error': "Maximum retrieval attempts exceeded"}
    
    def _determine_strategy(
        self,
        query: str,
        conversation_context: Optional[str] = None
    ) -> RetrievalStrategy:
        """Determine the best retrieval strategy for the query."""
        
        # Use configured strategy if not adaptive
        if self.config.strategy != RetrievalStrategy.ADAPTIVE:
            return self.config.strategy
        
        # Adaptive strategy selection based on query characteristics
        query_words = query.lower().split()
        
        # If query is very specific (contains specific terms), use simple strategy
        specific_indicators = ['what is', 'define', 'explain', 'how many', 'when did']
        if any(indicator in query.lower() for indicator in specific_indicators):
            return RetrievalStrategy.SIMPLE
        
        # If query is broad or exploratory, use progressive strategy
        broad_indicators = ['tell me about', 'overview', 'summary', 'introduction']
        if any(indicator in query.lower() for indicator in broad_indicators):
            return RetrievalStrategy.PROGRESSIVE
        
        # If conversation context suggests related queries, use multi-hop
        if conversation_context and len(conversation_context) > 100:
            return RetrievalStrategy.MULTI_HOP
        
        # Default to adaptive
        return RetrievalStrategy.SIMPLE
    
    def _adapt_strategy(
        self,
        current_strategy: RetrievalStrategy,
        attempt_number: int,
        confidence: float
    ) -> RetrievalStrategy:
        """Adapt retrieval strategy based on previous attempt results."""
        
        if confidence < 0.3:
            # Very low confidence, try a broader approach
            if current_strategy == RetrievalStrategy.SIMPLE:
                return RetrievalStrategy.PROGRESSIVE
            elif current_strategy == RetrievalStrategy.PROGRESSIVE:
                return RetrievalStrategy.MULTI_HOP
        
        elif confidence < 0.5:
            # Medium confidence, try different approach
            if current_strategy == RetrievalStrategy.SIMPLE:
                return RetrievalStrategy.MULTI_HOP
            else:
                return RetrievalStrategy.SIMPLE
        
        # If confidence is decent but still not sufficient, keep same strategy but relax filters
        return current_strategy
    
    async def _attempt_retrieval(
        self,
        query: str,
        attempt_number: int,
        strategy: RetrievalStrategy,
        conversation_context: Optional[str],
        knowledge_mode: KnowledgeMode
    ) -> Tuple[List[RetrievalResult], Dict[str, Any]]:
        """Perform a single retrieval attempt."""
        
        logger.debug(f"Attempt {attempt_number} using strategy: {strategy}")
        
        # Prepare metadata filters
        filters = self._prepare_filters(attempt_number, query, conversation_context)
        
        # Modify query based on strategy
        search_queries = self._prepare_queries(query, strategy, conversation_context)
        
        all_results = []
        retrieval_metadata = {
            'attempt_number': attempt_number,
            'strategy': strategy.value if hasattr(strategy, 'value') else str(strategy),
            'queries_used': search_queries,
            'filters_applied': filters
        }
        
        # Perform retrieval for each query
        for search_query in search_queries:
            try:
                # Apply metadata filtering if enabled
                candidate_chunks = self.knowledge_manager.chunks
                if self.config.enable_metadata_filtering and filters:
                    candidate_chunks = self.knowledge_manager.get_chunks_with_metadata_filter(filters)
                
                # Use base retriever on filtered candidates
                if candidate_chunks:
                    # Convert to format expected by base retriever
                    retrieval_results = await self._retrieve_from_chunks(
                        query=search_query,
                        chunks=candidate_chunks,
                        max_results=self.config.max_chunks_total // len(search_queries)
                    )
                    
                    all_results.extend(retrieval_results)
                
            except Exception as e:
                logger.error(f"Error retrieving for query '{search_query}': {e}")
        
        # Sort by similarity and limit results
        all_results.sort(key=lambda x: x.similarity_score, reverse=True)
        final_results = all_results[:self.config.max_chunks_total]
        
        # Record attempt
        max_similarity = max((r.similarity_score for r in final_results), default=0.0)
        
        attempt = RetrievalAttempt(
            attempt_number=attempt_number,
            query=query,
            strategy=strategy.value if hasattr(strategy, 'value') else str(strategy),
            results_count=len(final_results),
            max_similarity=max_similarity,
            sufficiency_score=0.0,  # Will be updated after sufficiency check
            filters_used=filters,
            success=len(final_results) > 0
        )
        
        self.last_attempts.append(attempt)
        
        retrieval_metadata['results_count'] = len(final_results)
        retrieval_metadata['max_similarity'] = max_similarity
        
        return final_results, retrieval_metadata
    
    def _prepare_filters(
        self,
        attempt_number: int,
        query: str,
        conversation_context: Optional[str]
    ) -> Dict[str, Any]:
        """Prepare metadata filters for this attempt."""
        
        filters = {}
        
        # Start with configured filters
        filters.update(self.config.metadata_filters)
        
        # Relax filters on subsequent attempts
        if attempt_number > 1:
            # Remove strict filters
            filters.pop('min_readability', None)
            if attempt_number > 2:
                filters.pop('section', None)
        
        # Add query-based filters (simplified)
        # This could be much more sophisticated with NLP
        query_lower = query.lower()
        
        # Domain detection (very basic)
        science_terms = ['cell', 'atom', 'evolution', 'species', 'quantum', 'chemical', 'biology']
        if any(term in query_lower for term in science_terms):
            if attempt_number == 1:  # Only apply on first attempt
                filters['domain'] = 'science'
        
        return filters
    
    def _prepare_queries(
        self,
        original_query: str,
        strategy: RetrievalStrategy,
        conversation_context: Optional[str]
    ) -> List[str]:
        """Prepare search queries based on strategy."""
        
        queries = [original_query]
        
        if strategy == RetrievalStrategy.SIMPLE:
            return queries
        
        elif strategy == RetrievalStrategy.PROGRESSIVE:
            # Add broader and more specific versions
            words = original_query.split()
            if len(words) > 2:
                # Broader query (remove some words)
                broader = ' '.join(words[:len(words)//2])
                queries.append(broader)
            
            # Add key terms
            key_terms = self._extract_key_terms(original_query)
            for term in key_terms[:2]:  # Limit to 2 additional terms
                queries.append(term)
        
        elif strategy == RetrievalStrategy.MULTI_HOP:
            # Add context-based queries
            if conversation_context:
                context_terms = self._extract_key_terms(conversation_context)
                for term in context_terms[:2]:
                    queries.append(f"{original_query} {term}")
        
        return queries[:3]  # Limit total queries
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text (simplified)."""
        # This is a very basic implementation
        # In practice, you'd use NLP libraries for better term extraction
        
        words = text.lower().split()
        
        # Filter common words (basic stop words)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can'}
        
        key_terms = [word for word in words if len(word) > 3 and word not in stop_words]
        
        # Sort by length (longer terms first) and return top terms
        key_terms.sort(key=len, reverse=True)
        
        return key_terms[:5]
    
    async def _retrieve_from_chunks(
        self,
        query: str,
        chunks: List[Tuple[str, ChunkMetadata]],
        max_results: int
    ) -> List[RetrievalResult]:
        """Retrieve from filtered chunks using the base retriever."""
        
        results = []
        
        # Simple similarity-based retrieval (in practice, you'd use the base_retriever)
        # For now, we'll do basic keyword matching as a placeholder
        
        query_terms = set(query.lower().split())
        
        for content, metadata in chunks:
            content_terms = set(content.lower().split())
            
            # Calculate simple similarity
            intersection = query_terms.intersection(content_terms)
            similarity = len(intersection) / max(len(query_terms), 1)
            
            if similarity >= self.config.min_similarity:
                result = self.knowledge_manager.create_retrieval_result(
                    content=content,
                    chunk_metadata=metadata,
                    similarity_score=similarity,
                    retrieval_method="keyword_matching"
                )
                results.append(result)
        
        # Sort by similarity and return top results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:max_results]
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get statistics about recent retrieval attempts."""
        if not self.last_attempts:
            return {"message": "No recent retrieval attempts"}
        
        successful_attempts = [a for a in self.last_attempts if a.success]
        
        return {
            "total_attempts": len(self.last_attempts),
            "successful_attempts": len(successful_attempts),
            "average_results": sum(a.results_count for a in self.last_attempts) / len(self.last_attempts),
            "max_similarity": max((a.max_similarity for a in self.last_attempts), default=0.0),
            "strategies_used": list(set(a.strategy for a in self.last_attempts)),
            "last_attempt": {
                "query": self.last_attempts[-1].query,
                "success": self.last_attempts[-1].success,
                "results_count": self.last_attempts[-1].results_count
            }
        }