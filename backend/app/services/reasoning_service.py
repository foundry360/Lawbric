"""
Reasoning Service - Claude ONLY for reasoning, synthesis, summarization

This service enforces:
- Claude receives ONLY extracted facts (never raw text)
- Used ONLY when reasoning/synthesis required
- Operates on structured JSON
"""

import logging
import os
from typing import List, Dict, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class ReasoningService:
    """Service for reasoning over extracted facts using Claude"""
    
    # System prompt for Claude reasoning
    REASONING_SYSTEM_PROMPT = """You are a legal analyst.
You may reason ONLY over the provided extracted facts.
Do not introduce new facts or assumptions."""

    def __init__(self):
        """Initialize reasoning service"""
        self._client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Claude client"""
        # Check for API key in settings or environment
        api_key = settings.ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY", "")
        
        if api_key:
            try:
                import anthropic
                
                self._client = anthropic.Anthropic(api_key=api_key)
                logger.info(f"Claude reasoning service initialized (API key found, length: {len(api_key)})")
            except ImportError:
                logger.error("Anthropic SDK not installed. Install with: pip install anthropic")
                self._client = None
            except Exception as e:
                logger.error(f"Failed to initialize Claude client: {e}", exc_info=True)
                self._client = None
        else:
            logger.warning("Anthropic API key not configured - reasoning service unavailable. Set ANTHROPIC_API_KEY in .env or environment.")
            self._client = None
    
    def reason(
        self,
        question: str,
        extracted_facts: List[Dict],
        task_type: str = "general"
    ) -> Dict:
        """
        Perform reasoning over extracted facts using Claude.
        
        Args:
            question: User's question
            extracted_facts: List of dicts with keys: fact, source, page
            task_type: Type of reasoning (contradiction, synthesis, summary, general)
        
        Returns:
            Dict with keys: answer, reasoning, sources
        """
        if not self._client:
            return {
                "answer": "Reasoning service not available. Claude not configured.",
                "reasoning": None,
                "sources": []
            }
        
        # Format extracted facts
        facts_text = self._format_facts(extracted_facts)
        
        # Build reasoning prompt based on task type
        if task_type == "contradiction":
            prompt = self._build_contradiction_prompt(question, facts_text)
        elif task_type == "synthesis":
            prompt = self._build_synthesis_prompt(question, facts_text)
        elif task_type == "summary":
            prompt = self._build_summary_prompt(question, facts_text)
        else:
            prompt = self._build_general_reasoning_prompt(question, facts_text)
        
        try:
            # Use Claude for reasoning
            model = settings.ANTHROPIC_MODEL
            
            logger.info(f"Calling Claude with model: {model}")
            response = self._client.messages.create(
                model=model,
                max_tokens=1000,
                temperature=0.1,  # Low temperature for deterministic reasoning
                system=self.REASONING_SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            answer = response.content[0].text
            
            return {
                "answer": answer,
                "reasoning": "Claude reasoning over extracted facts",
                "sources": self._extract_sources(extracted_facts)
            }
            
        except Exception as e:
            logger.error(f"Error in Claude reasoning: {e}", exc_info=True)
            return {
                "answer": f"Error performing reasoning: {str(e)}",
                "reasoning": None,
                "sources": []
            }
    
    def _format_facts(self, extracted_facts: List[Dict]) -> str:
        """Format extracted facts for reasoning prompt"""
        lines = ["EXTRACTED FACTS:"]
        for i, fact_dict in enumerate(extracted_facts, 1):
            fact_text = fact_dict.get("fact", "")
            source = fact_dict.get("source", {})
            doc_name = source.get("document_name", "Unknown")
            page = source.get("page_number", "N/A")
            lines.append(f"{i}. [{doc_name}, Page {page}]: {fact_text}")
        
        return "\n".join(lines)
    
    def _build_contradiction_prompt(self, question: str, facts_text: str) -> str:
        """Build prompt for contradiction detection"""
        return f"""{facts_text}

QUESTION: {question}

Analyze the extracted facts for contradictions. Identify statements that cannot both be true.
If contradictions exist, explain them clearly. If no contradictions, state that clearly."""
    
    def _build_synthesis_prompt(self, question: str, facts_text: str) -> str:
        """Build prompt for synthesis"""
        return f"""{facts_text}

QUESTION: {question}

Synthesize the extracted facts to answer the question. Combine information from multiple sources where relevant."""
    
    def _build_summary_prompt(self, question: str, facts_text: str) -> str:
        """Build prompt for summarization"""
        return f"""{facts_text}

QUESTION: {question}

Summarize the extracted facts relevant to the question. Focus on key points."""
    
    def _build_general_reasoning_prompt(self, question: str, facts_text: str) -> str:
        """Build prompt for general reasoning"""
        return f"""{facts_text}

QUESTION: {question}

Reason over the extracted facts to answer the question. Use only the provided facts."""
    
    def _extract_sources(self, extracted_facts: List[Dict]) -> List[Dict]:
        """Extract unique sources from facts"""
        sources = []
        seen = set()
        
        for fact_dict in extracted_facts:
            source = fact_dict.get("source", {})
            key = (source.get("document_name"), source.get("page_number"))
            if key not in seen:
                sources.append(source)
                seen.add(key)
        
        return sources

