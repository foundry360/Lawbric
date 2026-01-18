"""
RAG (Retrieval-Augmented Generation) service for grounded AI responses
"""

import logging
from typing import List, Dict, Optional
import json

from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore
from app.core.config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """RAG service for generating source-grounded responses"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self._llm_client = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize LLM client"""
        if settings.LLM_PROVIDER.lower() == "openai" and settings.OPENAI_API_KEY:
            import openai
            openai.api_key = settings.OPENAI_API_KEY
            self._llm_client = "openai"
        elif settings.LLM_PROVIDER.lower() == "anthropic" and settings.ANTHROPIC_API_KEY:
            try:
                import anthropic
                self._llm_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            except ImportError:
                logger.warning("Anthropic SDK not installed, falling back to OpenAI or chunks only")
                self._llm_client = None
        else:
            logger.warning("No LLM provider configured, RAG will only return retrieved chunks")
            self._llm_client = None
    
    def query(
        self, 
        question: str, 
        case_id: int,
        top_k: int = 5,
        max_citations: int = 5
    ) -> Dict:
        """
        Query the RAG system with a question
        
        Args:
            question: User's question
            case_id: Case ID to filter documents
            top_k: Number of chunks to retrieve
            max_citations: Maximum number of citations to include
        
        Returns:
            Dict with: answer, citations, confidence_score, retrieved_chunks
        """
        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(question)
        
        # Search vector store with case filter
        filter_metadata = {"case_id": case_id} if settings.CASE_ISOLATION_ENABLED else None
        retrieved_chunks = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata
        )
        
        if not retrieved_chunks:
            return {
                "answer": "The provided documents do not contain sufficient information to answer this question.",
                "citations": [],
                "confidence_score": None,
                "retrieved_chunks": []
            }
        
        # Generate answer using LLM with retrieved context
        answer, citations = self._generate_grounded_answer(
            question=question,
            retrieved_chunks=retrieved_chunks,
            max_citations=max_citations
        )
        
        # Calculate confidence (simplified: based on retrieval scores)
        confidence_score = self._calculate_confidence(retrieved_chunks)
        
        return {
            "answer": answer,
            "citations": citations[:max_citations],
            "confidence_score": confidence_score,
            "retrieved_chunks": retrieved_chunks
        }
    
    def _generate_grounded_answer(
        self, 
        question: str, 
        retrieved_chunks: List[Dict],
        max_citations: int = 5
    ) -> tuple:
        """
        Generate answer using LLM with retrieved context
        
        Returns:
            Tuple of (answer, citations)
        """
        # Prepare context from retrieved chunks
        context_parts = []
        citations = []
        
        for i, chunk in enumerate(retrieved_chunks[:max_citations]):
            content = chunk.get("content", "")
            metadata = chunk.get("metadata", {})
            
            # Build citation
            citation = {
                "document_id": metadata.get("document_id"),
                "document_name": metadata.get("document_name", "Unknown"),
                "page_number": metadata.get("page_number"),
                "paragraph_number": metadata.get("paragraph_number"),
                "chunk_id": metadata.get("chunk_id"),
                "quoted_text": content[:200] + "..." if len(content) > 200 else content,
                "confidence": chunk.get("score")
            }
            citations.append(citation)
            
            # Add to context
            context_parts.append(f"[Source {i+1} - {metadata.get('document_name', 'Document')}, Page {metadata.get('page_number', 'N/A')}]:\n{content}")
        
        context = "\n\n".join(context_parts)
        
        # Build prompt with strict grounding instructions
        prompt = f"""You are a legal AI assistant. Answer the question using ONLY the information provided in the sources below. 

CRITICAL RULES:
1. Only use information explicitly stated in the sources
2. If the answer is not in the sources, say: "The provided documents do not contain sufficient information to answer this question."
3. Cite specific sources using [Source X] format
4. Do not infer, assume, or add information not in the sources
5. If information is unclear or contradictory, state that clearly

SOURCES:
{context}

QUESTION: {question}

ANSWER (with citations in [Source X] format):"""

        # Generate answer using LLM
        if self._llm_client == "openai":
            answer = self._generate_openai(prompt)
        elif self._llm_client and hasattr(self._llm_client, 'messages'):
            answer = self._generate_anthropic(prompt)
        else:
            # Fallback: return concatenated chunks
            answer = f"Based on the retrieved documents:\n\n{context}\n\nNote: This is a summary of retrieved passages. For a more detailed answer, please configure an LLM provider."
            return answer, citations
        
        return answer, citations
    
    def _generate_openai(self, prompt: str) -> str:
        """Generate answer using OpenAI"""
        try:
            import openai
            
            response = openai.ChatCompletion.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a legal AI assistant that provides accurate, source-grounded answers. Never hallucinate or make up information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for accuracy
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {e}")
            return "Error generating response. Please try again."
    
    def _generate_anthropic(self, prompt: str) -> str:
        """Generate answer using Anthropic Claude"""
        try:
            response = self._llm_client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=1000,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error generating Anthropic response: {e}")
            return "Error generating response. Please try again."
    
    def _calculate_confidence(self, retrieved_chunks: List[Dict]) -> Dict:
        """Calculate confidence scores"""
        if not retrieved_chunks:
            return {"overall": 0.0, "top_score": 0.0}
        
        scores = [chunk.get("score", 0.0) for chunk in retrieved_chunks if chunk.get("score")]
        if not scores:
            return {"overall": 0.5, "top_score": 0.5}
        
        return {
            "overall": sum(scores) / len(scores) if scores else 0.0,
            "top_score": max(scores) if scores else 0.0,
            "num_sources": len(retrieved_chunks)
        }

