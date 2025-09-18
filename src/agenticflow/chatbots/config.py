"""
Chatbot Configuration
=====================

Configuration classes and enums for AgenticFlow chatbots that extend the base Agent
with conversational and RAG capabilities.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from pydantic import BaseModel, Field
from ..config.settings import AgentConfig


class KnowledgeMode(str, Enum):
    """How the chatbot should use knowledge sources."""
    KNOWLEDGE_ONLY = "knowledge_only"  # Only use knowledge base, no LLM internal knowledge
    LLM_ONLY = "llm_only"  # Only use LLM's internal knowledge, no retrieval
    HYBRID = "hybrid"  # Use both knowledge base and LLM knowledge (default)
    KNOWLEDGE_FIRST = "knowledge_first"  # Try knowledge base first, fallback to LLM


class CitationStyle(str, Enum):
    """How sources should be cited in responses."""
    NONE = "none"  # No citations
    INLINE = "inline"  # [Source: document.txt, chunk 3]
    FOOTNOTES = "footnotes"  # Response with numbered references at the end
    DETAILED = "detailed"  # Full source information with page/section numbers
    ACADEMIC = "academic"  # Academic-style citations


class RetrievalStrategy(str, Enum):
    """Strategy for retrieving relevant information."""
    SIMPLE = "simple"  # Single retrieval attempt
    ADAPTIVE = "adaptive"  # Retry with different queries if insufficient
    PROGRESSIVE = "progressive"  # Start specific, get broader if needed
    MULTI_HOP = "multi_hop"  # Follow references and related content


class ConversationMode(str, Enum):
    """Type of conversation interaction."""
    QA = "qa"  # Question and Answer
    CHAT = "chat"  # Free-form conversation
    INTERVIEW = "interview"  # Structured Q&A with follow-ups
    TUTORIAL = "tutorial"  # Educational step-by-step guidance


class KnowledgeSourceConfig(BaseModel):
    """Configuration for a knowledge source."""
    
    name: str = Field(..., description="Human-readable name for the source")
    path: Union[str, Path] = Field(..., description="Path to knowledge files")
    file_patterns: List[str] = Field(["*.txt", "*.md"], description="File patterns to include")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Processing options
    chunk_size: int = Field(400, ge=100, description="Text chunk size for embedding")
    chunk_overlap: int = Field(100, ge=0, description="Overlap between chunks")
    enable_preprocessing: bool = Field(True, description="Enable text preprocessing")
    
    # Retrieval options
    weight: float = Field(1.0, ge=0.0, description="Relative importance of this source")
    max_chunks: int = Field(5, ge=1, description="Maximum chunks to retrieve from this source")


class RetrievalConfig(BaseModel):
    """Configuration for the retrieval system."""
    
    strategy: RetrievalStrategy = Field(RetrievalStrategy.ADAPTIVE, description="Retrieval strategy")
    max_attempts: int = Field(3, ge=1, le=10, description="Maximum retrieval attempts")
    min_similarity: float = Field(0.3, ge=0.0, le=1.0, description="Minimum similarity threshold")
    max_chunks_total: int = Field(10, ge=1, description="Maximum total chunks across all sources")
    
    # Sufficiency checking
    enable_sufficiency_check: bool = Field(True, description="Check if retrieved content is sufficient")
    sufficiency_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Sufficiency confidence threshold")
    
    # Metadata filtering
    enable_metadata_filtering: bool = Field(True, description="Enable metadata-based pre-filtering")
    metadata_filters: Dict[str, Any] = Field(default_factory=dict, description="Metadata filters to apply")


class CitationConfig(BaseModel):
    """Configuration for source citations."""
    
    style: CitationStyle = Field(CitationStyle.INLINE, description="Citation style")
    include_chunk_position: bool = Field(True, description="Include chunk position in citations")
    include_similarity_score: bool = Field(False, description="Include similarity scores")
    max_citations_per_response: int = Field(5, ge=1, description="Maximum citations per response")
    
    # Detailed citation options
    include_file_path: bool = Field(False, description="Include full file path")
    include_timestamp: bool = Field(False, description="Include document timestamp")
    custom_format: Optional[str] = Field(None, description="Custom citation format string")


class ConversationConfig(BaseModel):
    """Configuration for conversation management."""
    
    mode: ConversationMode = Field(ConversationMode.CHAT, description="Conversation mode")
    max_history_length: int = Field(50, ge=1, description="Maximum conversation history to maintain")
    context_window: int = Field(10, ge=1, description="Recent messages to use for context")
    
    # Session management
    enable_session_persistence: bool = Field(True, description="Persist conversations across restarts")
    session_timeout_hours: int = Field(24, ge=1, description="Session timeout in hours")
    
    # Response options
    enable_follow_up_suggestions: bool = Field(True, description="Suggest follow-up questions")
    enable_topic_tracking: bool = Field(True, description="Track conversation topics")


class ChatbotConfig(AgentConfig):
    """
    Extended AgentConfig for chatbots with RAG capabilities.
    
    Inherits all Agent capabilities (tools, memory, LLM, etc.) and adds
    chatbot-specific features like knowledge bases, retrieval, and citations.
    """
    
    # Knowledge and retrieval
    knowledge_mode: KnowledgeMode = Field(KnowledgeMode.HYBRID, description="How to use knowledge sources")
    knowledge_sources: List[KnowledgeSourceConfig] = Field(default_factory=list, description="Knowledge sources")
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig, description="Retrieval configuration")
    
    # Citations and referencing
    citations: CitationConfig = Field(default_factory=CitationConfig, description="Citation configuration")
    
    # Conversation features
    conversation: ConversationConfig = Field(default_factory=ConversationConfig, description="Conversation configuration")
    
    # Chatbot personality and behavior
    chatbot_personality: Optional[str] = Field(None, description="Personality description for the chatbot")
    welcome_message: Optional[str] = Field(None, description="Custom welcome message")
    error_responses: Dict[str, str] = Field(default_factory=dict, description="Custom error response templates")
    
    # Advanced features
    enable_context_awareness: bool = Field(True, description="Use conversation context in retrieval")
    enable_topic_coherence: bool = Field(True, description="Maintain topic coherence in responses")
    enable_user_preferences: bool = Field(False, description="Learn and adapt to user preferences")
    
    # Simplified approach: tools are just tools, handled by base Agent
    # No need for separate "retrieval_tools" - tools can handle retrieval naturally
    
    @classmethod
    def create_simple_rag(
        cls,
        name: str,
        knowledge_path: Union[str, Path],
        llm_config: Any,
        **kwargs
    ) -> "ChatbotConfig":
        """Create a simple RAG chatbot configuration."""
        knowledge_source = KnowledgeSourceConfig(
            name="Knowledge Base",
            path=knowledge_path
        )
        
        return cls(
            name=name,
            llm=llm_config,
            knowledge_sources=[knowledge_source],
            instructions=f"You are {name}, a helpful AI assistant with access to a knowledge base. "
                        "Use the retrieved information to provide accurate, helpful responses. "
                        "Always cite your sources when using information from the knowledge base.",
            **kwargs
        )
    
    @classmethod
    def create_expert_chatbot(
        cls,
        name: str,
        domain: str,
        knowledge_sources: List[KnowledgeSourceConfig],
        llm_config: Any,
        **kwargs
    ) -> "ChatbotConfig":
        """Create an expert domain chatbot configuration."""
        return cls(
            name=name,
            llm=llm_config,
            knowledge_sources=knowledge_sources,
            knowledge_mode=KnowledgeMode.KNOWLEDGE_FIRST,
            citations=CitationConfig(style=CitationStyle.DETAILED),
            conversation=ConversationConfig(mode=ConversationMode.INTERVIEW),
            instructions=f"You are {name}, an expert AI assistant specializing in {domain}. "
                        f"You have access to comprehensive knowledge sources about {domain}. "
                        "Provide detailed, accurate information with proper citations. "
                        "Ask clarifying questions when needed and suggest related topics.",
            chatbot_personality=f"Expert, knowledgeable, thorough, and helpful specialist in {domain}",
            **kwargs
        )
    
    @classmethod
    def create_tool_based_rag(
        cls,
        name: str,
        tools: List[str],
        llm_config: Any,
        **kwargs
    ) -> "ChatbotConfig":
        """Create a RAG chatbot that uses tools for information retrieval."""
        return cls(
            name=name,
            llm=llm_config,
            knowledge_sources=[],  # No static knowledge base
            tools=tools,  # Standard Agent tools - much simpler!
            knowledge_mode=KnowledgeMode.HYBRID,
            instructions=f"You are {name}, a helpful AI assistant with access to tools for retrieving information. "
                        f"Available tools: {', '.join(tools)}. "
                        "When you need information, use the appropriate tool to retrieve it. "
                        "Always cite your sources when using tool-retrieved information.",
            **kwargs
        )
    
    @classmethod
    def create_hybrid_rag(
        cls,
        name: str,
        knowledge_path: Union[str, Path],
        tools: List[str],
        llm_config: Any,
        **kwargs
    ) -> "ChatbotConfig":
        """Create a hybrid RAG chatbot with both knowledge base and tools."""
        knowledge_source = KnowledgeSourceConfig(
            name="Knowledge Base",
            path=knowledge_path
        )
        
        return cls(
            name=name,
            llm=llm_config,
            knowledge_sources=[knowledge_source],
            tools=tools,  # Standard Agent tools
            knowledge_mode=KnowledgeMode.HYBRID,
            instructions=f"You are {name}, a helpful AI assistant with both a knowledge base and tools. "
                        f"You have a curated knowledge base and can also use these tools: {', '.join(tools)}. "
                        "Use the knowledge base for core information and tools for real-time or current data. "
                        "Always cite your sources.",
            **kwargs
        )
