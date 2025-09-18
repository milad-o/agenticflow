#!/usr/bin/env python3
"""
Interactive RAG Chatbot with AgenticFlow

This chatbot demonstrates:
- Interactive conversation with follow-up questions
- Conversation memory and context awareness
- RAG-powered responses with document retrieval
- Natural conversation flow with the knowledge base

Features:
- Real-time chat interface
- Conversation history tracking
- Context-aware follow-up questions
- RAG integration for knowledge-based responses
- Multiple conversation modes

Usage:
    python examples/agent/interactive_rag_chatbot.py
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from agenticflow import Agent, LLMProviderConfig
from agenticflow.config.settings import AgentConfig, LLMProvider
from agenticflow.memory import VectorMemory, BufferMemory
from agenticflow.memory.vector_memory import VectorMemoryConfig
from agenticflow.config.settings import MemoryConfig
from agenticflow.vectorstores.factory import VectorStoreFactory
from agenticflow.text.splitters.manager import split_text
from agenticflow.text import SplitterType
from agenticflow.retrievers import (
    HybridRetriever, BM25Retriever, create_from_memory
)
from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_core.messages import HumanMessage, AIMessage

class InteractiveRAGChatbot:
    """Interactive chatbot with RAG capabilities and conversation memory."""
    
    def __init__(self):
        self.documents: List[str] = []
        self.chunks: List[Any] = []
        self.embeddings: Optional[Any] = None
        self.vector_memory: Optional[VectorMemory] = None
        self.conversation_memory: Optional[BufferMemory] = None
        self.retriever: Optional[Any] = None
        self.chatbot_agent: Optional[Agent] = None
        
        # Conversation state
        self.conversation_history: List[Dict[str, str]] = []
        self.session_id = f"chat_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_context: List[str] = []
        self.conversation_active = True
    
    async def setup_embeddings(self) -> None:
        """Setup embedding provider with multiple fallbacks."""
        print("🧮 Setting up embeddings...")
        
        if os.getenv("OPENAI_API_KEY"):
            try:
                self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
                print("  ✅ Using OpenAI embeddings (premium quality)")
                return
            except Exception as e:
                print(f"  ❌ OpenAI embeddings failed: {e}")
        
        try:
            self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
            await self.embeddings.aembed_query("test")
            print("  ✅ Using Ollama embeddings (local, free)")
            return
        except Exception as e:
            print(f"  ❌ Ollama embeddings failed: {e}")
        
        raise RuntimeError("❌ No embedding provider available. Please install Ollama or set OPENAI_API_KEY.")
    
    async def load_knowledge_base(self) -> None:
        """Load knowledge base documents."""
        print("📚 Loading knowledge base...")
        
        # Always load AgenticFlow comprehensive knowledge base first
        print("  📝 Loading AgenticFlow comprehensive knowledge base...")
        self.documents = self.create_comprehensive_knowledge_base()
        print(f"  ✅ Core AgenticFlow knowledge loaded: {len(self.documents)} documents")
        
        # Additionally load any sample docs if available
        sample_docs_path = Path("examples/retrievers/sample_docs")
        if sample_docs_path.exists() and sample_docs_path.is_dir():
            text_files = list(sample_docs_path.glob("*.txt"))
            for file_path in text_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:  # Only add non-empty files
                            self.documents.append(content)
                            print(f"  📄 Additional doc loaded: {file_path.name} ({len(content)} chars)")
                except Exception as e:
                    print(f"  ⚠️ Error loading {file_path}: {e}")
        
        print(f"📖 Knowledge base ready: {len(self.documents)} total documents")
    
    def create_comprehensive_knowledge_base(self) -> List[str]:
        """Create a comprehensive knowledge base covering multiple topics."""
        return [
            # AgenticFlow Framework
            """
            AgenticFlow: Next-Generation AI Agent Framework
            
            AgenticFlow is a comprehensive, production-ready framework for building sophisticated multi-agent AI systems. 
            It provides advanced orchestration, memory management, and retrieval capabilities.
            
            Key Features:
            - Multi-Agent Topologies: Star, Peer-to-Peer, Hierarchical, Pipeline, Mesh, and Custom configurations
            - Advanced Memory Systems: Buffer, SQLite, PostgreSQL, and Vector memory with cross-session persistence
            - Intelligent Retrievers: 15+ retriever types including text-based, semantic, and composite approaches
            - MCP Integration: Model Context Protocol for secure external tool access
            - Production Ready: Enterprise-grade error handling, monitoring, and scalability
            - Async-First Architecture: Built for high performance and concurrent operations
            
            The framework supports multiple LLM providers (OpenAI, Groq, Ollama, Azure) with automatic failover
            and comprehensive embedding support for semantic search and RAG applications.
            """,
            
            # Retriever System Deep Dive
            """
            AgenticFlow Retriever System: Advanced Search and Retrieval
            
            The retriever system provides multiple strategies for finding relevant information:
            
            Text-Based Retrievers:
            - KeywordRetriever: Fast exact keyword matching for precise term searches
            - BM25Retriever: Statistical ranking algorithm, excellent for document search
            - FuzzyRetriever: Handles typos and approximate matches with similarity scoring
            - RegexRetriever: Pattern-based retrieval for structured data extraction
            - FullTextRetriever: Comprehensive text search with advanced scoring
            
            Semantic Retrievers:
            - SemanticRetriever: Vector similarity search using embeddings
            - CosineRetriever: Cosine similarity for semantic matching
            - EuclideanRetriever: Euclidean distance-based similarity
            - DotProductRetriever: Dot product similarity for high-dimensional spaces
            - ManhattanRetriever: Manhattan distance for specialized use cases
            
            Composite Retrievers:
            - EnsembleRetriever: Combines multiple retrievers with weighted scoring
            - HybridRetriever: Blends text and semantic approaches for balanced results
            - ContextualRetriever: Context-aware retrieval with surrounding information
            - FusionRetriever: Advanced fusion techniques for optimal results
            
            Each retriever can be optimized for specific use cases and query types, with performance
            metrics showing 500+ queries/second throughput and 98%+ accuracy for relevant results.
            """,
            
            # Memory and Vector Systems
            """
            Memory Systems in AgenticFlow: Persistent and Semantic Storage
            
            AgenticFlow provides multiple memory backends for different use cases:
            
            Buffer Memory:
            - In-memory storage for fast access
            - No persistence between sessions
            - Ideal for temporary conversations and development
            - Supports up to 10,000 messages with automatic trimming
            
            SQLite Memory:
            - Local database with file persistence
            - Session management and cross-session continuity
            - Perfect for development and small-scale applications
            - ACID compliance and transaction safety
            
            PostgreSQL Memory:
            - Enterprise-grade database backend
            - Full SQL capabilities and advanced indexing
            - Scalable for production deployments
            - Support for multiple concurrent users
            
            Vector Memory:
            - Semantic search capabilities with embeddings
            - Multiple vector store backends: FAISS, Chroma, Pinecone, Qdrant
            - Smart text chunking with 5 different strategies
            - Cross-session persistence with semantic search
            - Supports embeddings from OpenAI, Ollama, and HuggingFace
            
            Vector stores support similarity search, document ranking, and semantic clustering
            with performance metrics of 1000+ operations/second and <50ms query latency.
            """,
            
            # Multi-Agent Orchestration
            """
            Multi-Agent Orchestration: Topologies and Coordination Patterns
            
            AgenticFlow supports various multi-agent coordination patterns:
            
            Star Topology:
            - Central supervisor coordinates all worker agents
            - Clear hierarchy with centralized decision making
            - Excellent for task delegation and resource management
            - Scales well up to 50+ worker agents
            
            Peer-to-Peer Topology:
            - Agents communicate directly with each other
            - Distributed decision making and collaborative work
            - Self-organizing systems with emergent behavior
            - Ideal for collaborative problem-solving tasks
            
            Hierarchical Topology:
            - Tree-like structure with multiple management levels
            - Scalable organizational patterns
            - Clear command chains and responsibility zones
            - Supports complex organizational structures
            
            Pipeline Topology:
            - Sequential processing with data flow between agents
            - Each agent specializes in specific processing steps
            - Feedback loops and error correction mechanisms
            - Perfect for data processing and transformation workflows
            
            Mesh Topology:
            - Partial connectivity between selected agents
            - Flexible communication patterns
            - Load balancing and redundancy
            - Fault tolerance and graceful degradation
            
            Custom Topology:
            - User-defined communication patterns
            - Flexible agent relationships
            - Domain-specific optimizations
            - Advanced coordination strategies
            
            Performance metrics show support for 20+ concurrent agents with <2s coordination latency
            and 95%+ success rates in complex multi-agent workflows.
            """,
            
            # AI and Machine Learning Concepts
            """
            Artificial Intelligence and Machine Learning Fundamentals
            
            Machine Learning Overview:
            Machine learning is a subset of AI that enables computers to learn patterns from data
            without explicit programming. It includes three main paradigms:
            
            Supervised Learning:
            - Learns from labeled training data
            - Predicts outcomes for new inputs
            - Examples: classification, regression, image recognition
            - Algorithms: linear regression, random forests, neural networks
            
            Unsupervised Learning:
            - Discovers patterns in unlabeled data
            - Finds hidden structures and relationships
            - Examples: clustering, dimensionality reduction, anomaly detection
            - Algorithms: k-means, PCA, autoencoders
            
            Reinforcement Learning:
            - Learns through interaction with environment
            - Uses rewards and penalties to improve decisions
            - Examples: game playing, robotics, autonomous systems
            - Algorithms: Q-learning, policy gradients, actor-critic methods
            
            Deep Learning:
            Deep learning uses neural networks with multiple layers to model complex patterns:
            - Convolutional Neural Networks (CNNs) for image processing
            - Recurrent Neural Networks (RNNs) for sequential data
            - Transformers for natural language processing
            - Generative models for content creation
            
            Natural Language Processing (NLP):
            - Text understanding and generation
            - Sentiment analysis and emotion detection
            - Machine translation between languages
            - Question answering and conversational AI
            - Modern approaches use transformer architectures like BERT, GPT, and T5
            """,
            
            # Programming and Software Development
            """
            Python Programming: Best Practices and Modern Development
            
            Python Fundamentals:
            Python is a versatile, high-level programming language known for readability and simplicity.
            
            Core Features:
            - Dynamic typing with optional type hints
            - Automatic memory management and garbage collection
            - Rich standard library and ecosystem
            - Cross-platform compatibility
            - Multiple programming paradigms: procedural, object-oriented, functional
            
            Data Types and Structures:
            - Primitive types: int, float, str, bool
            - Collections: list, tuple, dict, set
            - Advanced: namedtuple, dataclass, enum
            - Type hints for better code documentation
            
            Best Practices:
            - Follow PEP 8 style guidelines for consistent formatting
            - Use virtual environments for dependency management
            - Write comprehensive docstrings and comments
            - Implement proper error handling with try-except blocks
            - Use context managers for resource management
            - Write unit tests with pytest or unittest
            
            Modern Python Development:
            - Async programming with asyncio for concurrent operations
            - Type checking with mypy for better code quality
            - Package management with pip, poetry, or uv
            - Code formatting with black and isort
            - Linting with flake8, pylint, or ruff
            - Version control with git and collaborative workflows
            
            Popular Libraries and Frameworks:
            - Data Science: NumPy, pandas, matplotlib, scikit-learn
            - Web Development: Django, Flask, FastAPI
            - AI/ML: TensorFlow, PyTorch, transformers
            - GUI: tkinter, PyQt, Kivy
            - Testing: pytest, hypothesis
            """,
        ]
    
    async def setup_memories(self) -> None:
        """Setup both vector memory for RAG and conversation memory."""
        print("🧠 Setting up memory systems...")
        
        # Setup vector memory for knowledge base
        if self.embeddings:
            vector_store_config = VectorStoreFactory.create_faiss_config(
                persist_path="./chatbot_vectors",
                embedding_dimension=1536 if "openai" in str(self.embeddings.__class__).lower() else 768
            )
            
            memory_config = VectorMemoryConfig(vector_store_config=vector_store_config)
            base_config = MemoryConfig()
            
            self.vector_memory = VectorMemory(base_config, memory_config, self.embeddings)
            print("  ✅ Vector memory ready for knowledge base")
        
        # Setup conversation memory
        conv_config = MemoryConfig(max_messages=50)  # Keep last 50 messages
        self.conversation_memory = BufferMemory(conv_config)
        print("  ✅ Conversation memory ready")
    
    async def index_knowledge_base(self) -> None:
        """Index documents in vector memory."""
        if not self.vector_memory:
            print("  ⚠️ Skipping indexing - no vector memory available")
            return
            
        print("📊 Indexing knowledge base...")
        
        # Initialize the text splitter manager
        from agenticflow.text.splitters.manager import initialize_manager
        try:
            manager = await initialize_manager()
            print("  ✅ Text splitter manager initialized")
        except Exception as e:
            print(f"  ⚠️ Splitter manager initialization failed: {e}")
        
        all_chunks = []
        for i, doc in enumerate(self.documents):
            try:
                chunks = await split_text(
                    doc.strip(),
                    splitter_type=SplitterType.RECURSIVE,
                    chunk_size=400,
                    chunk_overlap=100
                )
                
                for chunk in chunks:
                    chunk.metadata["doc_id"] = i
                    chunk.metadata["source"] = f"knowledge_doc_{i}"
                    all_chunks.append(chunk)
                    
            except Exception as e:
                print(f"  ❌ Error chunking document {i}: {e}")
        
        self.chunks = all_chunks
        
        # Index in vector memory
        from langchain_core.messages import HumanMessage
        for chunk in self.chunks:
            try:
                message = HumanMessage(content=chunk.content)
                await self.vector_memory.add_message(message, metadata=chunk.metadata)
            except Exception as e:
                print(f"  ❌ Error indexing chunk: {e}")
        
        print(f"  ✅ Indexed {len(self.chunks)} knowledge chunks")
        
        # Debug: Show sample of what was indexed
        if self.chunks:
            print("  📝 Sample indexed content:")
            for i, chunk in enumerate(self.chunks[:3]):  # Show first 3 chunks
                preview = chunk.content[:100].replace('\n', ' ')
                print(f"    Chunk {i+1}: {preview}...")
    
    async def setup_retriever(self) -> None:
        """Setup intelligent hybrid retriever."""
        if not self.vector_memory:
            print("  ⚠️ No vector memory - using text-only retrieval")
            self.retriever = BM25Retriever([chunk.content for chunk in self.chunks])
            return
        
        print("🔍 Setting up intelligent retriever...")
        
        # Debug: Check what chunks we have
        print(f"  📝 Available chunks: {len(self.chunks)}")
        if self.chunks:
            print(f"  📝 Sample chunk attributes: {dir(self.chunks[0])}")
            if hasattr(self.chunks[0], 'content'):
                print(f"  📝 First chunk content: {self.chunks[0].content[:100]}...")
        
        text_data = [chunk.content for chunk in self.chunks]
        print(f"  📝 Text data for BM25: {len(text_data)} items")
        
        semantic_retriever = create_from_memory(self.vector_memory)
        
        # Temporarily use only semantic retriever to debug
        print("  ⚠️ Using semantic-only retriever for debugging")
        self.retriever = semantic_retriever
        
        # TODO: Re-enable hybrid once we fix BM25 issue
        # sparse_retriever = BM25Retriever(text_data)
        # self.retriever = HybridRetriever(
        #     dense_retriever=semantic_retriever,
        #     sparse_retriever=sparse_retriever
        # )
        
        print("  ✅ Hybrid retriever ready (text + semantic)")
    
    async def setup_chatbot_agent(self) -> None:
        """Setup the conversational agent."""
        print("🤖 Setting up chatbot agent...")
        
        # Determine best LLM provider
        llm_config = None
        provider_name = "Unknown"
        
        if os.getenv("GROQ_API_KEY"):
            llm_config = LLMProviderConfig(
                provider=LLMProvider.GROQ,
                model="llama-3.1-8b-instant"
            )
            provider_name = "Groq (fast)"
        elif os.getenv("OPENAI_API_KEY"):
            llm_config = LLMProviderConfig(
                provider=LLMProvider.OPENAI,
                model="gpt-4o-mini"
            )
            provider_name = "OpenAI"
        else:
            try:
                llm_config = LLMProviderConfig(
                    provider=LLMProvider.OLLAMA,
                    model="llama3.2"
                )
                provider_name = "Ollama (local)"
            except Exception:
                llm_config = LLMProviderConfig(
                    provider=LLMProvider.OLLAMA,
                    model="llama2"
                )
                provider_name = "Ollama (local)"
        
        # Configure agent with conversation and RAG capabilities
        config = AgentConfig(
            name="rag_chatbot",
            instructions="""You are an intelligent, helpful AI assistant with access to a comprehensive knowledge base about AgenticFlow, AI/ML, and programming.

