"""
LangChain Vector Store Adapter
============================
Seamless integration with any LangChain VectorStore implementation.
"""

from typing import Any, Dict, List, Optional
import uuid
import structlog

from langchain_core.vectorstores import VectorStore as LangChainVectorStore
from langchain_core.documents import Document as LangChainDocument
from langchain_core.embeddings import Embeddings

from .base import (
    AsyncVectorStore,
    VectorStoreConfig,
    VectorStoreDocument,
    SearchResult,
    VectorStoreError,
    VectorStoreConnectionError
)

logger = structlog.get_logger(__name__)


class LangChainVectorStoreAdapter(AsyncVectorStore):
    """
    Adapter to use any LangChain VectorStore with our unified interface.
    
    Supports all LangChain vector stores including:
    - Chroma
    - FAISS
    - Pinecone
    - Qdrant
    - Weaviate
    - And many more!
    """
    
    def __init__(
        self, 
        config: VectorStoreConfig,
        langchain_vectorstore: LangChainVectorStore,
        embeddings: Optional[Embeddings] = None
    ):
        super().__init__(config)
        self.langchain_store = langchain_vectorstore
        self.embeddings = embeddings
        self.connected = False
    
    async def connect(self) -> None:
        """Connect to the LangChain vector store."""
        try:
            # Most LangChain vector stores don't need explicit connection
            self.connected = True
            self.logger.info(f"Connected to LangChain vector store: {type(self.langchain_store).__name__}")
        except Exception as e:
            raise VectorStoreConnectionError(f"Failed to connect to LangChain vector store: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from the LangChain vector store."""
        # Most LangChain stores don't need explicit disconnection
        self.connected = False
        self.logger.info("Disconnected from LangChain vector store")
    
    async def create_collection(
        self, 
        collection_name: Optional[str] = None,
        dimension: Optional[int] = None,
        distance_metric: Optional[str] = None
    ) -> None:
        """Create collection (if supported by the underlying store)."""
        # Many LangChain vector stores auto-create collections
        # This is mainly for compatibility
        collection = collection_name or self.config.collection_name
        self.logger.debug(f"Collection handling delegated to LangChain store: {collection}")
    
    async def delete_collection(self, collection_name: Optional[str] = None) -> None:
        """Delete collection (if supported by the underlying store)."""
        collection = collection_name or self.config.collection_name
        
        # Try to delete if the store supports it
        if hasattr(self.langchain_store, 'delete_collection'):
            try:
                await self.langchain_store.delete_collection(collection)
                self.logger.debug(f"Deleted collection: {collection}")
            except Exception as e:
                self.logger.warning(f"Failed to delete collection {collection}: {e}")
        else:
            self.logger.warning("Underlying LangChain store doesn't support collection deletion")
    
    async def add_documents(
        self, 
        documents: List[VectorStoreDocument],
        collection_name: Optional[str] = None
    ) -> List[str]:
        """Add documents to the LangChain vector store."""
        if not self.connected:
            await self.connect()
        
        if not documents:
            return []
        
        # Convert our documents to LangChain format
        langchain_docs = []
        texts = []
        metadatas = []
        ids = []
        
        for doc in documents:
            # Create LangChain document
            langchain_doc = LangChainDocument(
                page_content=doc.content,
                metadata=doc.metadata
            )
            langchain_docs.append(langchain_doc)
            
            # Prepare for batch operations
            texts.append(doc.content)
            metadatas.append(doc.metadata)
            ids.append(doc.id)
        
        try:
            # Use embeddings if available, otherwise let the store handle it
            if hasattr(self.langchain_store, 'add_documents'):
                # Preferred method - use documents directly
                added_ids = await self.langchain_store.aadd_documents(langchain_docs, ids=ids)
            elif hasattr(self.langchain_store, 'add_texts'):
                # Fallback - use texts
                if self.embeddings:
                    embeddings_list = [doc.embedding for doc in documents if doc.embedding]
                    if len(embeddings_list) == len(texts):
                        added_ids = await self.langchain_store.aadd_texts(
                            texts=texts, 
                            metadatas=metadatas, 
                            ids=ids,
                            embeddings=embeddings_list
                        )
                    else:
                        added_ids = await self.langchain_store.aadd_texts(
                            texts=texts, 
                            metadatas=metadatas, 
                            ids=ids
                        )
                else:
                    added_ids = await self.langchain_store.aadd_texts(
                        texts=texts, 
                        metadatas=metadatas, 
                        ids=ids
                    )
            else:
                raise VectorStoreError("LangChain store doesn't support adding documents")
            
            # Ensure we return the original IDs if the store doesn't return them
            if not added_ids:
                added_ids = ids
            
            self.logger.debug(f"Added {len(documents)} documents to LangChain vector store")
            return added_ids
        
        except Exception as e:
            raise VectorStoreError(f"Failed to add documents to LangChain store: {e}")
    
    async def update_documents(
        self, 
        documents: List[VectorStoreDocument],
        collection_name: Optional[str] = None
    ) -> None:
        """Update documents (delete and re-add)."""
        if not documents:
            return
        
        # Most LangChain stores don't have native update - delete and re-add
        doc_ids = [doc.id for doc in documents]
        
        try:
            await self.delete_documents(doc_ids, collection_name)
            await self.add_documents(documents, collection_name)
            self.logger.debug(f"Updated {len(documents)} documents in LangChain store")
        except Exception as e:
            raise VectorStoreError(f"Failed to update documents in LangChain store: {e}")
    
    async def delete_documents(
        self, 
        document_ids: List[str],
        collection_name: Optional[str] = None
    ) -> None:
        """Delete documents by ID."""
        if not document_ids:
            return
        
        try:
            if hasattr(self.langchain_store, 'delete'):
                # Preferred method
                await self.langchain_store.adelete(ids=document_ids)
            elif hasattr(self.langchain_store, 'delete_by_ids'):
                # Alternative method
                await self.langchain_store.adelete_by_ids(document_ids)
            else:
                self.logger.warning("LangChain store doesn't support document deletion")
                return
            
            self.logger.debug(f"Deleted {len(document_ids)} documents from LangChain store")
        
        except Exception as e:
            raise VectorStoreError(f"Failed to delete documents from LangChain store: {e}")
    
    async def search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None
    ) -> List[SearchResult]:
        """Search for similar documents."""
        if not self.connected:
            await self.connect()
        
        try:
            # LangChain typically uses text queries, but we can work with embeddings
            results = []
            
            if hasattr(self.langchain_store, 'similarity_search_by_vector'):
                # Direct vector search (preferred)
                docs = await self.langchain_store.asimilarity_search_by_vector(
                    embedding=query_embedding,
                    k=limit,
                    filter=metadata_filter
                )
                
                # Convert to our format
                for i, doc in enumerate(docs):
                    # Try to get similarity score if available
                    score = 1.0  # Default score
                    doc_id = doc.metadata.get('id', str(uuid.uuid4()))
                    
                    vector_doc = VectorStoreDocument(
                        id=doc_id,
                        content=doc.page_content,
                        embedding=query_embedding,  # Use query embedding as placeholder
                        metadata=doc.metadata
                    )
                    
                    result = SearchResult(
                        document=vector_doc,
                        score=score,
                        rank=i + 1
                    )
                    results.append(result)
            
            elif hasattr(self.langchain_store, 'similarity_search_with_score_by_vector'):
                # Vector search with scores
                docs_with_scores = await self.langchain_store.asimilarity_search_with_score_by_vector(
                    embedding=query_embedding,
                    k=limit,
                    filter=metadata_filter
                )
                
                for i, (doc, score) in enumerate(docs_with_scores):
                    # Apply score threshold
                    if score_threshold and score < score_threshold:
                        continue
                    
                    doc_id = doc.metadata.get('id', str(uuid.uuid4()))
                    
                    vector_doc = VectorStoreDocument(
                        id=doc_id,
                        content=doc.page_content,
                        embedding=query_embedding,
                        metadata=doc.metadata
                    )
                    
                    result = SearchResult(
                        document=vector_doc,
                        score=score,
                        rank=i + 1
                    )
                    results.append(result)
            
            else:
                # Fallback: convert embedding to a simple text query (not ideal)
                self.logger.warning("LangChain store doesn't support vector search, skipping search")
                return []
            
            self.logger.debug(f"Found {len(results)} results in LangChain store")
            return results
        
        except Exception as e:
            self.logger.error(f"Search failed in LangChain store: {e}")
            return []
    
    async def get_document(
        self, 
        document_id: str,
        collection_name: Optional[str] = None
    ) -> Optional[VectorStoreDocument]:
        """Get document by ID (if supported)."""
        try:
            # Most LangChain stores don't have direct get_by_id
            # We can try searching by metadata
            results = await self.search(
                query_embedding=[0.0] * (self.config.embedding_dimension or 1536),
                limit=1,
                metadata_filter={"id": document_id}
            )
            
            if results:
                return results[0].document
            return None
        
        except Exception as e:
            self.logger.error(f"Failed to get document {document_id}: {e}")
            return None
    
    async def count_documents(self, collection_name: Optional[str] = None) -> int:
        """Count documents (estimated if exact count not available)."""
        try:
            # Try different methods to get count
            if hasattr(self.langchain_store, 'count'):
                return await self.langchain_store.acount()
            elif hasattr(self.langchain_store, '__len__'):
                return len(self.langchain_store)
            else:
                # Fallback: return 0 or estimate
                self.logger.warning("LangChain store doesn't support document counting")
                return 0
        
        except Exception as e:
            self.logger.error(f"Failed to count documents: {e}")
            return 0
    
    async def list_collections(self) -> List[str]:
        """List collections (if supported)."""
        try:
            if hasattr(self.langchain_store, 'list_collections'):
                return await self.langchain_store.alist_collections()
            else:
                # Return default collection
                return [self.config.collection_name]
        
        except Exception as e:
            self.logger.error(f"Failed to list collections: {e}")
            return [self.config.collection_name]


