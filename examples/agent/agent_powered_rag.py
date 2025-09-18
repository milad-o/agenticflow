#!/usr/bin/env python3
"""
Agent-Powered RAG System

This example demonstrates a conversational RAG system where agents can intelligently
retrieve and use context from documents to answer questions naturally.

Features:
- Conversational interface with memory
- Intelligent context retrieval
- Multi-turn conversations with context awareness
- Agent memory for conversation history
- Smart retriever selection based on query type

Usage:
    python examples/agent/agent_powered_rag.py
"""

import asyncio
import os
from pathlib import Path
from typing import List, Optional, Dict, Any

from agenticflow import Agent, AgentConfig
from agenticflow.llm_providers import LLMProviderConfig, LLMProvider
from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from agenticflow.memory import VectorMemory
from agenticflow.memory.vector_memory import VectorMemoryConfig
from agenticflow.config.settings import MemoryConfig
from agenticflow.vectorstores.factory import VectorStoreFactory
from agenticflow.text import split_text, ChunkingStrategy
from agenticflow.retrievers import (
    HybridRetriever, BM25Retriever, create_from_memory,
    EnsembleRetriever, KeywordRetriever
)

class AgentPoweredRAG:
    """Intelligent RAG system with conversational agent interface."""
    
    def __init__(self):
        self.documents: List[str] = []
        self.chunks: List[Any] = []
        self.embeddings: Optional[Any] = None
        self.memory: Optional[VectorMemory] = None
        self.retriever: Optional[Any] = None
        self.rag_agent: Optional[Agent] = None
        self.conversation_history: List[Dict[str, str]] = []
    
    async def setup_embeddings(self) -> None:
        """Setup embedding provider."""
        print("🧮 Setting up embeddings...")
        
        if os.getenv("OPENAI_API_KEY"):
            self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            print("  Using OpenAI embeddings")
        else:
            try:
                self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
                await self.embeddings.aembed_query("test")
                print("  Using Ollama embeddings")
            except Exception as e:
                raise RuntimeError(f"No embedding provider available: {e}")
    
    async def load_knowledge_base(self) -> None:
        """Load knowledge base documents."""
        print("📚 Loading knowledge base...")
        
        # Check if sample docs exist from retriever examples
        sample_docs_path = Path("examples/retrievers/sample_docs")
        if sample_docs_path.exists():
            # Load from existing sample docs
            text_files = list(sample_docs_path.glob("*.txt"))
            for file_path in text_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        self.documents.append(content)
                        print(f"  Loaded: {file_path.name}")
                except Exception as e:
                    print(f"  Error loading {file_path}: {e}")
        
        # If no docs found, create sample knowledge base
        if not self.documents:
            self.documents = await self.create_sample_knowledge_base()
        
        print(f"📖 Loaded {len(self.documents)} knowledge base documents")
    
    async def create_sample_knowledge_base(self) -> List[str]:
        """Create a sample knowledge base if none exists."""
        print("  Creating sample knowledge base...")
        
        return [
            """
            AgenticFlow Framework Documentation
            
            AgenticFlow is a comprehensive AI agent framework for building multi-agent systems.
            Key features include:
            
            - Multiple agent topologies (Star, Peer-to-Peer, Hierarchical, Pipeline, Mesh)
            - Advanced memory systems with vector storage capabilities
            - Intelligent retriever system with 15+ retriever types
            - MCP (Model Context Protocol) integration for external tool access
            - Production-ready orchestration with task dependencies
            - Comprehensive embedding provider support
            
            The framework supports async-first architecture and is designed for enterprise-grade
            applications with high performance and scalability requirements.
            """,
            
            """
            Retriever System in AgenticFlow
            
            AgenticFlow provides a comprehensive retriever system with multiple types:
            
            Text-based Retrievers:
            - KeywordRetriever: Exact keyword matching
            - BM25Retriever: Statistical ranking algorithm
            - FuzzyRetriever: Approximate string matching
            - RegexRetriever: Pattern-based retrieval
            
            Semantic Retrievers:
            - SemanticRetriever: Vector similarity search
            - CosineRetriever: Cosine similarity matching
            - EuclideanRetriever: Euclidean distance matching
            
            Composite Retrievers:
            - EnsembleRetriever: Combines multiple retrievers
            - HybridRetriever: Blends text and semantic approaches
            - ContextualRetriever: Context-aware retrieval
            
            Each retriever can be optimized for different use cases and query types.
            """,
            
            """
            Memory Systems and Vector Storage
            
            AgenticFlow supports multiple memory backends:
            
            Buffer Memory:
            - Fast in-memory storage
            - No persistence between sessions
            - Best for temporary conversations
            
            SQLite Memory:
            - Local database storage
            - Session persistence
            - Good for development and small applications
            
            PostgreSQL Memory:
            - Enterprise database backend
            - Full ACID compliance
            - Suitable for production deployments
            
            Vector Memory:
            - Semantic search capabilities
            - Multiple vector store backends (FAISS, Chroma, Pinecone)
            - Supports embeddings and similarity search
            - Cross-session persistence with chunking strategies
            """,
            
            """
            Multi-Agent Orchestration Patterns
            
            AgenticFlow supports various multi-agent coordination patterns:
            
            Star Topology:
            - Central supervisor agent coordinates worker agents
            - Clear hierarchy and centralized control
            - Good for task delegation scenarios
            
            Peer-to-Peer Topology:
            - Agents communicate directly with each other
            - Distributed decision making
            - Suitable for collaborative tasks
            
            Hierarchical Topology:
            - Tree-like structure with multiple levels
            - Scalable organization
            - Supports complex organizational structures
            
            Pipeline Topology:
            - Sequential processing with feedback loops
            - Each agent processes and passes to the next
            - Ideal for data processing workflows
            
            Each topology can be configured with custom communication protocols and coordination strategies.
            """
        ]
    
    async def prepare_knowledge_base(self) -> None:
        """Chunk and prepare knowledge base for retrieval."""
        print("✂️ Preparing knowledge base...")
        
        all_chunks = []
        for i, doc in enumerate(self.documents):
            chunks = await split_text(
                doc.strip(),
                splitter_type=ChunkingStrategy.RECURSIVE,
                chunk_size=400,
                chunk_overlap=100
            )
            
            for chunk in chunks:
                chunk.metadata["doc_id"] = i
                chunk.metadata["source"] = f"knowledge_doc_{i}"
                all_chunks.append(chunk)
        
        self.chunks = all_chunks
        print(f"📄 Created {len(self.chunks)} knowledge chunks")
    
    async def setup_vector_memory(self) -> None:
        """Setup vector memory for semantic search."""
        print("🧠 Setting up vector memory...")
        
        vector_store_config = VectorStoreFactory.create_faiss_config(
            persist_path="./agent_rag_vectors",
            embedding_dimension=1536 if "openai" in str(self.embeddings.__class__).lower() else 768
        )
        
        memory_config = VectorMemoryConfig(vector_store_config=vector_store_config)
        base_config = MemoryConfig()
        
        self.memory = VectorMemory(base_config, memory_config, self.embeddings)
        await self.memory.initialize()
        
        # Index all chunks
        from langchain_core.messages import HumanMessage
        
        for chunk in self.chunks:
            message = HumanMessage(content=chunk.content)
            await self.memory.add_message(message, metadata=chunk.metadata)
        
        print("✅ Vector memory ready")
    
    async def setup_intelligent_retriever(self) -> None:
        """Setup intelligent retriever system."""
        print("🔍 Setting up intelligent retriever...")
        
        # Create hybrid retriever combining text and semantic approaches
        text_data = [chunk.content for chunk in self.chunks]
        
        self.retriever = HybridRetriever(
            text_retriever=BM25Retriever(text_data),
            semantic_retriever=create_from_memory(self.memory),
            text_weight=0.3,  # Favor semantic retrieval slightly
            semantic_weight=0.7
        )
        
        print("🎯 Intelligent retriever ready")
    
    async def setup_rag_agent(self) -> None:
        """Setup the conversational RAG agent."""
        print("🤖 Setting up RAG agent...")
        
        # Determine LLM provider
        llm_config = None
        if os.getenv("GROQ_API_KEY"):
            llm_config = LLMProviderConfig(
                provider=LLMProvider.GROQ,
                model="llama-3.1-8b-instant"
            )
        elif os.getenv("OPENAI_API_KEY"):
            llm_config = LLMProviderConfig(
                provider=LLMProvider.OPENAI,
                model="gpt-4o-mini"
            )
        else:
            llm_config = LLMProviderConfig(
                provider=LLMProvider.OLLAMA,
                model="llama3.2"
            )
        
        # Configure agent
        config = AgentConfig(
            name="rag_expert",
            instructions="""You are a knowledgeable AI assistant with access to AgenticFlow documentation.
            
            Your role:
            1. Answer questions about AgenticFlow using the provided context
            2. Be conversational and helpful
            3. If you don't have enough context, ask for clarification
            4. Reference the retrieved information when answering
            5. Maintain context across multiple turns in the conversation
            
            Always provide accurate, helpful responses based on the retrieved context.
            If the context doesn't contain the answer, say so clearly and suggest what information might help.""",
            llm=llm_config
        )
        
        self.rag_agent = Agent(config)
        print("✅ RAG agent ready")
    
    async def retrieve_context(self, query: str, top_k: int = 3) -> str:
        """Retrieve relevant context for a query."""
        try:
            results = await self.retriever.retrieve(query, top_k=top_k)
            
            if not results:
                return "No relevant information found in the knowledge base."
            
            context_parts = []
            for i, result in enumerate(results):
                context_parts.append(f"Context {i+1}:\n{result.content}")
            
            return "\n\n".join(context_parts)
        except Exception as e:
            return f"Error retrieving context: {e}"
    
    def format_conversation_history(self) -> str:
        """Format recent conversation history."""
        if not self.conversation_history:
            return ""
        
        # Keep last 3 exchanges for context
        recent_history = self.conversation_history[-6:]  # 3 Q&A pairs
        
        history_parts = []
        for exchange in recent_history:
            if exchange["type"] == "user":
                history_parts.append(f"User: {exchange['content']}")
            else:
                history_parts.append(f"Assistant: {exchange['content']}")
        
        return "\n".join(history_parts)
    
    async def ask_question(self, question: str) -> str:
        """Ask a question to the RAG agent."""
        print(f"\n💬 User: {question}")
        
        # Retrieve relevant context
        print("🔍 Retrieving context...")
        context = await self.retrieve_context(question)
        
        # Format conversation history
        history = self.format_conversation_history()
        
        # Build prompt with context and history
        prompt_parts = []
        
        if history:
            prompt_parts.append(f"Recent conversation history:\n{history}\n")
        
        prompt_parts.extend([
            f"Retrieved context:\n{context}\n",
            f"User question: {question}\n",
            "Please provide a helpful answer based on the context and conversation history:"
        ])
        
        prompt = "\n".join(prompt_parts)
        
        try:
            # Generate response
            response = await self.rag_agent.execute(prompt)
            answer = response.content if hasattr(response, 'content') else str(response)
            
            # Update conversation history
            self.conversation_history.append({"type": "user", "content": question})
            self.conversation_history.append({"type": "assistant", "content": answer})
            
            print(f"🤖 Assistant: {answer}")
            return answer
            
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {e}"
            print(f"❌ {error_msg}")
            return error_msg
    
    async def interactive_session(self) -> None:
        """Run an interactive Q&A session."""
        print("\n🎯 INTERACTIVE RAG SESSION")
        print("=" * 50)
        print("Ask questions about AgenticFlow! Type 'quit' to exit.\n")
        
        # Sample questions to get started
        sample_questions = [
            "What is AgenticFlow?",
            "What types of retrievers are available?",
            "How do memory systems work?",
            "What agent topologies are supported?"
        ]
        
        print("💡 Sample questions you can ask:")
        for i, q in enumerate(sample_questions, 1):
            print(f"   {i}. {q}")
        print()
        
        while True:
            try:
                user_input = input("Your question: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Thanks for using AgenticFlow RAG! Goodbye!")
                    break
                
                await self.ask_question(user_input)
                print("\n" + "-" * 50)
                
            except KeyboardInterrupt:
                print("\n\n👋 Thanks for using AgenticFlow RAG! Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    async def demo_conversation(self) -> None:
        """Run a demo conversation to showcase capabilities."""
        print("\n🎭 DEMO CONVERSATION")
        print("=" * 40)
        
        demo_questions = [
            "What is AgenticFlow and what are its main features?",
            "Can you tell me more about the retriever system?",
            "Which retriever would be best for keyword search?",
            "What about semantic search capabilities?",
            "How do the memory systems work?",
            "What's the difference between vector memory and SQLite memory?"
        ]
        
        for question in demo_questions:
            await self.ask_question(question)
            print()
            await asyncio.sleep(1)  # Pause between questions
    
    async def initialize_system(self) -> None:
        """Initialize the complete RAG system."""
        print("🚀 INITIALIZING AGENT-POWERED RAG SYSTEM")
        print("=" * 50)
        
        try:
            await self.setup_embeddings()
            await self.load_knowledge_base()
            await self.prepare_knowledge_base()
            await self.setup_vector_memory()
            await self.setup_intelligent_retriever()
            await self.setup_rag_agent()
            
            print("\n✅ RAG system ready!")
            
        except Exception as e:
            print(f"❌ System initialization failed: {e}")
            raise
    
    async def run_demo(self) -> None:
        """Run the complete RAG demo."""
        try:
            await self.initialize_system()
            await self.demo_conversation()
            await self.interactive_session()
            
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """Main function to run the agent-powered RAG demo."""
    rag_system = AgentPoweredRAG()
    await rag_system.run_demo()

if __name__ == "__main__":
    print("🤖 AgenticFlow Agent-Powered RAG System")
    print("This demo shows conversational RAG with intelligent context retrieval")
    print()
    print("Requirements:")
    print("- OPENAI_API_KEY or Ollama with 'nomic-embed-text' model for embeddings")
    print("- GROQ_API_KEY, OPENAI_API_KEY, or Ollama with 'llama3.2' for chat")
    print()
    
    asyncio.run(main())