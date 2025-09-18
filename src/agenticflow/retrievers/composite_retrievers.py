"""
Composite Retrievers

Implements advanced retrievers that combine multiple retrieval strategies
for better performance through ensembles, fusion, and reranking.
"""

import asyncio
import math
import time
from typing import Any, Dict, List, Optional, Union, Callable
from collections import defaultdict

import structlog
from pydantic import BaseModel

from .base import AsyncRetriever, RetrieverResult, RetrieverConfig, RetrieverType
from ..memory.core import MemoryDocument

logger = structlog.get_logger(__name__)


class EnsembleRetrieverConfig(RetrieverConfig):
    """Configuration for ensemble retrieval."""
    
    fusion_method: str = "weighted_sum"  # "weighted_sum", "rank_fusion", "max", "min"
    retriever_weights: Optional[Dict[str, float]] = None
    min_retrievers: int = 1  # Minimum retrievers that must return results
    normalize_scores: bool = True
    enable_diversity: bool = True
    diversity_threshold: float = 0.8


class HybridRetrieverConfig(RetrieverConfig):
    """Configuration for hybrid dense-sparse retrieval."""
    
    dense_weight: float = 0.7
    sparse_weight: float = 0.3
    alpha: float = 0.5  # Interpolation parameter
    normalize_before_fusion: bool = True


class ContextualRetrieverConfig(RetrieverConfig):
    """Configuration for contextual retrieval."""
    
    context_window: int = 5  # Number of surrounding documents to consider
    context_weight: float = 0.3
    use_conversation_history: bool = True
    max_history_length: int = 10


class FusionRetrieverConfig(RetrieverConfig):
    """Configuration for score fusion and reranking."""
    
    fusion_strategies: List[str] = ["rrf", "weighted_sum"]  # RRF = Reciprocal Rank Fusion
    rerank_top_k: int = 50  # Rerank top K results
    rrf_k: int = 60  # RRF parameter
    enable_neural_rerank: bool = False


