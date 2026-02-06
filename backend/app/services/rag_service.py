"""
RAG (Retrieval-Augmented Generation) service for grounded AI responses
"""

import logging
from typing import List, Dict, Optional
import json
import re

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
            "citations": citations,  # Return citations with document names and page numbers
            "confidence_score": confidence_score,
            "retrieved_chunks": []  # Don't return chunks to frontend - they're only used internally
        }
    
    def _clean_chunk_content(self, content: str) -> str:
        """Clean chunk content by normalizing whitespace and removing formatting artifacts"""
        if not content:
            return ""
        
        # First, detect if this looks like PDF extraction with one word per line
        # Check if most lines are very short (1-3 words)
        lines = content.split('\n')
        short_lines = sum(1 for line in lines if line.strip() and len(line.strip().split()) <= 3)
        total_lines = sum(1 for line in lines if line.strip())
        
        # If more than 70% of lines are short, likely PDF extraction issue
        if total_lines > 0 and (short_lines / total_lines) > 0.7:
            # Join all lines with spaces, then normalize
            cleaned = ' '.join(line.strip() for line in lines if line.strip())
            # Normalize multiple spaces
            cleaned = re.sub(r' +', ' ', cleaned)
            # Try to restore some paragraph structure by looking for sentence endings
            # Add line breaks after periods followed by capital letters (likely new sentence)
            cleaned = re.sub(r'\. ([A-Z])', r'.\n\n\1', cleaned)
            # Clean up multiple newlines
            cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
            return cleaned.strip()
        
        # Normal cleaning for properly formatted text
        # Replace multiple newlines with double newline (paragraph break)
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Normalize spaces
        content = re.sub(r' +', ' ', content)  # Multiple spaces to single
        content = re.sub(r'\n +', '\n', content)  # Spaces after newlines
        content = re.sub(r' +\n', '\n', content)  # Spaces before newlines
        
        return content.strip()
    
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
            Tuple of (answer, citations) - citations with document names and page numbers
        """
        # Prepare context with proper source attribution
        context_parts = []
        citations = []
        
        # Group chunks by document to avoid mixing information
        chunks_by_doc = {}
        for chunk in retrieved_chunks[:max_citations]:
            metadata = chunk.get("metadata", {})
            doc_id = metadata.get("document_id")
            doc_name = metadata.get("document_name", "Unknown Document")
            page_num = metadata.get("page_number")
            content = chunk.get("content", "").strip()
            
            if not content:
                continue
            
            # Clean chunk content to fix formatting issues
            content = self._clean_chunk_content(content)
            
            if not content:
                continue
                
            # Group by document
            if doc_id not in chunks_by_doc:
                chunks_by_doc[doc_id] = {
                    "document_name": doc_name,
                    "document_id": doc_id,
                    "chunks": []
                }
            
            chunks_by_doc[doc_id]["chunks"].append({
                "content": content,
                "page_number": page_num
            })
        
        # Build context with clear source attribution
        for doc_id, doc_data in chunks_by_doc.items():
            doc_name = doc_data["document_name"]
            for chunk_data in doc_data["chunks"]:
                content = chunk_data["content"]
                page_num = chunk_data["page_number"]
                
                # Format with document name and page for clarity
                if page_num is not None:
                    context_parts.append(f"[{doc_name}, Page {page_num}]:\n{content}")
                    # Create citation
                    citations.append({
                        "document_id": doc_id,
                        "document_name": doc_name,
                        "page_number": page_num,
                        "quoted_text": content[:200] if len(content) > 200 else content,  # First 200 chars
                        "confidence": None
                    })
                else:
                    context_parts.append(f"[{doc_name}]:\n{content}")
                    citations.append({
                        "document_id": doc_id,
                        "document_name": doc_name,
                        "page_number": None,
                        "quoted_text": content[:200] if len(content) > 200 else content,
                        "confidence": None
                    })
        
        context = "\n\n".join(context_parts)
        
        # Build a structured prompt that ensures proper answering
        prompt = f"""You are a legal research assistant. Answer the user's question using ONLY the information provided in the document excerpts below.

DOCUMENT EXCERPTS:
{context}

USER QUESTION: {question}

INSTRUCTIONS:
- Answer the question DIRECTLY and COMPLETELY in the first sentence
- Use ONLY the information from the excerpts - do not add external knowledge
- If the excerpts don't contain enough information, state that clearly
- When referencing information, mention the document name and page number naturally (e.g., "According to [Document Name, Page 3]...")
- If information comes from multiple documents, clearly distinguish between them
- Format your answer with proper paragraphs - do NOT just list raw text
- Be specific and cite sources naturally within your answer
- Do NOT repeat the question or add preamble - just provide the answer

ANSWER:"""

        # Generate answer using Claude
        if self._llm_client:
            try:
                answer = self._generate_anthropic(prompt)
                # Validate answer is not just raw chunks
                if answer and len(answer) > 100 and not answer.startswith("Based on the retrieved documents"):
                    # Answer looks good
                    logger.info(f"Generated answer of length {len(answer)}")
                else:
                    logger.warning(f"Answer may be malformed: {answer[:100] if answer else 'None'}")
            except Exception as e:
                logger.error(f"Error generating answer with LLM: {e}", exc_info=True)
                # Return a helpful error message instead of raw chunks
                answer = f"I encountered an error while generating an answer. The relevant document excerpts were found, but I was unable to process them. Please try again or check the LLM configuration."
                return answer, citations
        else:
            # Fallback: return helpful message instead of raw chunks
            logger.warning("LLM client not available, returning fallback message")
            answer = f"I found relevant information in the documents, but I cannot generate a detailed answer because the AI model is not configured. Please configure Claude (set LLM_PROVIDER=anthropic and ANTHROPIC_API_KEY in .env)."
            return answer, citations
        
        return answer, citations
    
    def _generate_anthropic(self, prompt: str) -> str:
        """Generate answer using Anthropic Claude"""
        try:
            logger.info(f"Calling Anthropic API with model {settings.ANTHROPIC_MODEL}")
            response = self._llm_client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=2000,
                temperature=0.2,  # Lower temperature for more focused, factual responses
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            if not response.content or len(response.content) == 0:
                logger.error("Anthropic API returned empty response")
                raise ValueError("Empty response from Anthropic API")
            
            answer = response.content[0].text.strip()
            
            if not answer:
                logger.error("Anthropic API returned empty answer text")
                raise ValueError("Empty answer text from Anthropic API")
            
            logger.info(f"Successfully generated answer of length {len(answer)}")
            return answer
            
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
            # Re-raise to be handled by caller
            raise RuntimeError(f"Failed to generate answer: {error_details}")
    
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