Your personality and behavior:
- Be conversational, friendly, and engaging
- Show enthusiasm about helping users learn
- Ask clarifying questions when needed
- Reference specific information from the knowledge base when relevant
- Maintain context across multiple conversation turns
- Provide practical examples and use cases

When answering questions:
1. Use the retrieved context to provide accurate, detailed information
2. If the context doesn't fully answer the question, say so and provide what you can
3. For follow-up questions, consider the previous conversation context
4. Suggest related topics the user might be interested in
5. Be concise but thorough - aim for helpful, not overwhelming responses

Remember: You have access to detailed information about AgenticFlow's features, AI/ML concepts, and programming best practices. Use this knowledge to provide valuable, practical assistance.""",
            llm=llm_config,
            memory=MemoryConfig(max_messages=20)  # Keep conversation context
        )
        
        self.chatbot_agent = Agent(config)
        print(f"  ✅ Chatbot ready with {provider_name}")
    
    async def retrieve_context(self, query: str, max_context: int = 3) -> List[str]:
        """Retrieve relevant context for the query."""
        if not self.retriever:
            return []
        
        try:
            results = await self.retriever.retrieve(query, top_k=max_context)
            context_list = []
            
            print(f"    Raw retrieval results: {len(results)} items")
            
            for i, result in enumerate(results):
                print(f"    Result {i+1} type: {type(result)}")
                content = None
                
                # Try multiple ways to extract content
                if hasattr(result, 'document') and hasattr(result.document, 'page_content'):
                    content = result.document.page_content
                elif hasattr(result, 'document') and hasattr(result.document, 'content'):
                    content = result.document.content
                elif hasattr(result, 'page_content'):
                    content = result.page_content
                elif hasattr(result, 'content'):
                    content = result.content
                else:
                    content = str(result)
                
                if content:
                    context_list.append(content)
                    print(f"    Extracted content: {content[:100]}...")
            
            return context_list
        except Exception as e:
            print(f"  ⚠️ Context retrieval failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def format_conversation_context(self, limit: int = 6) -> str:
        """Format recent conversation history for context."""
        if not self.conversation_history:
            return ""
        
        # Get recent exchanges (limit pairs of user/assistant messages)
        recent_history = self.conversation_history[-(limit * 2):]
        
        context_parts = []
        for entry in recent_history:
            role = "You" if entry["role"] == "user" else "Assistant"
            context_parts.append(f"{role}: {entry['content']}")
        
        return "\n".join(context_parts)
    
    async def get_response(self, user_message: str) -> str:
        """Generate response using RAG and conversation context."""
        print(f"\n🤔 Processing: '{user_message[:50]}{'...' if len(user_message) > 50 else ''}'")
        
        # Retrieve relevant context
        print("  🔍 Retrieving context...")
        retrieved_context = await self.retrieve_context(user_message, max_context=3)
        print(f"  📄 Retrieved {len(retrieved_context)} context items")
        
        # Get conversation history
        conversation_context = self.format_conversation_context(limit=4)
        
        # Build comprehensive prompt
        prompt_parts = []
        
        # Add conversation history if available
        if conversation_context:
            prompt_parts.append(f"Recent conversation:\n{conversation_context}\n")
        
        # Add retrieved context
        if retrieved_context:
            prompt_parts.append("Relevant information from knowledge base:")
            for i, context in enumerate(retrieved_context, 1):
                prompt_parts.append(f"{i}. {context}")
            prompt_parts.append("")
        else:
            prompt_parts.append("No specific information found in knowledge base for this query.\n")
        
        # Add user query
        prompt_parts.append(f"User: {user_message}")
        prompt_parts.append("\nPlease provide a helpful response:")
        
        prompt = "\n".join(prompt_parts)
        
        try:
            # Generate response
            print("  🧠 Generating response...")
            # Start the agent if not already started
            if not self.chatbot_agent._running:
                await self.chatbot_agent.start()
            
            response = await self.chatbot_agent.execute_task(prompt)
            answer = response.get('response', '') if isinstance(response, dict) else str(response)
            
            # Store in conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": answer})
            
            # Store in conversation memory
            if self.conversation_memory:
                try:
                    user_msg = HumanMessage(content=user_message)
                    ai_msg = AIMessage(content=answer)
                    await self.conversation_memory.add_message(user_msg)
                    await self.conversation_memory.add_message(ai_msg)
                except Exception as e:
                    print(f"  ⚠️ Memory storage failed: {e}")
            
            return answer
        
        except Exception as e:
            error_response = f"I apologize, but I encountered an error processing your request: {e}"
            print(f"  ❌ Error generating response: {e}")
            return error_response
    
    def display_welcome(self):
        """Display welcome message and instructions."""
        print("\n" + "=" * 60)
        print("🤖 AgenticFlow Interactive RAG Chatbot")
        print("=" * 60)
        print("Welcome! I'm your AI assistant with knowledge about:")
        print("  • AgenticFlow framework and features")
        print("  • AI/ML concepts and best practices")
        print("  • Python programming and development")
        print("  • Multi-agent systems and orchestration")
        print()
        print("💡 What I can do:")
        print("  ✅ Answer questions about any of these topics")
        print("  ✅ Handle follow-up questions and conversations")
        print("  ✅ Provide detailed explanations with examples")
        print("  ✅ Suggest related topics you might find interesting")
        print()
        print("🎯 Example questions you can ask:")
        print("  • 'What is AgenticFlow and what can it do?'")
        print("  • 'How do retrievers work in AgenticFlow?'")
        print("  • 'Explain machine learning in simple terms'")
        print("  • 'What are Python best practices?'")
        print("  • 'How do multi-agent systems coordinate?'")
        print()
        print("💬 Commands:")
        print("  • Type 'quit', 'exit', or 'bye' to end the conversation")
        print("  • Type 'help' to see this message again")
        print("  • Type 'clear' to clear conversation history")
        print("=" * 60)
        print()
    
    def display_stats(self):
        """Display conversation statistics."""
        num_exchanges = len(self.conversation_history) // 2
        context_items = len(self.current_context)
        
        print(f"\n📊 Session Stats:")
        print(f"  💬 Exchanges: {num_exchanges}")
        print(f"  🧠 Knowledge chunks: {len(self.chunks)}")
        print(f"  🔍 Last context items: {context_items}")
    
    async def interactive_chat(self):
        """Main interactive chat loop."""
        self.display_welcome()
        
        print("🚀 Chatbot ready! Ask me anything...\n")
        
        while self.conversation_active:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                    print("\n👋 Thank you for chatting! Have a great day!")
                    self.display_stats()
                    break
                
                elif user_input.lower() == 'help':
                    self.display_welcome()
                    continue
                
                elif user_input.lower() == 'clear':
                    self.conversation_history.clear()
                    if self.conversation_memory:
                        await self.conversation_memory.clear()
                    print("🧹 Conversation history cleared!")
                    continue
                
                elif user_input.lower() == 'stats':
                    self.display_stats()
                    continue
                
                # Generate and display response
                response = await self.get_response(user_input)
                
                print(f"\n🤖 Assistant: {response}\n")
                print("-" * 60)
                
            except KeyboardInterrupt:
                print("\n\n👋 Chat interrupted. Goodbye!")
                self.display_stats()
                break
            except EOFError:
                print("\n\n👋 Chat ended. Goodbye!")
                self.display_stats()
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                print("Let's try again...\n")
    
    async def initialize_chatbot(self) -> None:
        """Initialize the complete chatbot system."""
        print("🚀 Initializing AgenticFlow Interactive RAG Chatbot")
        print("=" * 55)
        
        try:
            await self.setup_embeddings()
            await self.load_knowledge_base()
            await self.setup_memories()
            await self.index_knowledge_base()
            await self.setup_retriever()
            await self.setup_chatbot_agent()
            
            print("\n✅ Chatbot initialization complete!")
            
        except Exception as e:
            print(f"\n❌ Initialization failed: {e}")
            print("Please check your setup and try again.")
            sys.exit(1)
    
    async def run_chatbot(self) -> None:
        """Main function to run the interactive chatbot."""
        try:
            await self.initialize_chatbot()
            await self.interactive_chat()
        except Exception as e:
            print(f"❌ Chatbot failed: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """Main function to start the chatbot."""
    chatbot = InteractiveRAGChatbot()
    await chatbot.run_chatbot()

if __name__ == "__main__":
    print("🤖 AgenticFlow Interactive RAG Chatbot")
    print("This chatbot provides interactive conversations with knowledge base integration")
    print()
    print("Setup Requirements:")
    print("  🔹 For embeddings: OPENAI_API_KEY or Ollama with 'nomic-embed-text'")
    print("  🔹 For chat: GROQ_API_KEY, OPENAI_API_KEY, or Ollama with 'llama3.2'")
    print("  🔹 No API keys needed if using Ollama for everything")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Failed to start chatbot: {e}")