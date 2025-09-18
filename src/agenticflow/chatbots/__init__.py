"""
AgenticFlow Chatbots
====================

Advanced chatbot framework built on AgenticFlow Agents with:
- Retrieval-Augmented Generation (RAG) capabilities
- Smart knowledge management with metadata tracking
- Adaptive retrieval with retry logic and sufficiency checking
- Automatic source citation and referencing
- Interactive conversation management
- Configurable knowledge vs LLM usage modes

Key Components:
- RAGAgent: Agent class with RAG capabilities
- InteractiveChatbot: User-friendly interactive wrapper
- ChatbotConfig: Comprehensive configuration system
- KnowledgeManager: Advanced document and metadata management
- SmartRetriever: Intelligent retrieval with adaptive strategies

Example Usage:

    from agenticflow.chatbots import ChatbotConfig, RAGAgent, InteractiveChatbot
    from agenticflow.config.settings import LLMProviderConfig, LLMProvider
    
    # Simple RAG chatbot
    config = ChatbotConfig.create_simple_rag(
        name="Science Assistant",
        knowledge_path="./knowledge",
        llm_config=LLMProviderConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini"
        )
    )
    
    # Create and run interactive chatbot
    chatbot = InteractiveChatbot(config)
    await chatbot.interactive_loop()
    
    # Or use RAGAgent directly
    agent = RAGAgent(config)
    await agent.start()
    result = await agent.execute_task("What is photosynthesis?")
    print(result['response'])
"""

# Configuration
from .config import (
    # Enums
    KnowledgeMode,
    CitationStyle, 
    RetrievalStrategy,
    ConversationMode,
    
    # Configuration classes
    KnowledgeSourceConfig,
    RetrievalConfig,
    CitationConfig,
    ConversationConfig,
    ChatbotConfig
)

# Knowledge management
from .knowledge import (
    DocumentMetadata,
    ChunkMetadata,
    RetrievalResult,
    KnowledgeManager
)

# Retrieval system
from .retrieval import (
    RetrievalAttempt,
    SufficiencyChecker,
    SmartRetriever
)

# Core chatbot classes
from .rag_agent import (
    CitationFormatter,
    RAGAgent
)

from .interactive import (
    InteractiveChatbot
)

# Convenience imports for common use cases
__all__ = [
    # Configuration
    "KnowledgeMode",
    "CitationStyle", 
    "RetrievalStrategy",
    "ConversationMode",
    "KnowledgeSourceConfig",
    "RetrievalConfig", 
    "CitationConfig",
    "ConversationConfig",
    "ChatbotConfig",
    
    # Knowledge management
    "DocumentMetadata",
    "ChunkMetadata", 
    "RetrievalResult",
    "KnowledgeManager",
    
    # Retrieval
    "RetrievalAttempt",
    "SufficiencyChecker",
    "SmartRetriever",
    
    # Core classes
    "CitationFormatter",
    "RAGAgent",
    "InteractiveChatbot",
]

# Version info
__version__ = "0.1.0"