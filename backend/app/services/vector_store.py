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
    
    def __init__(self):
        self.store_type = settings.VECTOR_DB_TYPE.lower()
        self._client = None
        self._initialize()
    
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
            
            # Get or create collection
            self.collection = self._client.get_or_create_collection(
                name="legal_documents",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("ChromaDB initialized")
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
            
            # Get or create index
            if settings.PINECONE_INDEX_NAME not in pinecone.list_indexes():
                pinecone.create_index(
                    settings.PINECONE_INDEX_NAME,
                    dimension=1536,  # OpenAI ada-002 dimension
                    metric="cosine"
                )
            
            self._client = pinecone.Index(settings.PINECONE_INDEX_NAME)
            logger.info("Pinecone initialized")
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
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadata
        )
    
    def _add_pinecone(self, documents: List[Dict], embeddings: List[List[float]], metadata: List[Dict]):
        """Add to Pinecone"""
        vectors = []
        for i, (doc, emb, meta) in enumerate(zip(documents, embeddings, metadata)):
            vectors.append({
                "id": f"chunk_{meta.get('chunk_id', i)}",
                "values": emb,
                "metadata": {**meta, "text": doc.get("content", "")}
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
        where = filter_metadata if filter_metadata else None
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where
        )
        
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

