"""
RAG Agent
=========

Agent class with Retrieval-Augmented Generation capabilities, extending the base Agent
with advanced knowledge management, smart retrieval, and automatic citation features.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple

from ..core.agent import Agent
from .config import ChatbotConfig, KnowledgeMode, CitationStyle, RetrievalStrategy
from .knowledge import KnowledgeManager, RetrievalResult
from .retrieval import SmartRetriever
from ..retrievers.base import AsyncRetriever


logger = logging.getLogger(__name__)


class CitationFormatter:
    """Formats citations for retrieved content."""
    
    def __init__(self, citation_style: CitationStyle):
        self.style = citation_style
    
    def format_response_with_citations(
        self,
        response: str,
        retrieval_results: List[RetrievalResult]
    ) -> str:
        """Add citations to the response based on the configured style."""
        
        if self.style == CitationStyle.NONE or not retrieval_results:
            return response
        
        if self.style == CitationStyle.INLINE:
            return self._add_inline_citations(response, retrieval_results)
        elif self.style == CitationStyle.FOOTNOTES:
            return self._add_footnote_citations(response, retrieval_results)
        elif self.style == CitationStyle.DETAILED:
            return self._add_detailed_citations(response, retrieval_results)
        elif self.style == CitationStyle.ACADEMIC:
            return self._add_academic_citations(response, retrieval_results)
        
        return response
    
    def _add_inline_citations(self, response: str, results: List[RetrievalResult]) -> str:
        """Add inline citations within the response."""
        # Append citations at the end for simplicity
        if not results:
            return response
        
        citations = []
        for i, result in enumerate(results, 1):
            citation = result.get_citation("inline")
            if citation not in citations:
                citations.append(citation)
        
        if citations:
            response += "\n\n" + " ".join(citations)
        
        return response
    
    def _add_footnote_citations(self, response: str, results: List[RetrievalResult]) -> str:
        """Add footnote-style citations."""
        if not results:
            return response
        
        footnotes = []
        unique_citations = []
        
        for i, result in enumerate(results, 1):
            citation = result.get_citation("footnotes")
            if citation not in unique_citations:
                unique_citations.append(citation)
                footnotes.append(f"[{len(unique_citations)}] {citation}")
        
        if footnotes:
            response += "\n\n**Sources:**\n" + "\n".join(footnotes)
        
        return response
    
    def _add_detailed_citations(self, response: str, results: List[RetrievalResult]) -> str:
        """Add detailed citations with full metadata."""
        if not results:
            return response
        
        citations = []
        for i, result in enumerate(results, 1):
            citation = result.get_citation("detailed")
            citations.append(f"{i}. {citation}")
        
        if citations:
            response += "\n\n**Detailed Sources:**\n" + "\n".join(citations)
        
        return response
    
    def _add_academic_citations(self, response: str, results: List[RetrievalResult]) -> str:
        """Add academic-style citations."""
        if not results:
            return response
        
        references = []
        unique_sources = set()
        
        for result in results:
            source_key = f"{result.chunk_metadata.source_name}_{result.chunk_metadata.section or 'main'}"
            if source_key not in unique_sources:
                unique_sources.add(source_key)
                citation = result.get_citation("academic")
                references.append(citation)
        
        if references:
            response += "\n\n**References:**\n" + "\n".join(f"- {ref}" for ref in references)
        
        return response


class RAGAgent(Agent):
    """
    Agent with Retrieval-Augmented Generation capabilities.
    
    Extends the base Agent with:
    - Advanced knowledge management and retrieval
    - Smart retry logic and sufficiency checking
    - Automatic source citation
    - Configurable knowledge vs LLM usage modes
    - Enhanced conversation context awareness
    """
    
    def __init__(self, config: ChatbotConfig):
        # Initialize base agent
        super().__init__(config)
        
        # Store chatbot-specific config
        self.chatbot_config = config
        
        # Initialize knowledge management - use temp directory to avoid root clutter
        import tempfile
        cache_dir = Path(tempfile.gettempdir()) / f"agenticflow_cache_{self.id}"
        self.knowledge_manager = KnowledgeManager(cache_dir)
        
        # Initialize retrieval components (will be set up in _setup_knowledge_system)
        self.smart_retriever: Optional[SmartRetriever] = None
        self.citation_formatter = CitationFormatter(config.citations.style)
        
        # Track last retrieval for debugging/stats
        self.last_retrieval_results: List[RetrievalResult] = []
        self.last_retrieval_metadata: Dict[str, Any] = {}
        
        # The base Agent class handles all tools automatically
        # No need for complex tool retrieval system
    
    async def start(self) -> None:
        """Start the RAG agent with knowledge system setup."""
        # Start base agent first
        await super().start()
        
        # Setup knowledge system
        await self._setup_knowledge_system()
        
        chunk_count = len(self.knowledge_manager.chunks)
        tool_count = len(self.config.tools) if self.config.tools else 0
        tool_info = f" and {tool_count} tools" if tool_count > 0 else ""
        
        logger.info(f"RAG Agent {self.id} started with {chunk_count} knowledge chunks{tool_info}")
    
    async def _setup_knowledge_system(self) -> None:
        """Setup the knowledge management and retrieval system."""
        logger.info("Setting up knowledge system...")
        
        # Load knowledge sources
        for source_config in self.chatbot_config.knowledge_sources:
            logger.info(f"Loading knowledge source: {source_config.name}")
            
            chunks = self.knowledge_manager.load_knowledge_source(
                source_path=source_config.path,
                source_name=source_config.name,
                file_patterns=source_config.file_patterns,
                chunk_size=source_config.chunk_size,
                chunk_overlap=source_config.chunk_overlap,
                metadata=source_config.metadata
            )
            
            logger.info(f"  Loaded {len(chunks)} chunks from {source_config.name}")
        
        # Setup retriever - for now we'll use None as placeholder
        # In practice, you'd initialize with actual vector/hybrid retriever
        base_retriever = None  # Replace with actual AsyncRetriever implementation
        
        self.smart_retriever = SmartRetriever(
            knowledge_manager=self.knowledge_manager,
            base_retriever=base_retriever,
            config=self.chatbot_config.retrieval
        )
        
        summary = self.knowledge_manager.get_knowledge_summary()
        logger.info(f"Knowledge system ready: {summary}")
    
    
    async def execute_task(self, task: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute a task with RAG capabilities.
        
        Enhances the base execute_task with:
        - Knowledge retrieval and context injection
        - Source citation in responses
        - Knowledge mode enforcement
        """
        if isinstance(task, str):
            query = task
            task_dict = {"query": query}
        else:
            query = task.get("query", str(task))
            task_dict = task
        
        logger.info(f"Executing RAG task: '{query[:50]}...'")
        
        # Get conversation context for retrieval
        conversation_context = await self._get_conversation_context()
        
        # Perform retrieval (either knowledge base or tool-based)
        retrieval_results = []
        retrieval_metadata = {}
        
        if self._should_use_knowledge(query):
            logger.debug("Performing knowledge retrieval...")
            retrieval_results, retrieval_metadata = await self._perform_retrieval(
                query, conversation_context
            )
            
            self.last_retrieval_results = retrieval_results
            self.last_retrieval_metadata = retrieval_metadata
            
            logger.info(f"Retrieved {len(retrieval_results)} knowledge chunks")
        
        # Prepare enhanced task with knowledge context
        enhanced_task = await self._prepare_enhanced_task(
            query, task_dict, retrieval_results, conversation_context
        )
        
        # Execute with base agent
        try:
            result = await super().execute_task(enhanced_task)
            
            # Post-process response with citations
            if isinstance(result, dict) and "response" in result:
                original_response = result["response"]
                cited_response = self.citation_formatter.format_response_with_citations(
                    original_response, retrieval_results
                )
                result["response"] = cited_response
                
                # Add RAG metadata
                result["rag_metadata"] = {
                    "knowledge_chunks_used": len(retrieval_results),
                    "retrieval_metadata": retrieval_metadata,
                    "knowledge_mode": self.chatbot_config.knowledge_mode.value,
                    "citation_style": self.chatbot_config.citations.style.value
                }
            
            return result
            
        except Exception as e:
            logger.error(f"RAG task execution failed: {e}")
            
            # Return error with context
            return {
                "error": str(e),
                "rag_metadata": {
                    "knowledge_chunks_retrieved": len(retrieval_results),
                    "retrieval_metadata": retrieval_metadata
                }
            }
    
    def _should_use_knowledge(self, query: str) -> bool:
        """Determine if knowledge retrieval should be used for this query."""
        mode = self.chatbot_config.knowledge_mode
        
        if mode == KnowledgeMode.LLM_ONLY:
            return False
        elif mode in [KnowledgeMode.KNOWLEDGE_ONLY, KnowledgeMode.KNOWLEDGE_FIRST, KnowledgeMode.HYBRID]:
            return True
        
        return True  # Default to using knowledge
    
    async def _perform_retrieval(
        self, 
        query: str, 
        conversation_context: Optional[str]
    ) -> Tuple[List[RetrievalResult], Dict[str, Any]]:
        """Perform knowledge retrieval using the smart retriever."""
        if not self.smart_retriever:
            logger.warning("Smart retriever not initialized")
            return [], {"error": "Retriever not available"}
        
        try:
            return await self.smart_retriever.retrieve(
                query=query,
                conversation_context=conversation_context,
                knowledge_mode=self.chatbot_config.knowledge_mode
            )
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return [], {"error": str(e)}
    
    async def _get_conversation_context(self) -> Optional[str]:
        """Get recent conversation context for retrieval enhancement."""
        try:
            if hasattr(self, 'memory') and self.memory:
                # Get recent messages from memory
                recent_messages = await self.memory.get_messages(
                    limit=self.chatbot_config.conversation.context_window
                )
                
                if recent_messages:
                    # Format messages into context string
                    context_parts = []
                    for msg in recent_messages[-5:]:  # Last 5 messages
                        if hasattr(msg, 'content'):
                            content = msg.content[:200]  # Limit length
                            context_parts.append(content)
                    
                    return " ".join(context_parts)
            
        except Exception as e:
            logger.debug(f"Could not get conversation context: {e}")
        
        return None
    
    async def _prepare_enhanced_task(
        self,
        original_query: str,
        task_dict: Dict[str, Any],
        retrieval_results: List[RetrievalResult],
        conversation_context: Optional[str]
    ) -> Union[str, Dict[str, Any]]:
        """Prepare the enhanced task with knowledge context."""
        
        # Build knowledge context
        knowledge_context = ""
        if retrieval_results:
            context_parts = []
            for i, result in enumerate(retrieval_results, 1):
                # Include source information in context
                source_info = f"Source {i}: {result.chunk_metadata.source_name}"
                if result.chunk_metadata.section:
                    source_info += f" (Section: {result.chunk_metadata.section})"
                
                context_parts.append(f"{source_info}\n{result.content}")
            
            knowledge_context = "\n\n".join(context_parts)
        
        # Determine how to incorporate knowledge based on mode
        mode = self.chatbot_config.knowledge_mode
        
        if mode == KnowledgeMode.KNOWLEDGE_ONLY:
            # Only use knowledge, restrict LLM to knowledge-based responses
            enhanced_query = self._format_knowledge_only_prompt(
                original_query, knowledge_context
            )
        elif mode == KnowledgeMode.KNOWLEDGE_FIRST:
            # Try knowledge first, allow LLM fallback
            enhanced_query = self._format_knowledge_first_prompt(
                original_query, knowledge_context
            )
        elif mode == KnowledgeMode.HYBRID:
            # Combine knowledge and LLM knowledge
            enhanced_query = self._format_hybrid_prompt(
                original_query, knowledge_context, conversation_context
            )
        else:  # LLM_ONLY
            enhanced_query = original_query
        
        # Return enhanced task
        if isinstance(task_dict, dict) and len(task_dict) > 1:
            enhanced_task = task_dict.copy()
            enhanced_task["query"] = enhanced_query
            return enhanced_task
        else:
            return enhanced_query
    
    def _format_knowledge_only_prompt(self, query: str, knowledge_context: str) -> str:
        """Format prompt to use only knowledge base."""
        if not knowledge_context:
            return (f"I don't have specific information in my knowledge base to answer: {query}\n\n"
                   f"Please ask about topics covered in my knowledge sources.")
        
        return f"""Based ONLY on the following knowledge sources, please answer this question: {query}

Available Knowledge:
{knowledge_context}

Instructions:
- Use ONLY information from the knowledge sources above
- If the knowledge sources don't contain enough information to answer the question, say so
- Do not use any external knowledge or make assumptions
- Cite which sources you're using in your response
"""
    
    def _format_knowledge_first_prompt(self, query: str, knowledge_context: str) -> str:
        """Format prompt to prioritize knowledge base with LLM fallback."""
        base_prompt = f"Question: {query}\n\n"
        
        if knowledge_context:
            base_prompt += f"""I have found relevant information in my knowledge sources:

{knowledge_context}

Please answer the question using this information as the primary source. If the provided information is insufficient, you may supplement with your general knowledge, but clearly distinguish between information from the knowledge sources and general knowledge."""
        else:
            base_prompt += "I didn't find specific information in my knowledge sources for this question. Please answer using your general knowledge and mention that this is not from my specific knowledge base."
        
        return base_prompt
    
    def _format_hybrid_prompt(
        self, 
        query: str, 
        knowledge_context: str, 
        conversation_context: Optional[str]
    ) -> str:
        """Format prompt to combine knowledge base and LLM knowledge."""
        prompt_parts = [f"Question: {query}"]
        
        if conversation_context:
            prompt_parts.append(f"Recent conversation context:\n{conversation_context}")
        
        if knowledge_context:
            prompt_parts.append(f"Relevant information from my knowledge sources:\n{knowledge_context}")
            prompt_parts.append(
                "Please provide a comprehensive answer using both the specific information "
                "from my knowledge sources and your general knowledge. Clearly indicate "
                "when you're referencing the provided sources."
            )
        else:
            prompt_parts.append(
                "I didn't find specific information in my knowledge sources for this question. "
                "Please answer using your general knowledge."
            )
        
        return "\n\n".join(prompt_parts)
    
    # Note: Tool-based retrieval is handled automatically by the base Agent class
    # When the LLM decides it needs information, it can call any available tool
    # Tools handle their own retry logic, error handling, and data formatting
    # The RAGAgent just adds knowledge base retrieval on top of this
    
    async def get_knowledge_summary(self) -> Dict[str, Any]:
        """Get a summary of the loaded knowledge."""
        if self.knowledge_manager:
            return self.knowledge_manager.get_knowledge_summary()
        return {"message": "Knowledge manager not initialized"}
    
    async def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get statistics about recent retrieval performance."""
        stats = {
            "last_retrieval": {
                "results_count": len(self.last_retrieval_results),
                "metadata": self.last_retrieval_metadata
            }
        }
        
        if self.smart_retriever:
            stats["smart_retriever"] = self.smart_retriever.get_retrieval_stats()
        
        return stats
    
    async def search_knowledge(
        self, 
        query: str, 
        max_results: int = 5
    ) -> List[RetrievalResult]:
        """Direct search of the knowledge base."""
        if not self.smart_retriever:
            logger.warning("Smart retriever not initialized")
            return []
        
        try:
            results, _ = await self.smart_retriever.retrieve(
                query=query,
                conversation_context=None,
                knowledge_mode=KnowledgeMode.KNOWLEDGE_ONLY
            )
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Knowledge search failed: {e}")
            return []
    
    async def add_knowledge_source(
        self,
        source_path: Union[str, Path],
        source_name: str,
        **kwargs
    ) -> int:
        """
        Dynamically add a new knowledge source.
        
        Returns the number of chunks added.
        """
        if not self.knowledge_manager:
            raise RuntimeError("Knowledge manager not initialized")
        
        chunks = self.knowledge_manager.load_knowledge_source(
            source_path=source_path,
            source_name=source_name,
            **kwargs
        )
        
        logger.info(f"Added {len(chunks)} chunks from new source: {source_name}")
        return len(chunks)
    
    def __repr__(self) -> str:
        knowledge_info = ""
        if self.knowledge_manager:
            summary = self.knowledge_manager.get_knowledge_summary()
            knowledge_info = f" (Knowledge: {summary.get('total_chunks', 0)} chunks)"
        
        return f"RAGAgent(id={self.agent_id}, name={self.name}{knowledge_info})"