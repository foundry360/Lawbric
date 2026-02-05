"""
Fact Extraction Service - Claude ONLY for verbatim extraction

This service enforces:
- Claude is used ONLY for factual extraction
- Output is verbatim or NOT FOUND
- Returns structured JSON
- Context limited to < 1,500 tokens
"""

import logging
import json
from typing import List, Dict, Optional
import os
from app.core.config import settings

logger = logging.getLogger(__name__)


class FactExtractionService:
    """Service for extracting verbatim facts using Claude"""
    
    # System prompt for Claude extraction - ENFORCES verbatim extraction only
    EXTRACTION_SYSTEM_PROMPT = """You are a legal fact extraction engine.

Rules:
- You may ONLY return text that appears verbatim in the provided context.
- If the answer does not appear explicitly, return: NOT FOUND.
- Do NOT infer.
- Do NOT paraphrase.
- Do NOT explain.

Return valid JSON only."""

    def __init__(self):
        """Initialize fact extraction service"""
        self._client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Claude client"""
        api_key = settings.ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY", "")
        
        if api_key:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=api_key)
                logger.info(f"Claude fact extraction service initialized (API key found, length: {len(api_key)})")
            except ImportError:
                logger.error("Anthropic SDK not installed. Install with: pip install anthropic")
                self._client = None
            except Exception as e:
                logger.error(f"Failed to initialize Claude client: {e}", exc_info=True)
                self._client = None
        else:
            logger.warning("Anthropic API key not configured - fact extraction service unavailable. Set ANTHROPIC_API_KEY in .env or environment.")
            self._client = None
    
    async def extract_facts(
        self,
        question: str,
        document_sections: List[Dict],
        max_tokens: int = 1500
    ) -> Dict:
        """
        Extract verbatim facts from document sections using Claude.
        
        Args:
            question: User's question (used to focus extraction)
            document_sections: List of dicts with keys: content, document_name, page_number
            max_tokens: Maximum context tokens (default 1500)
        
        Returns:
            Dict with keys:
            - facts: List of extracted facts (verbatim text)
            - not_found: bool (True if answer not in context)
            - sources: List of source metadata
        """
        if not self._client:
            return {
                "facts": [],
                "not_found": True,
                "sources": [],
                "error": "Claude not configured. Set ANTHROPIC_API_KEY in .env or environment."
            }
        
        # Limit context to max_tokens
        context_parts = []
        total_chars = 0
        max_chars = max_tokens * 4  # ~4 chars per token
        
        for section in document_sections:
            content = section.get("content", "")
            if total_chars + len(content) > max_chars:
                # Truncate this section if needed
                remaining = max_chars - total_chars
                if remaining > 100:  # Only include if meaningful
                    content = content[:remaining] + "...[truncated]"
                else:
                    break
            
            doc_name = section.get("document_name", "Document")
            page = section.get("page_number", "N/A")
            context_parts.append(f"[{doc_name}, Page {page}]:\n{content}")
            total_chars += len(content)
        
        context = "\n\n".join(context_parts)
        
        # Build extraction prompt
        prompt = f"""CONTEXT:
{context}

QUESTION: {question}

Extract ONLY verbatim text that directly answers the question. If not found, return NOT FOUND.

Return JSON format:
{{
    "facts": ["verbatim text 1", "verbatim text 2"],
    "not_found": false,
    "sources": [
        {{"document_name": "...", "page": "..."}}
    ]
}}"""

        try:
            # Call Claude for extraction (run synchronous call in executor to maintain async interface)
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            response = await loop.run_in_executor(
                None,
                lambda: self._client.messages.create(
                    model=settings.ANTHROPIC_MODEL,
                    max_tokens=1000,
                    temperature=0.1,  # Low temperature for verbatim extraction
                    system=self.EXTRACTION_SYSTEM_PROMPT,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
            )
            
            raw_response = response.content[0].text
            
            # Parse JSON response
            return self._parse_extraction_response(raw_response, document_sections)
                
        except Exception as e:
            logger.error(f"Error extracting facts with Claude: {e}", exc_info=True)
            return {
                "facts": [],
                "not_found": True,
                "sources": [],
                "error": str(e)
            }
    
    def _parse_extraction_response(
        self,
        raw_response: str,
        document_sections: List[Dict]
    ) -> Dict:
        """
        Parse Claude's extraction response and validate.
        
        Args:
            raw_response: Raw text response from Claude
            document_sections: Original sections for validation
        
        Returns:
            Parsed and validated extraction result
        """
        # Try to extract JSON from response
        json_start = raw_response.find("{")
        json_end = raw_response.rfind("}") + 1
        
        if json_start == -1 or json_end == 0:
            # No JSON found - check for NOT FOUND
            if "NOT FOUND" in raw_response.upper():
                return {
                    "facts": [],
                    "not_found": True,
                    "sources": []
                }
            # Try to extract facts as plain text
            return self._extract_facts_from_text(raw_response, document_sections)
        
        try:
            json_str = raw_response[json_start:json_end]
            parsed = json.loads(json_str)
            
            # Validate structure
            facts = parsed.get("facts", [])
            not_found = parsed.get("not_found", False)
            
            # Validate facts exist in source
            validated_facts = self._validate_facts(facts, document_sections)
            
            return {
                "facts": validated_facts,
                "not_found": not_found or len(validated_facts) == 0,
                "sources": self._extract_sources(document_sections)
            }
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON from Claude response: {raw_response[:200]}")
            return self._extract_facts_from_text(raw_response, document_sections)
    
    def _validate_facts(
        self,
        facts: List[str],
        document_sections: List[Dict]
    ) -> List[str]:
        """
        Validate that extracted facts exist verbatim in source sections.
        
        Args:
            facts: List of extracted fact strings
            document_sections: Source sections to validate against
        
        Returns:
            List of validated facts (only those found in source)
        """
        # Combine all source text
        source_text = " ".join([s.get("content", "").lower() for s in document_sections])
        
        validated = []
        for fact in facts:
            if not fact or not fact.strip():
                continue
            
            # Check if fact exists verbatim (case-insensitive, allow whitespace normalization)
            fact_normalized = " ".join(fact.lower().split())
            source_normalized = " ".join(source_text.split())
            
            if fact_normalized in source_normalized:
                validated.append(fact)
            else:
                logger.warning(f"Fact not found in source: {fact[:50]}...")
        
        return validated
    
    def _extract_facts_from_text(
        self,
        text: str,
        document_sections: List[Dict]
    ) -> Dict:
        """Extract facts from plain text response (fallback)"""
        if "NOT FOUND" in text.upper():
            return {
                "facts": [],
                "not_found": True,
                "sources": []
            }
        
        # Try to extract quoted strings or lines
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        potential_facts = []
        
        for line in lines:
            # Look for quoted text
            if '"' in line:
                import re
                quoted = re.findall(r'"([^"]+)"', line)
                potential_facts.extend(quoted)
            elif line and not line.startswith("{"):
                potential_facts.append(line)
        
        validated = self._validate_facts(potential_facts, document_sections)
        
        return {
            "facts": validated,
            "not_found": len(validated) == 0,
            "sources": self._extract_sources(document_sections)
        }
    
    def _extract_sources(self, document_sections: List[Dict]) -> List[Dict]:
        """Extract source metadata from sections"""
        sources = []
        seen = set()
        
        for section in document_sections:
            key = (section.get("document_name"), section.get("page_number"))
            if key not in seen:
                sources.append({
                    "document_name": section.get("document_name", "Unknown"),
                    "page_number": section.get("page_number", "N/A")
                })
                seen.add(key)
        
        return sources

