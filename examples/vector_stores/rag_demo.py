#!/usr/bin/env python3
"""
RAG (Retrieval Augmented Generation) Demo
=========================================

This demo shows how to build a complete RAG system using AgenticFlow:
1. Document ingestion and chunking
2. Embedding generation 
3. Vector storage
4. Semantic search and retrieval
5. Integration with text splitters
"""

import asyncio
import sys
import os
from pathlib import Path
import uuid

# Add the src directory to the path so we can import agenticflow
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))

try:
    from agenticflow.vectorstores import (
        VectorStoreFactory,
        VectorStoreType,
        VectorStoreConfig,
        VectorStoreDocument,
        DistanceMetric,
    )
    from agenticflow.embeddings import create_ollama_embedding_provider
    from agenticflow.text.splitters import (
        RecursiveSplitter,
        SentenceSplitter,
        create_splitter
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure AgenticFlow is properly installed")
    sys.exit(1)


class RAGSystem:
    """A complete RAG (Retrieval Augmented Generation) system."""
    
    def __init__(self, vector_store_type=VectorStoreType.MEMORY):
        self.vector_store_type = vector_store_type
        self.vector_store = None
        self.embedding_provider = None
        self.text_splitter = None
        
    async def initialize(self):
        """Initialize the RAG system components."""
        print("🚀 Initializing RAG System...")
        
        # Initialize embedding provider
        try:
            self.embedding_provider = create_ollama_embedding_provider(model="nomic-embed-text")
            if await self.embedding_provider.is_available():
                print("✅ Ollama embedding provider ready")
                embedding_dim = await self.embedding_provider.get_dimension()
            else:
                raise Exception("Ollama not available")
        except Exception as e:
            print(f"❌ Failed to initialize embeddings: {e}")
            return False
        
        # Initialize text splitter
        from agenticflow.text.splitters.base import SplitterConfig, SplitterType
        config = SplitterConfig(
            splitter_type=SplitterType.RECURSIVE,
            chunk_size=500,
            chunk_overlap=50,
            custom_separators=["\n\n", "\n", ". ", " ", ""]
        )
        self.text_splitter = RecursiveSplitter(config)
        print("✅ Text splitter ready")
        
        # Initialize vector store
        config = VectorStoreConfig(
            store_type=self.vector_store_type,
            collection_name="rag_knowledge_base",
            embedding_dimension=embedding_dim,
            distance_metric=DistanceMetric.COSINE
        )
        
        self.vector_store = VectorStoreFactory.create_vector_store(config)
        await self.vector_store.connect()
        print(f"✅ Vector store ready ({self.vector_store_type.value})")
        
        return True
    
    async def ingest_documents(self, documents: list[dict]):
        """
        Ingest documents into the RAG system.
        
        Args:
            documents: List of dicts with 'title', 'content', and optional 'metadata'
        """
        print(f"\n📚 Ingesting {len(documents)} documents...")
        
        all_chunks = []
        for doc_idx, doc in enumerate(documents):
            title = doc.get('title', f'Document {doc_idx}')
            content = doc['content']
            metadata = doc.get('metadata', {})
            
            print(f"📄 Processing: {title}")
            
            # Split document into chunks
            chunks = await self.text_splitter.split_text(content)
            print(f"   Split into {len(chunks)} chunks")
            
            # Create VectorStoreDocument objects
            for chunk_idx, chunk in enumerate(chunks):
                chunk_id = f"doc_{doc_idx}_chunk_{chunk_idx}"
                chunk_metadata = {
                    **metadata,
                    'title': title,
                    'chunk_index': chunk_idx,
                    'total_chunks': len(chunks),
                    'document_index': doc_idx
                }
                
                all_chunks.append({
                    'id': chunk_id,
                    'content': chunk.content,
                    'metadata': chunk_metadata
                })
        
        # Generate embeddings for all chunks
        print("🔄 Generating embeddings...")
        chunk_texts = [chunk['content'] for chunk in all_chunks]
        embeddings = await self.embedding_provider.embed_texts(chunk_texts)
        
        # Create vector store documents
        vector_docs = []
        for chunk, embedding in zip(all_chunks, embeddings):
            vector_doc = VectorStoreDocument(
                id=chunk['id'],
                content=chunk['content'],
                embedding=embedding,
                metadata=chunk['metadata']
            )
            vector_docs.append(vector_doc)
        
        # Add to vector store
        doc_ids = await self.vector_store.add_documents(vector_docs)
        print(f"✅ Added {len(doc_ids)} chunks to vector store")
        
        return doc_ids
    
    async def search(self, query: str, limit: int = 5, score_threshold: float = 0.3):
        """
        Search for relevant documents.
        
        Args:
            query: Search query
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            
        Returns:
            List of search results
        """
        print(f"\n🔍 Searching for: '{query}'")
        
        # Generate query embedding
        query_embedding = await self.embedding_provider.embed_text(query)
        
        # Search vector store
        results = await self.vector_store.search(
            query_embedding=query_embedding,
            limit=limit,
            score_threshold=score_threshold
        )
        
        print(f"📋 Found {len(results)} relevant chunks:")
        for i, result in enumerate(results):
            metadata = result.document.metadata
            title = metadata.get('title', 'Unknown')
            chunk_idx = metadata.get('chunk_index', '?')
            
            print(f"   {i+1}. [{title} - Chunk {chunk_idx}] (score: {result.score:.3f})")
            print(f"      {result.document.content[:100]}...")
        
        return results
    
    async def get_context(self, query: str, max_chunks: int = 3) -> str:
        """
        Get relevant context for a query as a formatted string.
        
        Args:
            query: Search query
            max_chunks: Maximum number of chunks to include
            
        Returns:
            Formatted context string
        """
        results = await self.search(query, limit=max_chunks, score_threshold=0.2)
        
        if not results:
            return "No relevant context found."
        
        context_parts = []
        for i, result in enumerate(results):
            metadata = result.document.metadata
            title = metadata.get('title', 'Unknown Document')
            
            context_parts.append(f"Context {i+1} (from {title}):\n{result.document.content}")
        
        return "\n\n".join(context_parts)
    
    async def answer_question(self, question: str) -> dict:
        """
        Answer a question using RAG approach.
        
        Args:
            question: The question to answer
            
        Returns:
            Dict with 'context', 'sources', and basic answer info
        """
        print(f"\n❓ Question: {question}")
        
        # Get relevant context
        results = await self.search(question, limit=5, score_threshold=0.2)
        
        if not results:
            return {
                'question': question,
                'context': "No relevant information found.",
                'sources': [],
                'answer': "I don't have enough information to answer this question."
            }
        
        # Format context
        context = await self.get_context(question, max_chunks=3)
        
        # Extract sources
        sources = []
        seen_docs = set()
        for result in results:
            title = result.document.metadata.get('title', 'Unknown')
            if title not in seen_docs:
                sources.append(title)
                seen_docs.add(title)
        
        # In a real system, you'd use an LLM here to generate the answer
        # For this demo, we'll just return the context
        answer = f"Based on the available information: {context[:200]}..."
        
        return {
            'question': question,
            'context': context,
            'sources': sources[:3],  # Top 3 sources
            'answer': answer,
            'num_chunks_used': len(results)
        }
    
    async def get_statistics(self) -> dict:
        """Get statistics about the knowledge base."""
        total_docs = await self.vector_store.count_documents()
        collections = await self.vector_store.list_collections()
        
        return {
            'total_chunks': total_docs,
            'collections': collections,
            'vector_store_type': self.vector_store_type.value,
            'embedding_dimension': self.vector_store.config.embedding_dimension
        }
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.vector_store:
            await self.vector_store.disconnect()
        if self.embedding_provider:
            await self.embedding_provider.close()


async def create_sample_documents():
    """Create sample documents for the demo."""
    return [
        {
            'title': 'Introduction to Machine Learning',
            'content': '''
Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. It focuses on developing algorithms that can access data and use it to learn for themselves.

The process of machine learning involves training models on datasets to recognize patterns and make predictions or decisions. There are three main types of machine learning: supervised learning, unsupervised learning, and reinforcement learning.

Supervised learning uses labeled datasets to train algorithms to classify data or predict outcomes accurately. Common applications include image recognition, spam detection, and medical diagnosis.

Unsupervised learning finds hidden patterns in data without labeled examples. It's used for clustering, association rules, and dimensionality reduction.

Reinforcement learning trains agents to make decisions by rewarding desired behaviors and punishing undesired ones. It's commonly used in game playing, robotics, and autonomous vehicles.
''',
            'metadata': {'category': 'AI/ML', 'difficulty': 'beginner'}
        },
        {
            'title': 'Vector Databases and Embeddings',
            'content': '''
Vector databases are specialized databases designed to store, index, and search high-dimensional vectors efficiently. They are essential for modern AI applications that rely on embeddings.

Embeddings are numerical representations of data (text, images, audio) in high-dimensional space. Similar items are placed close together in this space, enabling semantic similarity search.

Traditional databases store structured data in rows and columns, but vector databases store vectors and provide similarity search capabilities. They use approximate nearest neighbor (ANN) algorithms for fast retrieval.

Key features of vector databases include horizontal scaling, real-time updates, metadata filtering, and integration with machine learning pipelines. Popular vector databases include Pinecone, Weaviate, Qdrant, and Chroma.

Vector databases enable applications like recommendation systems, semantic search, chatbots, and retrieval-augmented generation (RAG) systems.
''',
            'metadata': {'category': 'Database', 'difficulty': 'intermediate'}
        },
        {
            'title': 'Natural Language Processing Basics',
            'content': '''
Natural Language Processing (NLP) is a branch of artificial intelligence that helps computers understand, interpret, and manipulate human language. It combines computational linguistics with statistical machine learning and deep learning models.

Key NLP tasks include tokenization, part-of-speech tagging, named entity recognition, sentiment analysis, and text classification. Modern NLP relies heavily on transformer models like BERT, GPT, and T5.

Text preprocessing is crucial in NLP and involves cleaning, tokenization, stop word removal, and normalization. Feature extraction techniques include bag-of-words, TF-IDF, and word embeddings.

Word embeddings like Word2Vec, GloVe, and contextual embeddings from transformers represent words as dense vectors that capture semantic relationships. These embeddings enable machines to understand context and meaning.

Applications of NLP include chatbots, machine translation, text summarization, question answering systems, and content generation.
''',
            'metadata': {'category': 'AI/ML', 'difficulty': 'intermediate'}
        },
        {
            'title': 'Retrieval Augmented Generation (RAG)',
            'content': '''
Retrieval Augmented Generation (RAG) is a technique that combines the power of pre-trained language models with external knowledge retrieval. It addresses the limitation of language models having static knowledge cutoffs.

RAG systems work by first retrieving relevant information from a knowledge base or document collection, then using this information to augment the generation process. This approach provides more accurate, up-to-date, and factual responses.

The typical RAG pipeline consists of: document ingestion and chunking, embedding generation, vector storage, query processing, retrieval, and generation. Each component is crucial for the system's effectiveness.

Benefits of RAG include reduced hallucinations, access to current information, domain-specific knowledge integration, and cost-effectiveness compared to training large models from scratch.

RAG systems are widely used in customer support, question-answering systems, research assistants, and knowledge management platforms. They represent a practical approach to building AI applications that require both reasoning and factual accuracy.
''',
            'metadata': {'category': 'AI/ML', 'difficulty': 'advanced'}
        }
    ]


async def demo_basic_rag():
    """Demonstrate basic RAG functionality."""
    print("🎯 Basic RAG Demo")
    print("=" * 50)
    
    # Initialize RAG system
    rag = RAGSystem(vector_store_type=VectorStoreType.MEMORY)
    
    if not await rag.initialize():
        return
    
    try:
        # Create and ingest sample documents
        documents = await create_sample_documents()
        await rag.ingest_documents(documents)
        
        # Show statistics
        stats = await rag.get_statistics()
        print(f"\n📊 Knowledge Base Statistics:")
        print(f"   Total chunks: {stats['total_chunks']}")
        print(f"   Vector store: {stats['vector_store_type']}")
        print(f"   Embedding dimension: {stats['embedding_dimension']}")
        
        # Test queries
        queries = [
            "What is machine learning?",
            "How do vector databases work?",
            "What are the benefits of RAG?",
            "Tell me about NLP preprocessing",
        ]
        
        for query in queries:
            result = await rag.answer_question(query)
            
            print(f"\n" + "="*60)
            print(f"Question: {result['question']}")
            print(f"Sources: {', '.join(result['sources'])}")
            print(f"Chunks used: {result['num_chunks_used']}")
            print("\nContext:")
            print(result['context'][:500] + "..." if len(result['context']) > 500 else result['context'])
    
    finally:
        await rag.cleanup()


async def demo_faiss_rag():
    """Demonstrate RAG with FAISS persistence."""
    print("\n🎯 RAG with FAISS Persistence Demo")
    print("=" * 50)
    
    try:
        import faiss
    except ImportError:
        print("⚠️ FAISS not available, skipping persistence demo")
        return
    
    # Use FAISS with persistence
    rag = RAGSystem(vector_store_type=VectorStoreType.FAISS)
    
    # Configure persistence path
    persist_path = Path("/tmp/rag_demo.faiss")
    rag.vector_store_config = VectorStoreConfig(
        store_type=VectorStoreType.FAISS,
        collection_name="rag_knowledge_base",
        persist_path=str(persist_path),
        embedding_dimension=768,
        distance_metric=DistanceMetric.COSINE
    )
    
    if not await rag.initialize():
        return
    
    try:
        # Check if we have existing data
        existing_count = await rag.vector_store.count_documents()
        
        if existing_count == 0:
            print("📚 No existing data found, ingesting documents...")
            documents = await create_sample_documents()
            await rag.ingest_documents(documents)
        else:
            print(f"📚 Found {existing_count} existing chunks in persistent store")
        
        # Test search
        results = await rag.search("What is supervised learning?", limit=3)
        
        print(f"\n🔍 Search Results:")
        for i, result in enumerate(results):
            print(f"{i+1}. Score: {result.score:.3f}")
            print(f"   Content: {result.document.content[:150]}...")
    
    finally:
        await rag.cleanup()
        print(f"💾 Data persisted to: {persist_path}")


async def demo_advanced_filtering():
    """Demonstrate advanced filtering and metadata usage."""
    print("\n🎯 Advanced Filtering Demo")
    print("=" * 50)
    
    rag = RAGSystem(vector_store_type=VectorStoreType.MEMORY)
    
    if not await rag.initialize():
        return
    
    try:
        documents = await create_sample_documents()
        await rag.ingest_documents(documents)
        
        # Search with metadata filtering
        query_embedding = await rag.embedding_provider.embed_text("machine learning algorithms")
        
        # Filter by category
        ai_ml_results = await rag.vector_store.search(
            query_embedding=query_embedding,
            limit=5,
            metadata_filter={'category': 'AI/ML'}
        )
        
        print(f"🔍 AI/ML Category Results: {len(ai_ml_results)}")
        for result in ai_ml_results:
            title = result.document.metadata.get('title', 'Unknown')
            difficulty = result.document.metadata.get('difficulty', 'Unknown')
            print(f"   • {title} ({difficulty}) - Score: {result.score:.3f}")
        
        # Filter by difficulty
        beginner_results = await rag.vector_store.search(
            query_embedding=query_embedding,
            limit=5,
            metadata_filter={'difficulty': 'beginner'}
        )
        
        print(f"\n🔍 Beginner Level Results: {len(beginner_results)}")
        for result in beginner_results:
            title = result.document.metadata.get('title', 'Unknown')
            print(f"   • {title} - Score: {result.score:.3f}")
    
    finally:
        await rag.cleanup()


async def main():
    """Run all RAG demos."""
    print("🚀 AgenticFlow RAG (Retrieval Augmented Generation) Demo")
    print("="*60)
    
    try:
        await demo_basic_rag()
        await demo_faiss_rag()
        await demo_advanced_filtering()
        
        print("\n" + "="*60)
        print("✅ All RAG demos completed successfully!")
        print("\n💡 Key Takeaways:")
        print("• RAG combines retrieval and generation for better AI responses")
        print("• Vector stores enable semantic search over document collections") 
        print("• Text chunking and embeddings are crucial for good retrieval")
        print("• Metadata filtering enables precise document targeting")
        print("• Persistence allows knowledge bases to survive restarts")
        
    except KeyboardInterrupt:
        print("\n❌ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())