# Convenience functions for common LangChain integrations

def create_langchain_adapter(
    langchain_vectorstore: LangChainVectorStore,
    collection_name: str = "default",
    embeddings: Optional[Embeddings] = None
) -> LangChainVectorStoreAdapter:
    """
    Create a LangChain vector store adapter.
    
    Args:
        langchain_vectorstore: Any LangChain VectorStore instance
        collection_name: Collection name for our interface
        embeddings: Optional embeddings model
    
    Returns:
        LangChainVectorStoreAdapter instance
    """
    from .base import VectorStoreType, VectorStoreConfig
    
    config = VectorStoreConfig(
        store_type=VectorStoreType.MEMORY,  # Placeholder type
        collection_name=collection_name,
        embedding_dimension=None  # Will be determined by embeddings
    )
    
    return LangChainVectorStoreAdapter(config, langchain_vectorstore, embeddings)


# Integration examples for popular LangChain vector stores

def create_chroma_adapter(
    persist_directory: Optional[str] = None,
    collection_name: str = "default",
    embeddings: Optional[Embeddings] = None
) -> LangChainVectorStoreAdapter:
    """Create adapter for LangChain Chroma vector store."""
    try:
        from langchain_chroma import Chroma
        
        chroma_store = Chroma(
            collection_name=collection_name,
            persist_directory=persist_directory,
            embedding_function=embeddings
        )
        
        return create_langchain_adapter(chroma_store, collection_name, embeddings)
    
    except ImportError:
        raise VectorStoreError("langchain-chroma not installed. Install with: pip install langchain-chroma")


