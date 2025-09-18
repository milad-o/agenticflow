#!/usr/bin/env python3
"""
Vector Store RAG System Example

This example demonstrates using different vector stores (FAISS, Chroma, In-Memory)
for RAG (Retrieval-Augmented Generation) with document ingestion and semantic search.

Features:
- Multiple vector store backends
- Document chunking and embedding
- Semantic similarity search
- Question answering with retrieved context
- Performance comparison between vector stores

Usage:
    python examples/vector_stores/rag_with_vectorstores.py
"""

import asyncio
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from agenticflow.vectorstores import ChromaVectorStore, FAISSVectorStore, InMemoryVectorStore
from agenticflow.text import split_text, ChunkingStrategy
from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from agenticflow import Agent, AgentConfig
from agenticflow.llm_providers import LLMProviderConfig, LLMProvider

class VectorStoreRAGDemo:
    """Demonstrate RAG with different vector store backends."""
    
    def __init__(self):
        self.documents: List[str] = []
        self.chunks: List[Any] = []
        self.embeddings: Optional[Any] = None
        self.vector_stores: Dict[str, Any] = {}
        self.qa_agent: Optional[Agent] = None
    
    async def setup_embeddings(self) -> None:
        """Setup embedding provider."""
        print("🧮 Setting up embeddings...")
        
        if os.getenv("OPENAI_API_KEY"):
            self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            print("  Using OpenAI embeddings")
        else:
            try:
                self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
                # Test connection
                await self.embeddings.aembed_query("test")
                print("  Using Ollama embeddings")
            except Exception as e:
                raise RuntimeError(f"No embedding provider available: {e}")
    
    async def load_sample_documents(self) -> None:
        """Load sample documents for testing."""
        print("📖 Loading sample documents...")
        
        # Sample documents about different topics
        self.documents = [
            """
            Machine Learning Fundamentals
            
            Machine learning is a subset of artificial intelligence that enables computers to learn 
            and improve from experience without being explicitly programmed. There are three main 
            types of machine learning:
            
            1. Supervised Learning: Uses labeled training data to learn patterns and make predictions
            2. Unsupervised Learning: Finds hidden patterns in unlabeled data
            3. Reinforcement Learning: Learns through interaction with an environment using rewards
            
            Popular algorithms include linear regression, decision trees, neural networks, and 
            support vector machines. Deep learning, using neural networks with many layers, has 
            revolutionized fields like computer vision and natural language processing.
            """,
            
            """
            Python Programming Essentials
            
            Python is a high-level, interpreted programming language known for its simplicity and 
            readability. Key features include:
            
            - Dynamic typing and automatic memory management
            - Extensive standard library and third-party packages
            - Support for multiple programming paradigms
            - Cross-platform compatibility
            
            Python data types include integers, floats, strings, lists, tuples, dictionaries, 
            and sets. Control structures include if/else statements, for/while loops, and 
            try/except error handling. Functions are defined with the 'def' keyword and 
            can accept parameters and return values.
            """,
            
            """
            Climate Change Science
            
            Climate change refers to long-term shifts in global temperatures and weather patterns. 
            While climate variations occur naturally, scientific evidence shows that human activities 
            have been the main driver since the mid-20th century.
            
            Key greenhouse gases include:
            - Carbon dioxide (CO2) from burning fossil fuels
            - Methane (CH4) from agriculture and landfills
            - Nitrous oxide (N2O) from fertilizers and fossil fuels
            
            Impacts include rising temperatures, melting ice caps, sea level rise, and extreme 
            weather events. Solutions involve reducing emissions through renewable energy, 
            energy efficiency, and sustainable practices.
            """,
            
            """
            Web Development Technologies
            
            Web development involves creating websites and web applications using various 
            technologies:
            
            Frontend technologies:
            - HTML for structure and content
            - CSS for styling and layout
            - JavaScript for interactivity and dynamic behavior
            - Frameworks like React, Vue.js, and Angular
            
            Backend technologies:
            - Server-side languages like Python, Java, Node.js, PHP
            - Databases like MySQL, PostgreSQL, MongoDB
            - Web servers like Apache, Nginx
            - Cloud platforms like AWS, Google Cloud, Azure
            
            Modern development uses responsive design, APIs, version control (Git), 
            and deployment automation.
            """
        ]
        
        print(f"📚 Loaded {len(self.documents)} sample documents")
    
    async def chunk_documents(self) -> None:
        """Chunk documents for better retrieval."""
        print("✂️ Chunking documents...")
        
        all_chunks = []
        for i, doc in enumerate(self.documents):
            chunks = await split_text(
                doc,
                splitter_type=ChunkingStrategy.RECURSIVE,
                chunk_size=300,
                chunk_overlap=50
            )
            
            # Add metadata
            for chunk in chunks:
                chunk.metadata["doc_id"] = i
                chunk.metadata["source"] = f"document_{i}"
                all_chunks.append(chunk)
        
        self.chunks = all_chunks
        print(f"📄 Created {len(self.chunks)} chunks")
    
    async def setup_vector_stores(self) -> None:
        """Setup different vector store backends."""
        print("🗄️ Setting up vector stores...")
        
        # In-Memory Vector Store (fastest, no persistence)
        self.vector_stores["inmemory"] = InMemoryVectorStore(
            embedding_function=self.embeddings
        )
        
        # FAISS Vector Store (fast, local persistence)
        try:
            self.vector_stores["faiss"] = FAISSVectorStore(
                embedding_function=self.embeddings,
                persist_path="./demo_faiss_index"
            )
        except Exception as e:
            print(f"  FAISS not available: {e}")
        
        # Chroma Vector Store (full-featured, persistent)
        try:
            self.vector_stores["chroma"] = ChromaVectorStore(
                collection_name="rag_demo",
                embedding_function=self.embeddings,
                persist_directory="./demo_chroma_db"
            )
        except Exception as e:
            print(f"  Chroma not available: {e}")
        
        print(f"✅ Setup {len(self.vector_stores)} vector stores")
    
    async def index_documents(self) -> None:
        """Index documents in all vector stores."""
        print("📊 Indexing documents in vector stores...")
        
        # Prepare documents for indexing
        texts = [chunk.content for chunk in self.chunks]
        metadatas = [chunk.metadata for chunk in self.chunks]
        
        for store_name, store in self.vector_stores.items():
            try:
                start_time = time.time()
                
                # Add documents to vector store
                await store.aadd_texts(texts, metadatas=metadatas)
                
                duration = time.time() - start_time
                print(f"  {store_name}: indexed {len(texts)} chunks in {duration:.2f}s")
                
            except Exception as e:
                print(f"  ❌ {store_name} indexing failed: {e}")
    
    async def setup_qa_agent(self) -> None:
        """Setup question answering agent."""
        print("🤖 Setting up Q&A agent...")
        
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
        
        config = AgentConfig(
            name="vector_rag_assistant",
            instructions="""You are a helpful assistant that answers questions based on retrieved context.
            Provide accurate answers using the provided information. If insufficient information is 
            available, clearly state the limitations.""",
            llm=llm_config
        )
        
        self.qa_agent = Agent(config)
    
    async def test_retrieval(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """Test retrieval across all vector stores."""
        print(f"\n🔍 Testing retrieval for: '{query}'")
        print("=" * 60)
        
        results = {}
        
        for store_name, store in self.vector_stores.items():
            try:
                start_time = time.time()
                
                # Perform similarity search
                docs = await store.asimilarity_search(query, k=top_k)
                
                duration = time.time() - start_time
                results[store_name] = {
                    "documents": docs,
                    "duration": duration,
                    "count": len(docs)
                }
                
                print(f"\n📊 {store_name.upper()}:")
                print(f"   Time: {duration:.3f}s | Results: {len(docs)}")
                
                for i, doc in enumerate(docs[:2]):  # Show top 2
                    content = doc.page_content[:80] + "..." if len(doc.page_content) > 80 else doc.page_content
                    print(f"   {i+1}. {content}")
                
            except Exception as e:
                print(f"❌ {store_name} retrieval failed: {e}")
                results[store_name] = {"error": str(e)}
        
        return results
    
    async def answer_with_rag(self, question: str, store_name: str = "inmemory") -> str:
        """Answer question using RAG with specified vector store."""
        print(f"\n💬 Answering with {store_name.upper()}: '{question}'")
        
        if store_name not in self.vector_stores:
            return f"Vector store '{store_name}' not available"
        
        try:
            # Retrieve relevant documents
            store = self.vector_stores[store_name]
            docs = await store.asimilarity_search(question, k=3)
            
            # Build context
            context_parts = []
            for i, doc in enumerate(docs):
                context_parts.append(f"Context {i+1}: {doc.page_content}")
            
            context = "\\n\\n".join(context_parts)
            
            # Generate answer
            prompt = f"""Based on the provided context, answer the question accurately.
            
Context:
{context}

Question: {question}

Answer:"""
            
            response = await self.qa_agent.execute(prompt)
            answer = response.content if hasattr(response, 'content') else str(response)
            
            print(f"📝 Answer: {answer}")
            print(f"📚 Used {len(docs)} context documents")
            
            return answer
            
        except Exception as e:
            error_msg = f"Error: {e}"
            print(f"❌ {error_msg}")
            return error_msg
    
    async def compare_vector_stores(self, queries: List[str]) -> None:
        """Compare performance across vector stores."""
        print("\\n📈 VECTOR STORE PERFORMANCE COMPARISON")
        print("=" * 60)
        
        performance_data = {}
        
        for query in queries:
            results = await self.test_retrieval(query)
            
            for store_name, data in results.items():
                if "error" not in data:
                    if store_name not in performance_data:
                        performance_data[store_name] = {"durations": [], "counts": []}
                    
                    performance_data[store_name]["durations"].append(data["duration"])
                    performance_data[store_name]["counts"].append(data["count"])
        
        # Calculate and display averages
        print(f"\\n📊 AVERAGE PERFORMANCE ACROSS {len(queries)} QUERIES:")
        print(f"{'Store':<10} {'Avg Time (s)':<12} {'Avg Results':<12}")
        print("-" * 35)
        
        for store_name, data in performance_data.items():
            avg_time = sum(data["durations"]) / len(data["durations"])
            avg_count = sum(data["counts"]) / len(data["counts"])
            print(f"{store_name:<10} {avg_time:<12.3f} {avg_count:<12.1f}")
    
    async def run_demo(self) -> None:
        """Run the complete vector store RAG demonstration."""
        print("🚀 Vector Store RAG Demo")
        print("=" * 40)
        
        try:
            await self.setup_embeddings()
            await self.load_sample_documents()
            await self.chunk_documents()
            await self.setup_vector_stores()
            await self.index_documents()
            await self.setup_qa_agent()
            
            # Test queries
            test_queries = [
                "What is machine learning?",
                "What are Python data types?",
                "What causes climate change?",
                "What is web development?"
            ]
            
            # Performance comparison
            await self.compare_vector_stores(test_queries)
            
            # Question answering
            print("\\n🎯 QUESTION ANSWERING DEMO")
            print("=" * 40)
            
            qa_questions = [
                "What are the types of machine learning?",
                "How do you define functions in Python?",
                "What are greenhouse gases?"
            ]
            
            for question in qa_questions:
                # Try different vector stores
                for store_name in self.vector_stores.keys():
                    try:
                        await self.answer_with_rag(question, store_name)
                        break  # Success, move to next question
                    except Exception as e:
                        print(f"❌ {store_name} failed: {e}")
                        continue
                
                print("\\n" + "-" * 40)
            
            print("\\n✅ Vector Store RAG Demo Complete!")
            
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """Run the vector store RAG demo."""
    demo = VectorStoreRAGDemo()
    await demo.run_demo()

if __name__ == "__main__":
    print("🗄️ AgenticFlow Vector Store RAG Demo")
    print("This demo shows how to use different vector stores for RAG")
    print()
    print("Requirements:")
    print("- OPENAI_API_KEY or Ollama with 'nomic-embed-text' model")
    print("- GROQ_API_KEY for question answering (optional)")
    print()
    
    asyncio.run(main())