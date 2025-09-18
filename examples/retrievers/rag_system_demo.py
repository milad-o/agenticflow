#!/usr/bin/env python3
"""
Comprehensive RAG (Retrieval-Augmented Generation) System Demo

This demo showcases AgenticFlow's retriever system with text file ingestion,
embedding, and various retrieval strategies for question answering.

Features demonstrated:
- Text file ingestion and chunking
- Multiple embedding providers (OpenAI, Ollama, HuggingFace)
- Various retriever types (Text, Semantic, Composite)
- Vector store integration
- Performance comparison
- Question answering with retrieved context

Usage:
    python examples/retrievers/rag_system_demo.py
"""

import asyncio
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# AgenticFlow imports
from agenticflow.memory import VectorMemory
from agenticflow.memory.vector_memory import VectorMemoryConfig
from agenticflow.config.settings import MemoryConfig
from agenticflow.retrievers import (
    KeywordRetriever, BM25Retriever, FuzzyRetriever,
    SemanticRetriever, CosineRetriever, 
    EnsembleRetriever, HybridRetriever,
    create_from_memory
)
from agenticflow.vectorstores.factory import VectorStoreFactory
from agenticflow.text import split_text, ChunkingStrategy, ChunkingConfig
from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings

# For question answering
from agenticflow import Agent, AgentConfig
from agenticflow.llm_providers import LLMProviderConfig, LLMProvider

