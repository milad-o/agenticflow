#!/usr/bin/env python3
"""
Vector Stores Test Script
========================

This script tests the AgenticFlow vector store implementations including:
1. EphemeralVectorStore (in-memory)
2. FAISSVectorStore (if FAISS is available)
3. ChromaVectorStore (if Chroma is available)
4. Integration with embeddings
"""

import asyncio
import sys
import os
import tempfile
import uuid
from pathlib import Path

# Add the src directory to the path so we can import agenticflow
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))

try:
    from agenticflow.vectorstores import (
        VectorStoreFactory,
        VectorStoreType,
        VectorStoreConfig,
        VectorStoreDocument,
        DistanceMetric,
        EphemeralVectorStore,
        FAISSVectorStore,
        ChromaVectorStore,
    )
    from agenticflow.embeddings import create_ollama_embedding_provider
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure AgenticFlow is properly installed")
    sys.exit(1)


class VectorStoreTestSuite:
    """Test suite for vector store implementations."""
    
    def __init__(self):
        self.temp_dir = None
        self.embedding_provider = None
        
    async def setup(self):
        """Set up test environment."""
        print("🔧 Setting up test environment...")
        
        # Create temp directory for persistence tests
        self.temp_dir = Path(tempfile.mkdtemp(prefix="agenticflow_vector_test_"))
        print(f"📁 Temp directory: {self.temp_dir}")
        
        # Set up embedding provider (use Ollama if available)
        try:
            self.embedding_provider = create_ollama_embedding_provider(model="nomic-embed-text")
            if await self.embedding_provider.is_available():
                print("✅ Ollama embedding provider ready")
            else:
                print("⚠️ Ollama not available, will use mock embeddings")
                self.embedding_provider = None
        except Exception as e:
            print(f"⚠️ Failed to setup Ollama: {e}")
            self.embedding_provider = None
    
    async def teardown(self):
        """Clean up test environment."""
        print("🧹 Cleaning up...")
        
        if self.embedding_provider:
            await self.embedding_provider.close()
        
        # Clean up temp directory
        if self.temp_dir and self.temp_dir.exists():
            import shutil
            shutil.rmtree(self.temp_dir)
    
    async def get_test_embeddings(self, texts):
        """Generate embeddings for test texts."""
        if self.embedding_provider:
            embeddings = await self.embedding_provider.embed_texts(texts)
            return embeddings
        else:
            # Mock embeddings for testing
            import random
            dimension = 768
            embeddings = []
            for _ in texts:
                embedding = [random.random() for _ in range(dimension)]
                # Normalize
                magnitude = sum(x * x for x in embedding) ** 0.5
                embedding = [x / magnitude for x in embedding]
                embeddings.append(embedding)
            return embeddings
    
    async def create_test_documents(self, count=10):
        """Create test documents with embeddings."""
        texts = [
            "Artificial intelligence is transforming the world.",
            "Machine learning algorithms can identify complex patterns.",
            "Natural language processing enables computers to understand text.",
            "Deep learning models require large amounts of training data.",
            "Python is a popular programming language for data science.",
            "Vector databases store high-dimensional embeddings efficiently.",
            "Semantic search uses embeddings to find relevant content.",
            "Retrieval-augmented generation combines search with language models.",
            "Transformer models have revolutionized natural language understanding.",
            "Vector similarity search is fundamental to many AI applications."
        ]
        
        # Take only the requested count
        texts = texts[:count]
        embeddings = await self.get_test_embeddings(texts)
        
        documents = []
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            doc = VectorStoreDocument(
                id=f"doc_{i}",
                content=text,
                embedding=embedding,
                metadata={
                    "category": "ai" if i < 5 else "tech",
                    "length": len(text),
                    "index": i
                }
            )
            documents.append(doc)
        
        return documents
    
    async def test_ephemeral_vector_store(self):
        """Test the in-memory ephemeral vector store."""
        print("\n🧪 Testing EphemeralVectorStore...")
        
        # Create configuration
        config = VectorStoreConfig(
            store_type=VectorStoreType.MEMORY,
            collection_name="test_ephemeral",
            embedding_dimension=768,
            distance_metric=DistanceMetric.COSINE
        )
        
        # Create vector store
        store = EphemeralVectorStore(config)
        
        try:
            # Test connection
            await store.connect()
            print("✓ Connected to ephemeral vector store")
            
            # Test collection creation
            await store.create_collection("test_collection", dimension=768)
            print("✓ Created collection")
            
            # Create test documents
            documents = await self.create_test_documents(5)
            print(f"✓ Created {len(documents)} test documents")
            
            # Test adding documents
            doc_ids = await store.add_documents(documents, "test_collection")
            print(f"✓ Added documents: {doc_ids}")
            
            # Test counting documents
            count = await store.count_documents("test_collection")
            print(f"✓ Document count: {count}")
            
            # Test retrieving a document
            doc = await store.get_document("doc_0", "test_collection")
            if doc:
                print(f"✓ Retrieved document: {doc.id}")
            
            # Test search
            query_text = "artificial intelligence and machine learning"
            query_embedding = (await self.get_test_embeddings([query_text]))[0]
            
            results = await store.search(
                query_embedding=query_embedding,
                limit=3,
                collection_name="test_collection"
            )
            
            print(f"✓ Search found {len(results)} results")
            for i, result in enumerate(results):
                print(f"   {i+1}. {result.document.content[:50]}... (score: {result.score:.3f})")
            
            # Test metadata filtering
            filtered_results = await store.search(
                query_embedding=query_embedding,
                limit=3,
                metadata_filter={"category": "ai"},
                collection_name="test_collection"
            )
            print(f"✓ Filtered search found {len(filtered_results)} results")
            
            # Test document update
            updated_doc = VectorStoreDocument(
                id="doc_0",
                content="Updated: AI is transforming everything",
                embedding=documents[0].embedding,  # Keep same embedding
                metadata={"category": "ai", "updated": True}
            )
            await store.update_documents([updated_doc], "test_collection")
            print("✓ Updated document")
            
            # Test document deletion
            await store.delete_documents(["doc_4"], "test_collection")
            final_count = await store.count_documents("test_collection")
            print(f"✓ After deletion, document count: {final_count}")
            
            # Test health check
            is_healthy = await store.health_check()
            print(f"✓ Health check: {'passed' if is_healthy else 'failed'}")
            
            # Test collection info
            info = await store.get_collection_info("test_collection")
            print(f"✓ Collection info: {info}")
            
        except Exception as e:
            print(f"❌ Ephemeral vector store test failed: {e}")
        finally:
            await store.disconnect()
            print("✓ Disconnected from ephemeral vector store")
    
    async def test_faiss_vector_store(self):
        """Test FAISS vector store if available."""
        print("\n🧪 Testing FAISSVectorStore...")
        
        try:
            # Check if FAISS is available
            import faiss
        except ImportError:
            print("⚠️ FAISS not available, skipping test")
            print("💡 Install with: pip install faiss-cpu")
            return
        
        # Create configuration with persistence
        persist_path = self.temp_dir / "test_faiss.index"
        config = VectorStoreConfig(
            store_type=VectorStoreType.FAISS,
            collection_name="test_faiss",
            embedding_dimension=768,
            persist_path=str(persist_path),
            distance_metric=DistanceMetric.COSINE
        )
        
        try:
            store = FAISSVectorStore(config)
            
            # Test connection
            await store.connect()
            print("✓ Connected to FAISS vector store")
            
            # Create test documents
            documents = await self.create_test_documents(8)
            print(f"✓ Created {len(documents)} test documents")
            
            # Test adding documents
            doc_ids = await store.add_documents(documents)
            print(f"✓ Added documents: {len(doc_ids)}")
            
            # Test search
            query_text = "machine learning and data science"
            query_embedding = (await self.get_test_embeddings([query_text]))[0]
            
            results = await store.search(
                query_embedding=query_embedding,
                limit=3
            )
            
            print(f"✓ Search found {len(results)} results")
            for i, result in enumerate(results):
                print(f"   {i+1}. {result.document.content[:50]}... (score: {result.score:.3f})")
            
            # Test persistence by disconnecting and reconnecting
            await store.disconnect()
            print("✓ Disconnected and saved to disk")
            
            # Create new store instance and load
            store2 = FAISSVectorStore(config)
            await store2.connect()
            print("✓ Reconnected and loaded from disk")
            
            # Verify data persisted
            count = await store2.count_documents()
            print(f"✓ Document count after reload: {count}")
            
            # Test search on reloaded store
            results2 = await store2.search(
                query_embedding=query_embedding,
                limit=2
            )
            print(f"✓ Search on reloaded store found {len(results2)} results")
            
            await store2.disconnect()
            
        except Exception as e:
            print(f"❌ FAISS vector store test failed: {e}")
            import traceback
            traceback.print_exc()
    
    async def test_chroma_vector_store(self):
        """Test Chroma vector store if available."""
        print("\n🧪 Testing ChromaVectorStore...")
        
        try:
            import chromadb
        except ImportError:
            print("⚠️ ChromaDB not available, skipping test")
            print("💡 Install with: pip install chromadb")
            return
        
        # Create configuration
        persist_path = self.temp_dir / "chroma_db"
        config = VectorStoreConfig(
            store_type=VectorStoreType.CHROMA,
            collection_name="test_chroma",
            embedding_dimension=768,
            persist_path=str(persist_path),
            distance_metric=DistanceMetric.COSINE
        )
        
        try:
            store = ChromaVectorStore(config)
            
            # Test connection
            await store.connect()
            print("✓ Connected to Chroma vector store")
            
            # Test collection creation
            await store.create_collection(
                collection_name="test_collection",
                dimension=768
            )
            print("✓ Created collection")
            
            # Create test documents
            documents = await self.create_test_documents(6)
            print(f"✓ Created {len(documents)} test documents")
            
            # Test adding documents
            doc_ids = await store.add_documents(documents, "test_collection")
            print(f"✓ Added documents: {len(doc_ids)}")
            
            # Test search
            query_text = "vector databases and semantic search"
            query_embedding = (await self.get_test_embeddings([query_text]))[0]
            
            results = await store.search(
                query_embedding=query_embedding,
                limit=3,
                collection_name="test_collection"
            )
            
            print(f"✓ Search found {len(results)} results")
            for i, result in enumerate(results):
                print(f"   {i+1}. {result.document.content[:50]}... (score: {result.score:.3f})")
            
            # Test metadata filtering
            filtered_results = await store.search(
                query_embedding=query_embedding,
                limit=2,
                metadata_filter={"category": "tech"},
                collection_name="test_collection"
            )
            print(f"✓ Filtered search found {len(filtered_results)} results")
            
            # Test listing collections
            collections = await store.list_collections()
            print(f"✓ Available collections: {collections}")
            
            await store.disconnect()
            print("✓ Disconnected from Chroma vector store")
            
        except Exception as e:
            print(f"❌ Chroma vector store test failed: {e}")
            import traceback
            traceback.print_exc()
    
    async def test_vector_store_factory(self):
        """Test the vector store factory."""
        print("\n🧪 Testing VectorStoreFactory...")
        
        try:
            # Test supported stores
            supported = VectorStoreFactory.get_supported_stores()
            print(f"✓ Supported stores: {[s.value for s in supported]}")
            
            # Test store descriptions
            for store_type in [VectorStoreType.MEMORY, VectorStoreType.FAISS, VectorStoreType.CHROMA]:
                desc = VectorStoreFactory.get_store_description(store_type)
                print(f"✓ {store_type.value}: {desc}")
            
            # Test auto-selection
            requirements = {
                "persistence": False,
                "expected_documents": 1000,
                "deployment": "local",
                "budget": "free"
            }
            
            selected_type = VectorStoreFactory.auto_select_store(requirements)
            print(f"✓ Auto-selected store for requirements: {selected_type.value}")
            
            # Test creating ephemeral config
            ephemeral_config = VectorStoreFactory.create_ephemeral_config(
                collection_name="factory_test",
                embedding_dimension=768
            )
            print(f"✓ Created ephemeral config: {ephemeral_config.collection_name}")
            
            # Test creating store from factory
            store = VectorStoreFactory.create_vector_store(ephemeral_config)
            print(f"✓ Factory created store type: {type(store).__name__}")
            
            # Test factory fallback behavior
            try:
                # Try to create a store that might not be available
                unavailable_config = VectorStoreConfig(
                    store_type=VectorStoreType.PINECONE,
                    collection_name="test",
                    api_key="fake_key"
                )
                fallback_store = VectorStoreFactory.create_vector_store(unavailable_config)
                print(f"✓ Factory fallback created: {type(fallback_store).__name__}")
            except Exception as e:
                print(f"⚠️ Factory fallback test: {e}")
            
        except Exception as e:
            print(f"❌ Factory test failed: {e}")
    
    async def test_distance_metrics(self):
        """Test different distance metrics."""
        print("\n🧪 Testing Distance Metrics...")
        
        try:
            # Create test vectors
            vec1 = [1.0, 0.0, 0.0]
            vec2 = [0.0, 1.0, 0.0]
            vec3 = [1.0, 1.0, 0.0]
            
            for metric in [DistanceMetric.COSINE, DistanceMetric.EUCLIDEAN, DistanceMetric.DOT_PRODUCT]:
                config = VectorStoreConfig(
                    store_type=VectorStoreType.MEMORY,
                    collection_name=f"test_{metric.value}",
                    embedding_dimension=3,
                    distance_metric=metric
                )
                
                store = EphemeralVectorStore(config)
                await store.connect()
                
                # Add test documents
                docs = [
                    VectorStoreDocument(id="1", content="Document 1", embedding=vec1),
                    VectorStoreDocument(id="2", content="Document 2", embedding=vec2),
                    VectorStoreDocument(id="3", content="Document 3", embedding=vec3),
                ]
                
                await store.add_documents(docs)
                
                # Search with vec1 as query
                results = await store.search(vec1, limit=3)
                
                print(f"✓ {metric.value} metric results:")
                for i, result in enumerate(results):
                    print(f"   {i+1}. Doc {result.document.id} (score: {result.score:.3f})")
                
                await store.disconnect()
                
        except Exception as e:
            print(f"❌ Distance metrics test failed: {e}")
    
    async def test_integration_with_embeddings(self):
        """Test vector store integration with embeddings."""
        print("\n🧪 Testing Integration with Embeddings...")
        
        if not self.embedding_provider:
            print("⚠️ No embedding provider available, skipping integration test")
            return
        
        try:
            # Create vector store
            config = VectorStoreConfig(
                store_type=VectorStoreType.MEMORY,
                collection_name="integration_test",
                embedding_dimension=768,
                distance_metric=DistanceMetric.COSINE
            )
            
            store = EphemeralVectorStore(config)
            await store.connect()
            
            # Create documents with real embeddings
            texts = [
                "The future of artificial intelligence looks promising.",
                "Quantum computing will revolutionize computational science.",
                "Renewable energy is crucial for environmental sustainability.",
                "Blockchain technology enables decentralized systems."
            ]
            
            # Generate embeddings
            embeddings = await self.embedding_provider.embed_texts(texts)
            
            # Create documents
            documents = []
            for i, (text, embedding) in enumerate(zip(texts, embeddings)):
                doc = VectorStoreDocument(
                    id=f"real_doc_{i}",
                    content=text,
                    embedding=embedding,
                    metadata={"topic": ["ai", "quantum", "energy", "blockchain"][i]}
                )
                documents.append(doc)
            
            await store.add_documents(documents)
            print(f"✓ Added {len(documents)} documents with real embeddings")
            
            # Test semantic search
            query = "machine learning and AI research"
            query_embedding = await self.embedding_provider.embed_text(query)
            
            results = await store.search(
                query_embedding=query_embedding,
                limit=3
            )
            
            print(f"✓ Semantic search for '{query}':")
            for i, result in enumerate(results):
                print(f"   {i+1}. {result.document.content} (score: {result.score:.3f})")
            
            # Test that AI-related content ranks higher
            if results and "artificial intelligence" in results[0].document.content.lower():
                print("✓ Semantic search correctly prioritized AI-related content")
            
            await store.disconnect()
            
        except Exception as e:
            print(f"❌ Integration test failed: {e}")
    
    async def run_all_tests(self):
        """Run all vector store tests."""
        print("🚀 Starting Vector Store Test Suite")
        print("=" * 60)
        
        try:
            await self.setup()
            
            await self.test_ephemeral_vector_store()
            await self.test_faiss_vector_store()
            await self.test_chroma_vector_store()
            await self.test_vector_store_factory()
            await self.test_distance_metrics()
            await self.test_integration_with_embeddings()
            
            print("\n" + "=" * 60)
            print("✅ All vector store tests completed!")
            
        except KeyboardInterrupt:
            print("\n❌ Tests interrupted by user")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.teardown()


async def main():
    """Main function to run vector store tests."""
    test_suite = VectorStoreTestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())