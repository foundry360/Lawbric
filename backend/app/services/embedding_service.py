"""
Embedding service for generating vector embeddings
"""

import logging
from typing import List
import openai
from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings"""
    
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self._model = None
        self._initialize()
    
    def _initialize(self):
        """Initialize embedding model"""
        if self.provider == "openai":
            if settings.OPENAI_API_KEY:
                openai.api_key = settings.OPENAI_API_KEY
            else:
                logger.warning("OpenAI API key not set, falling back to sentence-transformers")
                self.provider = "sentence-transformers"
        
        if self.provider != "openai" or not settings.OPENAI_API_KEY:
            # Use sentence-transformers as fallback
            logger.info("Using sentence-transformers for embeddings")
            self._model = SentenceTransformer('all-MiniLM-L6-v2')
            self.embedding_dimension = 384
        else:
            self.embedding_dimension = 1536  # OpenAI ada-002 dimension
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        return self.embed_texts([text])[0]
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if self.provider == "openai" and settings.OPENAI_API_KEY:
            return self._embed_openai(texts)
        else:
            return self._embed_sentence_transformers(texts)
    
    def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI"""
        try:
            response = openai.Embedding.create(
                model="text-embedding-ada-002",
                input=texts
            )
            return [item["embedding"] for item in response["data"]]
        except Exception as e:
            logger.error(f"Error generating OpenAI embeddings: {e}")
            # Fallback to sentence-transformers
            if not self._model:
                self._model = SentenceTransformer('all-MiniLM-L6-v2')
            return self._embed_sentence_transformers(texts)
    
    def _embed_sentence_transformers(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using sentence-transformers"""
        if not self._model:
            self._model = SentenceTransformer('all-MiniLM-L6-v2')
        
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()