class RAGSystemDemo:
    """Comprehensive RAG system demonstration."""
    
    def __init__(self, docs_path: str = "examples/retrievers/sample_docs"):
        self.docs_path = Path(docs_path)
        self.documents: List[str] = []
        self.chunks: List[Any] = []
        self.memory: Optional[VectorMemory] = None
        self.retrievers: Dict[str, Any] = {}
        
    async def setup_embeddings(self) -> Any:
        """Setup embedding provider with fallback options."""
        print("🧮 Setting up embedding provider...")
        
        # Try OpenAI first (best quality)
        if os.getenv("OPENAI_API_KEY"):
            print("  Using OpenAI embeddings")
            return OpenAIEmbeddings(model="text-embedding-3-small")
        
        # Fallback to Ollama (local, free)
        try:
            embeddings = OllamaEmbeddings(model="nomic-embed-text")
            # Test connection
            await embeddings.aembed_query("test")
            print("  Using Ollama embeddings (local)")
            return embeddings
        except Exception as e:
            print(f"  Ollama not available: {e}")
            
        # Fallback to HuggingFace (if available)
        try:
            from agenticflow.llm_providers import HuggingFaceEmbeddings
            print("  Using HuggingFace embeddings")
            return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        except Exception as e:
            print(f"  HuggingFace not available: {e}")
            
        raise RuntimeError("No embedding provider available. Please install Ollama or set OPENAI_API_KEY.")
    
    async def load_documents(self) -> None:
        """Load text documents from the sample docs directory."""
        print("📖 Loading documents...")
        
        self.docs_path.mkdir(parents=True, exist_ok=True)
        text_files = list(self.docs_path.glob("*.txt"))
        
        if not text_files:
            print("  No text files found. Creating sample documents...")
            await self.create_sample_docs()
            text_files = list(self.docs_path.glob("*.txt"))
        
        for file_path in text_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.documents.append(content)
                    print(f"  Loaded: {file_path.name} ({len(content)} chars)")
            except Exception as e:
                print(f"  Error loading {file_path}: {e}")
        
        print(f"📚 Loaded {len(self.documents)} documents")
    
    async def create_sample_docs(self) -> None:
        """Create sample documents if none exist."""
        sample_docs = {
            "ai_basics.txt": """
Artificial Intelligence Overview
AI is the simulation of human intelligence in machines. It includes machine learning, 
deep learning, and natural language processing. Modern AI systems can perform complex 
tasks like image recognition, language translation, and decision making.
            """,
            "python_guide.txt": """
Python Programming Basics
Python is a versatile programming language known for its simplicity and readability.
It supports multiple programming paradigms and has extensive libraries for web development,
data science, machine learning, and automation.
            """,
            "climate_facts.txt": """
Climate Science Fundamentals
Climate change refers to long-term shifts in global temperatures and weather patterns.
Human activities, particularly greenhouse gas emissions, are the primary cause of recent
climate change. Mitigation and adaptation strategies are crucial for addressing these challenges.
            """
        }
        
        for filename, content in sample_docs.items():
            file_path = self.docs_path / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content.strip())
            print(f"  Created sample: {filename}")
    
    async def chunk_documents(self) -> None:
        """Chunk documents using different strategies."""
        print("✂️ Chunking documents...")
        
        all_chunks = []
        for i, doc in enumerate(self.documents):
            # Use recursive chunking for good balance
            chunks = await split_text(
                doc,
                splitter_type=ChunkingStrategy.RECURSIVE,
                chunk_size=500,
                chunk_overlap=100
            )
            
            # Add document metadata
            for chunk in chunks:
                chunk.metadata["doc_id"] = i
                chunk.metadata["doc_source"] = f"document_{i}"
                all_chunks.append(chunk)
        
        self.chunks = all_chunks
        print(f"📄 Created {len(self.chunks)} chunks from {len(self.documents)} documents")
    
    async def setup_vector_memory(self, embeddings: Any) -> None:
        """Setup vector memory for semantic search."""
        print("🧠 Setting up vector memory...")
        
        # Configure vector store (FAISS for local demo)
        vector_store_config = VectorStoreFactory.create_faiss_config(
            persist_path="./rag_demo_vectors",
            embedding_dimension=1536 if "openai" in str(embeddings.__class__).lower() else 768
        )
        
        # Configure vector memory
        from agenticflow.vectorstores import VectorStoreConfig
        from agenticflow.text.splitters import SplitterConfig
        
        memory_config = VectorMemoryConfig(
            vector_store_config=vector_store_config,
            splitter_config=SplitterConfig()
        )
        
        base_config = MemoryConfig()
        self.memory = VectorMemory(base_config, memory_config, embeddings)
        await self.memory.initialize()
        
        # Index all chunks
        print("📊 Indexing chunks...")
        from langchain_core.messages import HumanMessage
        
        for chunk in self.chunks:
            # Convert chunk to message for VectorMemory
            message = HumanMessage(content=chunk.content)
            await self.memory.add_message(message, metadata=chunk.metadata)
        
        print(f"✅ Indexed {len(self.chunks)} chunks in vector memory")
    
    async def setup_retrievers(self) -> None:
        """Setup various retriever types."""
        print("🔍 Setting up retrievers...")
        
        # Text-based retrievers (work with raw text)
        text_data = [chunk.content for chunk in self.chunks]
        
        self.retrievers = {
            # Text retrievers
            "keyword": KeywordRetriever(text_data),
            "bm25": BM25Retriever(text_data),
            "fuzzy": FuzzyRetriever(text_data),
            
            # Semantic retrievers (work with vector memory)
            "semantic": create_from_memory(self.memory),
            "cosine": CosineRetriever.from_memory(self.memory),
            
            # Composite retrievers
            "ensemble": EnsembleRetriever([
                KeywordRetriever(text_data),
                BM25Retriever(text_data),
                create_from_memory(self.memory)
            ]),
            "hybrid": HybridRetriever(
                text_retriever=BM25Retriever(text_data),
                semantic_retriever=create_from_memory(self.memory)
            )
        }
        
        print(f"🛠️ Setup {len(self.retrievers)} different retriever types")
    
    async def test_retrievers(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """Test all retrievers with a query."""
        print(f"\n🔍 Testing retrievers with query: '{query}'")
        print("=" * 60)
        
        results = {}
        
        for name, retriever in self.retrievers.items():
            try:
                start_time = time.time()
                retriever_results = await retriever.retrieve(query, top_k=top_k)
                duration = time.time() - start_time
                
                results[name] = {
                    "results": retriever_results,
                    "duration": duration,
                    "count": len(retriever_results)
                }
                
                print(f"\n📊 {name.upper()} RETRIEVER:")
                print(f"   Time: {duration:.3f}s | Results: {len(retriever_results)}")
                
                for i, result in enumerate(retriever_results[:2]):  # Show top 2
                    content = result.content[:100] + "..." if len(result.content) > 100 else result.content
                    score = getattr(result, 'score', 0.0)
                    print(f"   {i+1}. Score: {score:.3f} | {content}")
                    
            except Exception as e:
                print(f"❌ {name} retriever failed: {e}")
                results[name] = {"error": str(e)}
        
        return results
    
    async def compare_retriever_performance(self, queries: List[str]) -> None:
        """Compare performance across multiple queries."""
        print("\n📈 RETRIEVER PERFORMANCE COMPARISON")
        print("=" * 60)
        
        performance_data = {}
        
        for query in queries:
            print(f"\nQuery: '{query}'")
            results = await self.test_retrievers(query, top_k=5)
            
            for name, data in results.items():
                if "error" not in data:
                    if name not in performance_data:
                        performance_data[name] = {"durations": [], "avg_results": []}
                    
                    performance_data[name]["durations"].append(data["duration"])
                    performance_data[name]["avg_results"].append(data["count"])
        
        # Calculate averages
        print(f"\n📊 AVERAGE PERFORMANCE ACROSS {len(queries)} QUERIES:")
        print(f"{'Retriever':<12} {'Avg Time (s)':<12} {'Avg Results':<12}")
        print("-" * 40)
        
        for name, data in performance_data.items():
            avg_time = sum(data["durations"]) / len(data["durations"])
            avg_results = sum(data["avg_results"]) / len(data["avg_results"])
            print(f"{name:<12} {avg_time:<12.3f} {avg_results:<12.1f}")
    
    async def setup_qa_agent(self) -> Agent:
        """Setup agent for question answering."""
        print("🤖 Setting up Q&A agent...")
        
        # Try different LLM providers
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
            # Try Ollama
            llm_config = LLMProviderConfig(
                provider=LLMProvider.OLLAMA,
                model="llama3.2"
            )
        
        config = AgentConfig(
            name="rag_assistant",
            instructions="""You are a helpful assistant that answers questions based on provided context.
            Use the retrieved information to answer questions accurately. If the context doesn't contain 
            enough information, say so clearly.""",
            llm=llm_config
        )
        
        agent = Agent(config)
        return agent
    
    async def answer_question_with_rag(self, question: str, retriever_name: str = "hybrid") -> str:
        """Answer a question using RAG with specified retriever."""
        print(f"\n💬 Answering with {retriever_name.upper()} retriever: '{question}'")
        
        # Retrieve relevant context
        retriever = self.retrievers[retriever_name]
        results = await retriever.retrieve(question, top_k=3)
        
        # Build context
        context_parts = []
        for i, result in enumerate(results[:3]):
            context_parts.append(f"Context {i+1}: {result.content}")
        
        context = "\n\n".join(context_parts)
        
        # Setup agent and answer
        agent = await self.setup_qa_agent()
        
        prompt = f"""Based on the following context, please answer the question.

Context:
{context}

Question: {question}

Answer:"""

        try:
            response = await agent.execute(prompt)
            answer = response.content if hasattr(response, 'content') else str(response)
            
            print(f"📝 Answer: {answer}")
            print(f"📚 Used {len(results)} context chunks")
            
            return answer
        except Exception as e:
            print(f"❌ Error generating answer: {e}")
            return f"Error: {e}"
    
    async def run_comprehensive_demo(self) -> None:
        """Run the complete RAG system demonstration."""
        print("🚀 Starting Comprehensive RAG System Demo")
        print("=" * 50)
        
        try:
            # Setup components
            await self.load_documents()
            await self.chunk_documents()
            
            embeddings = await self.setup_embeddings()
            await self.setup_vector_memory(embeddings)
            await self.setup_retrievers()
            
            # Test queries
            test_queries = [
                "What is machine learning?",
                "How does Python handle data types?",
                "What causes climate change?",
                "What are neural networks?",
                "How do you write functions in Python?"
            ]
            
            # Performance comparison
            await self.compare_retriever_performance(test_queries)
            
            # Question answering demo
            print("\n🎯 QUESTION ANSWERING DEMONSTRATION")
            print("=" * 50)
            
            qa_questions = [
                "What are the main types of machine learning?",
                "What are Python's built-in data types?",
                "What are the main causes of climate change?"
            ]
            
            for question in qa_questions:
                # Try different retrievers
                for retriever_name in ["hybrid", "semantic", "bm25"]:
                    try:
                        await self.answer_question_with_rag(question, retriever_name)
                        break  # If successful, don't try other retrievers
                    except Exception as e:
                        print(f"❌ {retriever_name} failed: {e}")
                        continue
                
                print("\n" + "-" * 50)
            
            print("\n✅ RAG System Demo Complete!")
            
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """Main function to run the RAG demo."""
    demo = RAGSystemDemo()
    await demo.run_comprehensive_demo()

if __name__ == "__main__":
    print("🔍 AgenticFlow RAG System Demo")
    print("This demo showcases text ingestion, embedding, and retrieval capabilities")
    print("Ensure you have either:")
    print("- OPENAI_API_KEY set for OpenAI embeddings")
    print("- Ollama running with 'nomic-embed-text' model")
    print("- GROQ_API_KEY set for question answering")
    print()
    
    asyncio.run(main())