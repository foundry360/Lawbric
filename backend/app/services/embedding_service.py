"""
Embedding service for generating vector embeddings
"""

import logging
from typing import List
from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings"""
    
    def __init__(self):
        self.provider = "sentence-transformers"  # Always use sentence-transformers
        self._model = None
        self._initialize()
    
    def _initialize(self):
        """Initialize embedding model"""
        # Use sentence-transformers for embeddings (Claude is used for LLM tasks, not embeddings)
        # This is lightweight and doesn't require API keys
        logger.info("Using sentence-transformers for embeddings (Claude-only configuration)")
        self.provider = "sentence-transformers"
        self._model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dimension = 384
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        return self.embed_texts([text])[0]
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        # Always use sentence-transformers (Claude-only configuration)
        return self._embed_sentence_transformers(texts)
    
    def _embed_sentence_transformers(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using sentence-transformers"""
        if not self._model:
            self._model = SentenceTransformer('all-MiniLM-L6-v2')
        
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()










