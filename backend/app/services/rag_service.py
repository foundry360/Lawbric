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
        try:
            self.embedding_service = EmbeddingService()
        except Exception as e:
            logger.error(f"Failed to initialize EmbeddingService: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize embedding service: {str(e)}")
        
        try:
            self.vector_store = VectorStore()
        except Exception as e:
            logger.error(f"Failed to initialize VectorStore: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize vector store: {str(e)}")
        
        self._llm_client = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize LLM client - Claude only"""
        if settings.LLM_PROVIDER.lower() == "anthropic" and settings.ANTHROPIC_API_KEY:
            try:
                import anthropic
                self._llm_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                logger.info("RAG service initialized with Claude")
            except ImportError:
                logger.error("Anthropic SDK not installed. Install with: pip install anthropic")
                self._llm_client = None
        else:
            logger.warning("Claude not configured. RAG will only return retrieved chunks. Set LLM_PROVIDER=anthropic and ANTHROPIC_API_KEY in .env")
            self._llm_client = None
    
    def query(
        self, 
        question: str, 
        case_id: int,
        tenant_id: int = None,
        document_id: int = None,
        top_k: int = 5,
        max_citations: int = 5,
        intent: str = None
    ) -> Dict:
        """
        Query the RAG system with a question (tenant-isolated)
        
        Args:
            question: User's question
            case_id: Case ID to filter documents
            tenant_id: Tenant ID for multi-tenant isolation
            document_id: Optional document ID to filter by specific document
            top_k: Number of chunks to retrieve
            max_citations: Maximum number of citations to include
        
        Returns:
            Dict with: answer, citations, confidence_score, retrieved_chunks
        """
        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(question)
        
        # Search vector store with case, tenant, and document filter
        filter_metadata = {}
        if settings.CASE_ISOLATION_ENABLED:
            filter_metadata["case_id"] = case_id
        if tenant_id is not None:
            filter_metadata["tenant_id"] = tenant_id
        if document_id is not None:
            filter_metadata["document_id"] = document_id
        
        filter_metadata = filter_metadata if filter_metadata else None
        
        # Log search parameters for debugging
        logger.info(f"RAG search - case_id: {case_id}, tenant_id: {tenant_id}, document_id: {document_id}, filter: {filter_metadata}, top_k: {top_k}")
        
        retrieved_chunks = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata
        )
        
        logger.info(f"RAG search returned {len(retrieved_chunks)} chunks")
        
        if not retrieved_chunks:
            # Try searching without filters to see if there are any chunks at all
            logger.warning(f"No chunks found with filters. Trying without filters to diagnose...")
            all_chunks = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                filter_metadata=None
            )
            logger.info(f"Search without filters returned {len(all_chunks)} chunks")
            if all_chunks:
                logger.warning(f"Chunks exist but don't match case_id={case_id}. First chunk metadata: {all_chunks[0].get('metadata', {})}")
            
            return {
                "answer": "The provided documents do not contain sufficient information to answer this question. The document may not be fully processed yet, or no matching content was found.",
                "citations": [],
                "confidence_score": None,
                "retrieved_chunks": []
            }
        
        # Generate answer using LLM with retrieved context
        answer, citations = self._generate_grounded_answer(
            question=question,
            retrieved_chunks=retrieved_chunks,
            max_citations=max_citations,
            intent=intent
        )
        
        # Calculate confidence (simplified: based on retrieval scores)
        confidence_score = self._calculate_confidence(retrieved_chunks)
        
        return {
            "answer": answer,
            "citations": [],  # Return empty array - page numbers are included in the answer
            "confidence_score": confidence_score,
            "retrieved_chunks": retrieved_chunks
        }
    
    def _generate_grounded_answer(
        self, 
        question: str, 
        retrieved_chunks: List[Dict],
        max_citations: int = 5,
        intent: str = None
    ) -> tuple:
        """
        Generate answer using LLM with retrieved context
        
        Args:
            question: User's question
            retrieved_chunks: List of retrieved document chunks
            max_citations: Maximum number of citations
            intent: Optional intent type (summarize_section, extract_facts, check_contradictions, general)
        
        Returns:
            Tuple of (answer, citations) - citations will be empty, page numbers are in the answer
        """
        # Prepare context from retrieved chunks
        context_parts = []
        
        for i, chunk in enumerate(retrieved_chunks[:max_citations]):
            content = chunk.get("content", "")
            metadata = chunk.get("metadata", {})
            
            # Include page number in source label so LLM can reference it
            page_num = metadata.get("page_number")
            if page_num is not None:
                context_parts.append(f"[Source {i+1} - {metadata.get('document_name', 'Document')}, Page {page_num}]:\n{content}")
            else:
                context_parts.append(f"[Source {i+1} - {metadata.get('document_name', 'Document')}]:\n{content}")
        
        context = "\n\n".join(context_parts)
        
        # Build prompt that encourages inline citations with page numbers
        prompt = f"""SOURCES:
{context}

QUESTION: {question}

Please provide a clear answer based on the sources above. When referencing specific information, include inline citations with the page number from the source (e.g., "as stated on page 3" or "see page 4-5"). Only reference page numbers that are explicitly shown in the source labels above.

ANSWER:"""

        # Generate answer using Claude
        if self._llm_client and hasattr(self._llm_client, 'messages'):
            answer = self._generate_anthropic(prompt)
        else:
            # Fallback: return concatenated chunks
            answer = f"Based on the retrieved documents:\n\n{context}\n\nNote: This is a summary of retrieved passages. For a more detailed answer, please configure Claude (set LLM_PROVIDER=anthropic and ANTHROPIC_API_KEY in .env)."
            return answer, []  # Return empty citations
        
        # Return empty citations array since we're including page numbers in the answer
        return answer, []
    
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
            error_details = str(e)
            logger.error(f"Error generating Anthropic response: {e}", exc_info=True)
            # Log more details about the error
            if hasattr(e, 'response') and hasattr(e.response, 'json'):
                try:
                    error_json = e.response.json()
                    logger.error(f"Anthropic API error details: {error_json}")
                    if 'error' in error_json and 'message' in error_json['error']:
                        error_details = error_json['error']['message']
                except:
                    pass
            return f"Error generating response: {error_details}. Please check the model name and API key."
    
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

