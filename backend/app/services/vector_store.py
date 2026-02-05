"""
Vector store service for managing document embeddings
Supports multiple backends: Pinecone, Weaviate, ChromaDB
"""

import logging
from typing import List, Dict, Optional
import json

from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Abstract base class for vector stores"""
    
    def __init__(self, embedding_dimension: Optional[int] = None):
        """
        Initialize vector store
        
        Args:
            embedding_dimension: Expected embedding dimension. If None, will be inferred from EmbeddingService.
        """
        self.store_type = settings.VECTOR_DB_TYPE.lower()
        self._client = None
        self.embedding_dimension = embedding_dimension
        self._initialize()
    
    def _get_embedding_dimension(self) -> int:
        """Get embedding dimension from EmbeddingService if not provided"""
        if self.embedding_dimension is not None:
            return self.embedding_dimension
        
        # Import here to avoid circular dependency
        try:
            from app.services.embedding_service import EmbeddingService
            embedding_service = EmbeddingService()
            self.embedding_dimension = embedding_service.embedding_dimension
            return self.embedding_dimension
        except Exception as e:
            logger.error(f"Failed to get embedding dimension: {e}", exc_info=True)
            # Default to 384 (sentence-transformers) if we can't determine
            logger.warning("Using default embedding dimension 384 (sentence-transformers)")
            self.embedding_dimension = 384
            return self.embedding_dimension
    
    def _initialize(self):
        """Initialize the vector store client"""
        if self.store_type == "chroma":
            self._init_chroma()
        elif self.store_type == "pinecone":
            self._init_pinecone()
        elif self.store_type == "weaviate":
            self._init_weaviate()
        else:
            raise ValueError(f"Unsupported vector store type: {self.store_type}")
    
    def _init_chroma(self):
        """Initialize ChromaDB"""
        try:
            import chromadb
            import os
            
            # Use PersistentClient for the new ChromaDB API
            persist_directory = "./vector_db"
            os.makedirs(persist_directory, exist_ok=True)
            
            self._client = chromadb.PersistentClient(path=persist_directory)
            
            # Get expected embedding dimension
            expected_dimension = self._get_embedding_dimension()
            
            # Check if collection exists and verify dimension
            collection_name = "legal_documents"
            try:
                existing_collection = self._client.get_collection(name=collection_name)
                
                # Check if dimension matches by trying to peek at existing data
                # ChromaDB doesn't expose dimension directly, so we check by peeking
                count = existing_collection.count()
                
                if count > 0:
                    # Try to get a sample embedding to check dimension
                    try:
                        sample_results = existing_collection.peek(limit=1)
                        # Check if we have embeddings in the results
                        if sample_results and "embeddings" in sample_results:
                            embeddings_list = sample_results["embeddings"]
                            if embeddings_list and len(embeddings_list) > 0:
                                existing_dimension = len(embeddings_list[0])
                                if existing_dimension != expected_dimension:
                                    logger.warning(
                                        f"ChromaDB collection dimension mismatch: "
                                        f"existing={existing_dimension}, expected={expected_dimension}. "
                                        f"Deleting and recreating collection. "
                                        f"WARNING: All existing embeddings will be lost!"
                                    )
                                    self._client.delete_collection(name=collection_name)
                                    # Create new collection with correct dimension
                                    self.collection = self._client.create_collection(
                                        name=collection_name,
                                        metadata={"hnsw:space": "cosine"}
                                    )
                                    logger.info(f"ChromaDB collection recreated with dimension {expected_dimension}")
                                else:
                                    self.collection = existing_collection
                                    logger.info(f"ChromaDB collection found with matching dimension {expected_dimension}")
                            else:
                                # No embeddings in peek, try to verify with a test query
                                # If this fails, we'll catch it in add/search operations
                                self.collection = existing_collection
                                logger.info(f"ChromaDB collection found (could not verify dimension, will check on use)")
                        else:
                            # No embeddings in results, collection might be empty or using different format
                            # Keep existing collection, dimension will be checked on first use
                            self.collection = existing_collection
                            logger.info(f"ChromaDB collection found (dimension will be verified on first use)")
                    except Exception as e:
                        logger.warning(f"Could not verify collection dimension via peek: {e}. Will verify on first use.")
                        # Keep the collection, we'll catch dimension mismatch errors in add/search
                        self.collection = existing_collection
                else:
                    # Empty collection - keep it, don't recreate unnecessarily
                    # This prevents wiping out chunks that might be in the process of being added
                    self.collection = existing_collection
                    logger.info(f"ChromaDB collection found but empty (will be populated on first add)")
            except Exception as e:
                # Collection doesn't exist, create it
                if "does not exist" in str(e).lower() or "not found" in str(e).lower():
                    self.collection = self._client.create_collection(
                        name=collection_name,
                        metadata={"hnsw:space": "cosine"}
                    )
                    logger.info(f"ChromaDB collection created with dimension {expected_dimension}")
                else:
                    # Unexpected error, re-raise
                    raise
            
            logger.info(f"ChromaDB initialized with embedding dimension {expected_dimension}")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}")
            raise
    
    def _init_pinecone(self):
        """Initialize Pinecone"""
        try:
            import pinecone
            
            pinecone.init(
                api_key=settings.PINECONE_API_KEY,
                environment=settings.PINECONE_ENVIRONMENT
            )
            
            # Get expected embedding dimension
            expected_dimension = self._get_embedding_dimension()
            
            # Get or create index
            if settings.PINECONE_INDEX_NAME not in pinecone.list_indexes():
                pinecone.create_index(
                    settings.PINECONE_INDEX_NAME,
                    dimension=expected_dimension,
                    metric="cosine"
                )
                logger.info(f"Pinecone index created with dimension {expected_dimension}")
            else:
                # Note: Pinecone doesn't allow changing dimension of existing index
                # If dimension mismatch occurs, user needs to manually delete and recreate
                logger.info(f"Pinecone index found, expected dimension {expected_dimension}")
            
            self._client = pinecone.Index(settings.PINECONE_INDEX_NAME)
            logger.info(f"Pinecone initialized with embedding dimension {expected_dimension}")
        except Exception as e:
            logger.error(f"Error initializing Pinecone: {e}")
            raise
    
    def _init_weaviate(self):
        """Initialize Weaviate"""
        try:
            import weaviate
            
            auth = None
            if settings.WEAVIATE_API_KEY:
                auth = weaviate.AuthApiKey(api_key=settings.WEAVIATE_API_KEY)
            
            self._client = weaviate.Client(
                url=settings.WEAVIATE_URL,
                auth_client_secret=auth
            )
            logger.info("Weaviate initialized")
        except Exception as e:
            logger.error(f"Error initializing Weaviate: {e}")
            raise
    
    def add_documents(self, documents: List[Dict], embeddings: List[List[float]], metadata: List[Dict]):
        """
        Add documents to vector store
        
        Args:
            documents: List of document content dicts
            embeddings: List of embedding vectors
            metadata: List of metadata dicts
        """
        if self.store_type == "chroma":
            self._add_chroma(documents, embeddings, metadata)
        elif self.store_type == "pinecone":
            self._add_pinecone(documents, embeddings, metadata)
        elif self.store_type == "weaviate":
            self._add_weaviate(documents, embeddings, metadata)
    
    def _add_chroma(self, documents: List[Dict], embeddings: List[List[float]], metadata: List[Dict]):
        """Add to ChromaDB"""
        ids = [f"chunk_{meta.get('chunk_id', i)}" for i, meta in enumerate(metadata)]
        texts = [doc.get("content", "") for doc in documents]
        
        # Filter out None values from metadata as ChromaDB doesn't accept them
        cleaned_metadata = []
        for meta in metadata:
            cleaned_meta = {k: v for k, v in meta.items() if v is not None}
            cleaned_metadata.append(cleaned_meta)
        
        try:
            logger.info(f"Adding {len(ids)} chunks to ChromaDB collection '{self.collection.name}'")
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=cleaned_metadata
            )
            # Verify chunks were added
            count_after = self.collection.count()
            logger.info(f"ChromaDB collection now contains {count_after} chunks (added {len(ids)})")
        except Exception as e:
            error_msg = str(e).lower()
            if "dimension" in error_msg or "dimensionality" in error_msg:
                # Dimension mismatch detected
                expected_dimension = self._get_embedding_dimension()
                actual_dimension = len(embeddings[0]) if embeddings else None
                logger.error(
                    f"ChromaDB dimension mismatch error: {e}. "
                    f"Expected: {expected_dimension}, Actual: {actual_dimension}. "
                    f"Recreating collection..."
                )
                # Delete and recreate collection
                collection_name = self.collection.name
                self._client.delete_collection(name=collection_name)
                self.collection = self._client.create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"ChromaDB collection recreated. Retrying add operation...")
                # Retry the add operation
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=cleaned_metadata
                )
            else:
                # Re-raise if it's not a dimension error
                raise
    
    def _add_pinecone(self, documents: List[Dict], embeddings: List[List[float]], metadata: List[Dict]):
        """Add to Pinecone"""
        vectors = []
        for i, (doc, emb, meta) in enumerate(zip(documents, embeddings, metadata)):
            # Filter out None values from metadata as Pinecone doesn't accept them
            cleaned_meta = {k: v for k, v in meta.items() if v is not None}
            cleaned_meta["text"] = doc.get("content", "")
            vectors.append({
                "id": f"chunk_{meta.get('chunk_id', i)}",
                "values": emb,
                "metadata": cleaned_meta
            })
        
        self._client.upsert(vectors=vectors)
    
    def _add_weaviate(self, documents: List[Dict], embeddings: List[List[float]], metadata: List[Dict]):
        """Add to Weaviate"""
        # Weaviate implementation would go here
        # This is a simplified version
        pass
    
    def search(
        self, 
        query_embedding: List[float], 
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar documents
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filter_metadata: Metadata filters (e.g., {"case_id": 1})
        
        Returns:
            List of result dicts with: content, metadata, score
        """
        if self.store_type == "chroma":
            return self._search_chroma(query_embedding, top_k, filter_metadata)
        elif self.store_type == "pinecone":
            return self._search_pinecone(query_embedding, top_k, filter_metadata)
        elif self.store_type == "weaviate":
            return self._search_weaviate(query_embedding, top_k, filter_metadata)
    
    def _search_chroma(self, query_embedding: List[float], top_k: int, filter_metadata: Optional[Dict]) -> List[Dict]:
        """Search ChromaDB"""
        where = None
        if filter_metadata:
            # ChromaDB requires $and operator for multiple conditions
            if len(filter_metadata) > 1:
                where = {
                    "$and": [
                        {key: value} for key, value in filter_metadata.items()
                    ]
                }
            else:
                # Single condition - use directly
                where = filter_metadata
        
        # Log search parameters for debugging
        logger.debug(f"ChromaDB search - top_k: {top_k}, where: {where}, embedding_dim: {len(query_embedding)}")
        
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where
            )
            
            # Log results for debugging
            num_results = len(results["ids"][0]) if results.get("ids") and results["ids"][0] else 0
            logger.debug(f"ChromaDB search returned {num_results} results")
        except Exception as e:
            error_msg = str(e).lower()
            if "dimension" in error_msg or "dimensionality" in error_msg:
                # Dimension mismatch detected
                expected_dimension = self._get_embedding_dimension()
                actual_dimension = len(query_embedding) if query_embedding else None
                logger.error(
                    f"ChromaDB dimension mismatch error during search: {e}. "
                    f"Expected: {expected_dimension}, Actual: {actual_dimension}. "
                    f"Collection needs to be recreated. Returning empty results."
                )
                # Return empty results - collection will be recreated on next add operation
                return []
            else:
                # Re-raise if it's not a dimension error
                raise
        
        # Format results
        formatted_results = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": 1 - results["distances"][0][i] if "distances" in results else None
                })
        
        return formatted_results
    
    def _search_pinecone(self, query_embedding: List[float], top_k: int, filter_metadata: Optional[Dict]) -> List[Dict]:
        """Search Pinecone"""
        query_response = self._client.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter_metadata
        )
        
        formatted_results = []
        for match in query_response["matches"]:
            formatted_results.append({
                "content": match["metadata"].get("text", ""),
                "metadata": {k: v for k, v in match["metadata"].items() if k != "text"},
                "score": match["score"]
            })
        
        return formatted_results
    
    def _search_weaviate(self, query_embedding: List[float], top_k: int, filter_metadata: Optional[Dict]) -> List[Dict]:
        """Search Weaviate"""
        # Weaviate implementation would go here
        return []
    
    def delete_documents(self, chunk_ids: List[str]):
        """Delete documents by chunk IDs"""
        if self.store_type == "chroma":
            self.collection.delete(ids=chunk_ids)
        elif self.store_type == "pinecone":
            self._client.delete(ids=chunk_ids)
        elif self.store_type == "weaviate":
            # Weaviate delete implementation
            pass