class EnsembleRetriever(AsyncRetriever):
    """Combines multiple retrievers using various fusion methods."""
    
    def __init__(self, retrievers: List[AsyncRetriever], config: EnsembleRetrieverConfig = None):
        config = config or EnsembleRetrieverConfig()
        super().__init__(config)
        self.config: EnsembleRetrieverConfig = config
        self.retrievers = retrievers
        
        # Set default weights if not provided
        if not self.config.retriever_weights:
            weight = 1.0 / len(retrievers)
            self.config.retriever_weights = {
                retriever.retriever_type: weight for retriever in retrievers
            }
    
    def _get_retriever_type(self) -> str:
        return RetrieverType.ENSEMBLE
    
    async def _retrieve_impl(
        self,
        query: str,
        limit: int,
        **kwargs
    ) -> List[RetrieverResult]:
        """Implement ensemble retrieval."""
        
        # Run all retrievers concurrently
        retriever_tasks = []
        for retriever in self.retrievers:
            task = retriever.retrieve(query, limit=limit * 2, **kwargs)  # Get more results for fusion
            retriever_tasks.append((retriever, task))
        
        # Collect results from all retrievers
        retriever_results = {}
        successful_retrievers = 0
        
        for retriever, task in retriever_tasks:
            try:
                results = await task
                if results:
                    retriever_results[retriever.retriever_type] = results
                    successful_retrievers += 1
            except Exception as e:
                self.logger.warning(f"Retriever {retriever.retriever_type} failed: {e}")
        
        # Check minimum retrievers requirement
        if successful_retrievers < self.config.min_retrievers:
            self.logger.warning(f"Only {successful_retrievers} retrievers succeeded, minimum is {self.config.min_retrievers}")
            return []
        
        # Fuse results
        fused_results = self._fuse_results(retriever_results, query)
        
        # Apply diversity filtering if enabled
        if self.config.enable_diversity:
            fused_results = self._apply_diversity_filter(fused_results)
        
        return fused_results[:limit]
    
    def _fuse_results(
        self,
        retriever_results: Dict[str, List[RetrieverResult]],
        query: str
    ) -> List[RetrieverResult]:
        """Fuse results from multiple retrievers."""
        
        if self.config.fusion_method == "weighted_sum":
            return self._weighted_sum_fusion(retriever_results)
        elif self.config.fusion_method == "rank_fusion":
            return self._rank_fusion(retriever_results)
        elif self.config.fusion_method == "max":
            return self._max_fusion(retriever_results)
        elif self.config.fusion_method == "min":
            return self._min_fusion(retriever_results)
        else:
            # Default to weighted sum
            return self._weighted_sum_fusion(retriever_results)
    
    def _weighted_sum_fusion(self, retriever_results: Dict[str, List[RetrieverResult]]) -> List[RetrieverResult]:
        """Combine results using weighted sum of scores."""
        document_scores = defaultdict(float)
        document_results = {}
        
        # Normalize scores within each retriever if configured
        if self.config.normalize_scores:
            for retriever_type, results in retriever_results.items():
                if results:
                    scores = [r.score for r in results]
                    min_score, max_score = min(scores), max(scores)
                    if max_score > min_score:
                        for result in results:
                            result.score = (result.score - min_score) / (max_score - min_score)
        
        # Weight and sum scores
        for retriever_type, results in retriever_results.items():
            weight = self.config.retriever_weights.get(retriever_type, 1.0)
            
            for result in results:
                doc_id = result.document.id
                document_scores[doc_id] += result.score * weight
                
                # Keep the result with highest individual score for this document
                if doc_id not in document_results or result.score > document_results[doc_id].score:
                    document_results[doc_id] = result
        
        # Create final results
        final_results = []
        for doc_id, combined_score in document_scores.items():
            result = document_results[doc_id]
            result.score = combined_score
            result.metadata["fusion_method"] = "weighted_sum"
            result.metadata["individual_scores"] = {
                retriever_type: [r.score for r in results if r.document.id == doc_id]
                for retriever_type, results in retriever_results.items()
            }
            final_results.append(result)
        
        # Sort by combined score
        final_results.sort(key=lambda x: x.score, reverse=True)
        return final_results
    
    def _rank_fusion(self, retriever_results: Dict[str, List[RetrieverResult]]) -> List[RetrieverResult]:
        """Combine results using rank-based fusion (RRF)."""
        document_scores = defaultdict(float)
        document_results = {}
        
        k = 60  # RRF parameter
        
        for retriever_type, results in retriever_results.items():
            weight = self.config.retriever_weights.get(retriever_type, 1.0)
            
            for rank, result in enumerate(results, 1):
                doc_id = result.document.id
                rrf_score = weight / (k + rank)
                document_scores[doc_id] += rrf_score
                
                if doc_id not in document_results:
                    document_results[doc_id] = result
        
        # Create final results
        final_results = []
        for doc_id, rrf_score in document_scores.items():
            result = document_results[doc_id]
            result.score = rrf_score
            result.metadata["fusion_method"] = "rank_fusion"
            final_results.append(result)
        
        # Sort by RRF score
        final_results.sort(key=lambda x: x.score, reverse=True)
        return final_results
    
    def _max_fusion(self, retriever_results: Dict[str, List[RetrieverResult]]) -> List[RetrieverResult]:
        """Take maximum score for each document."""
        document_scores = defaultdict(float)
        document_results = {}
        
        for retriever_type, results in retriever_results.items():
            for result in results:
                doc_id = result.document.id
                if result.score > document_scores[doc_id]:
                    document_scores[doc_id] = result.score
                    document_results[doc_id] = result
        
        final_results = list(document_results.values())
        final_results.sort(key=lambda x: x.score, reverse=True)
        return final_results
    
    def _min_fusion(self, retriever_results: Dict[str, List[RetrieverResult]]) -> List[RetrieverResult]:
        """Take minimum score for each document (conservative approach)."""
        document_scores = {}
        document_results = {}
        
        for retriever_type, results in retriever_results.items():
            for result in results:
                doc_id = result.document.id
                if doc_id not in document_scores or result.score < document_scores[doc_id]:
                    document_scores[doc_id] = result.score
                    document_results[doc_id] = result
        
        final_results = list(document_results.values())
        final_results.sort(key=lambda x: x.score, reverse=True)
        return final_results
    
    def _apply_diversity_filter(self, results: List[RetrieverResult]) -> List[RetrieverResult]:
        """Apply diversity filtering to avoid similar results."""
        if not results:
            return results
        
        diverse_results = [results[0]]  # Always include top result
        
        for result in results[1:]:
            is_diverse = True
            
            for existing in diverse_results:
                # Simple content similarity check
                similarity = self._calculate_content_similarity(
                    result.document.content,
                    existing.document.content
                )
                
                if similarity > self.config.diversity_threshold:
                    is_diverse = False
                    break
            
            if is_diverse:
                diverse_results.append(result)
        
        return diverse_results
    
    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Simple content similarity calculation."""
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0


class HybridRetriever(AsyncRetriever):
    """Combines dense and sparse vector retrieval."""
    
    def __init__(
        self,
        dense_retriever: AsyncRetriever,
        sparse_retriever: AsyncRetriever,
        config: HybridRetrieverConfig = None
    ):
        config = config or HybridRetrieverConfig()
        super().__init__(config)
        self.config: HybridRetrieverConfig = config
        self.dense_retriever = dense_retriever
        self.sparse_retriever = sparse_retriever
    
    def _get_retriever_type(self) -> str:
        return RetrieverType.HYBRID_DENSE_SPARSE
    
    async def _retrieve_impl(
        self,
        query: str,
        limit: int,
        **kwargs
    ) -> List[RetrieverResult]:
        """Implement hybrid dense-sparse retrieval."""
        
        # Run both retrievers concurrently
        dense_task = self.dense_retriever.retrieve(query, limit=limit * 2, **kwargs)
        sparse_task = self.sparse_retriever.retrieve(query, limit=limit * 2, **kwargs)
        
        try:
            dense_results, sparse_results = await asyncio.gather(dense_task, sparse_task)
        except Exception as e:
            self.logger.error(f"Hybrid retrieval failed: {e}")
            return []
        
        # Normalize scores if configured
        if self.config.normalize_before_fusion:
            dense_results = self._normalize_scores(dense_results)
            sparse_results = self._normalize_scores(sparse_results)
        
        # Combine results using linear interpolation
        combined_results = self._combine_dense_sparse(dense_results, sparse_results)
        
        return combined_results[:limit]
    
    def _normalize_scores(self, results: List[RetrieverResult]) -> List[RetrieverResult]:
        """Normalize scores to [0, 1] range."""
        if not results:
            return results
        
        scores = [r.score for r in results]
        min_score, max_score = min(scores), max(scores)
        
        if max_score > min_score:
            for result in results:
                result.score = (result.score - min_score) / (max_score - min_score)
        
        return results
    
    def _combine_dense_sparse(
        self,
        dense_results: List[RetrieverResult],
        sparse_results: List[RetrieverResult]
    ) -> List[RetrieverResult]:
        """Combine dense and sparse results."""
        
        # Create document maps
        dense_docs = {r.document.id: r for r in dense_results}
        sparse_docs = {r.document.id: r for r in sparse_results}
        
        # Get all unique documents
        all_doc_ids = set(dense_docs.keys()) | set(sparse_docs.keys())
        
        combined_results = []
        for doc_id in all_doc_ids:
            dense_score = dense_docs[doc_id].score if doc_id in dense_docs else 0.0
            sparse_score = sparse_docs[doc_id].score if doc_id in sparse_docs else 0.0
            
            # Linear interpolation
            combined_score = (
                self.config.dense_weight * dense_score +
                self.config.sparse_weight * sparse_score
            )
            
            # Use the document from whichever retriever has it (prefer dense)
            if doc_id in dense_docs:
                result = dense_docs[doc_id]
            else:
                result = sparse_docs[doc_id]
            
            result.score = combined_score
            result.metadata["dense_score"] = dense_score
            result.metadata["sparse_score"] = sparse_score
            result.metadata["fusion_method"] = "hybrid_dense_sparse"
            
            combined_results.append(result)
        
        # Sort by combined score
        combined_results.sort(key=lambda x: x.score, reverse=True)
        return combined_results


class ContextualRetriever(AsyncRetriever):
    """Context-aware retrieval that considers surrounding documents."""
    
    def __init__(
        self,
        base_retriever: AsyncRetriever,
        config: ContextualRetrieverConfig = None
    ):
        config = config or ContextualRetrieverConfig()
        super().__init__(config)
        self.config: ContextualRetrieverConfig = config
        self.base_retriever = base_retriever
        self.conversation_history = []  # Store query history
    
    def _get_retriever_type(self) -> str:
        return RetrieverType.CONTEXTUAL
    
    async def _retrieve_impl(
        self,
        query: str,
        limit: int,
        **kwargs
    ) -> List[RetrieverResult]:
        """Implement contextual retrieval."""
        
        # Build contextual query
        contextual_query = self._build_contextual_query(query)
        
        # Get base results
        base_results = await self.base_retriever.retrieve(
            contextual_query, limit=limit * 2, **kwargs
        )
        
        # Apply context scoring
        contextualized_results = await self._apply_context_scoring(base_results, query)
        
        # Update conversation history
        if self.config.use_conversation_history:
            self._update_conversation_history(query)
        
        return contextualized_results[:limit]
    
    def _build_contextual_query(self, query: str) -> str:
        """Build enhanced query using conversation history."""
        if not self.config.use_conversation_history or not self.conversation_history:
            return query
        
        # Simple approach: append recent queries
        recent_history = self.conversation_history[-self.config.max_history_length:]
        context_terms = " ".join(recent_history)
        
        # Weight original query more heavily
        return f"{query} {context_terms}"
    
    async def _apply_context_scoring(
        self,
        results: List[RetrieverResult],
        original_query: str
    ) -> List[RetrieverResult]:
        """Apply context-aware scoring to results."""
        
        if not results:
            return results
        
        # Find context windows around each result
        for result in results:
            context_boost = await self._calculate_context_boost(result, results, original_query)
            
            # Apply context boost
            original_score = result.score
            result.score = (
                (1 - self.config.context_weight) * original_score +
                self.config.context_weight * context_boost
            )
            
            result.metadata["original_score"] = original_score
            result.metadata["context_boost"] = context_boost
        
        # Re-sort by new scores
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    async def _calculate_context_boost(
        self,
        target_result: RetrieverResult,
        all_results: List[RetrieverResult],
        query: str
    ) -> float:
        """Calculate context boost for a result based on surrounding documents."""
        
        # Simple context boost based on nearby high-scoring results
        context_score = 0.0
        target_rank = next((i for i, r in enumerate(all_results) if r.document.id == target_result.document.id), 0)
        
        # Consider documents within context window
        start_idx = max(0, target_rank - self.config.context_window)
        end_idx = min(len(all_results), target_rank + self.config.context_window + 1)
        
        context_results = all_results[start_idx:end_idx]
        if len(context_results) > 1:  # Don't include just the target
            context_scores = [r.score for r in context_results if r.document.id != target_result.document.id]
            if context_scores:
                context_score = sum(context_scores) / len(context_scores)
        
        return context_score
    
    def _update_conversation_history(self, query: str):
        """Update conversation history."""
        self.conversation_history.append(query)
        
        # Keep only recent history
        if len(self.conversation_history) > self.config.max_history_length:
            self.conversation_history = self.conversation_history[-self.config.max_history_length:]


class FusionRetriever(AsyncRetriever):
    """Advanced score fusion and reranking retriever."""
    
    def __init__(
        self,
        retrievers: List[AsyncRetriever],
        config: FusionRetrieverConfig = None
    ):
        config = config or FusionRetrieverConfig()
        super().__init__(config)
        self.config: FusionRetrieverConfig = config
        self.retrievers = retrievers
    
    def _get_retriever_type(self) -> str:
        return RetrieverType.FUSION
    
    async def _retrieve_impl(
        self,
        query: str,
        limit: int,
        **kwargs
    ) -> List[RetrieverResult]:
        """Implement fusion retrieval with multiple strategies."""
        
        # Get results from all retrievers
        retriever_tasks = [
            retriever.retrieve(query, limit=self.config.rerank_top_k, **kwargs)
            for retriever in self.retrievers
        ]
        
        try:
            all_results = await asyncio.gather(*retriever_tasks)
        except Exception as e:
            self.logger.error(f"Fusion retrieval failed: {e}")
            return []
        
        retriever_results = {
            retriever.retriever_type: results
            for retriever, results in zip(self.retrievers, all_results)
        }
        
        # Apply fusion strategies
        fused_results = []
        for strategy in self.config.fusion_strategies:
            if strategy == "rrf":
                strategy_results = self._reciprocal_rank_fusion(retriever_results)
            elif strategy == "weighted_sum":
                strategy_results = self._weighted_sum_fusion(retriever_results)
            else:
                continue
            
            fused_results.extend(strategy_results)
        
        # Remove duplicates and merge
        final_results = self._merge_fusion_results(fused_results)
        
        # Apply neural reranking if enabled
        if self.config.enable_neural_rerank:
            final_results = await self._neural_rerank(final_results, query)
        
        return final_results[:limit]
    
    def _reciprocal_rank_fusion(self, retriever_results: Dict[str, List[RetrieverResult]]) -> List[RetrieverResult]:
        """Apply Reciprocal Rank Fusion."""
        document_scores = defaultdict(float)
        document_results = {}
        
        for retriever_type, results in retriever_results.items():
            for rank, result in enumerate(results, 1):
                doc_id = result.document.id
                rrf_score = 1.0 / (self.config.rrf_k + rank)
                document_scores[doc_id] += rrf_score
                
                if doc_id not in document_results:
                    document_results[doc_id] = result
        
        # Create results with RRF scores
        rrf_results = []
        for doc_id, score in document_scores.items():
            result = document_results[doc_id]
            result.score = score
            result.metadata["fusion_strategy"] = "rrf"
            rrf_results.append(result)
        
        rrf_results.sort(key=lambda x: x.score, reverse=True)
        return rrf_results
    
    def _weighted_sum_fusion(self, retriever_results: Dict[str, List[RetrieverResult]]) -> List[RetrieverResult]:
        """Apply weighted sum fusion."""
        document_scores = defaultdict(float)
        document_results = {}
        
        # Equal weights for simplicity
        weight = 1.0 / len(retriever_results)
        
        for retriever_type, results in retriever_results.items():
            for result in results:
                doc_id = result.document.id
                document_scores[doc_id] += result.score * weight
                
                if doc_id not in document_results or result.score > document_results[doc_id].score:
                    document_results[doc_id] = result
        
        # Create results with weighted scores
        weighted_results = []
        for doc_id, score in document_scores.items():
            result = document_results[doc_id]
            result.score = score
            result.metadata["fusion_strategy"] = "weighted_sum"
            weighted_results.append(result)
        
        weighted_results.sort(key=lambda x: x.score, reverse=True)
        return weighted_results
    
    def _merge_fusion_results(self, fused_results: List[RetrieverResult]) -> List[RetrieverResult]:
        """Merge results from different fusion strategies."""
        document_results = {}
        
        for result in fused_results:
            doc_id = result.document.id
            if doc_id not in document_results or result.score > document_results[doc_id].score:
                document_results[doc_id] = result
        
        final_results = list(document_results.values())
        final_results.sort(key=lambda x: x.score, reverse=True)
        return final_results
    
    async def _neural_rerank(
        self,
        results: List[RetrieverResult],
        query: str
    ) -> List[RetrieverResult]:
        """Apply neural reranking (placeholder for future neural reranker)."""
        # This is a placeholder - in practice, you'd use a cross-encoder model
        # like sentence-transformers cross-encoders
        
        self.logger.info("Neural reranking not implemented yet, returning original results")
        return results