def create_faiss_adapter(
    embeddings: Embeddings,
    index_path: Optional[str] = None,
    collection_name: str = "default"
) -> LangChainVectorStoreAdapter:
    """Create adapter for LangChain FAISS vector store."""
    try:
        from langchain_community.vectorstores import FAISS
        
        if index_path:
            # Load existing index
            faiss_store = FAISS.load_local(index_path, embeddings)
        else:
            # Create new index with dummy data (will be replaced)
            faiss_store = FAISS.from_texts(
                texts=["dummy"], 
                embedding=embeddings,
                metadatas=[{"dummy": True}]
            )
        
        return create_langchain_adapter(faiss_store, collection_name, embeddings)
    
    except ImportError:
        raise VectorStoreError("Required dependencies not installed. Install with: pip install langchain-community faiss-cpu")


def create_pinecone_adapter(
    index_name: str,
    embeddings: Embeddings,
    api_key: Optional[str] = None,
    environment: Optional[str] = None,
    collection_name: str = "default"
) -> LangChainVectorStoreAdapter:
    """Create adapter for LangChain Pinecone vector store."""
    try:
        from langchain_pinecone import PineconeVectorStore
        
        pinecone_store = PineconeVectorStore(
            index=index_name,
            embedding=embeddings,
            api_key=api_key,
            environment=environment
        )
        
        return create_langchain_adapter(pinecone_store, collection_name, embeddings)
    
    except ImportError:
        raise VectorStoreError("langchain-pinecone not installed. Install with: pip install langchain-pinecone")