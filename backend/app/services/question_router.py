"""
Question Router - Maps questions to fact types and document sections

This is rules-based routing - NO LLM decides which sections to search.
"""

import logging
import re
from typing import Dict, List, Literal

logger = logging.getLogger(__name__)

FactType = Literal["party", "attorney", "date", "amount", "term", "witness_statement", "general"]


class QuestionRouter:
    """Routes questions to appropriate fact types and document sections"""
    
    # Mapping of fact types to typical document section locations
    FACT_TYPE_SECTIONS = {
        "party": ["pages_1_5"],  # Parties typically listed on first pages
        "attorney": ["pages_1_10"],  # Attorney info often in headers/first pages
        "date": ["all"],  # Dates can be anywhere
        "amount": ["all"],  # Amounts can be anywhere
        "term": ["all"],  # Terms can be anywhere
        "witness_statement": ["all"],  # Testimony throughout
        "general": ["all"]  # General questions search all
    }
    
    # Patterns for detecting fact types
    PARTY_PATTERNS = [
        r"\b(defendant|plaintiff|party|parties|respondent|petitioner)\b",
        r"who\s+(is|are)\s+(the\s+)?(defendant|plaintiff|party)",
        r"list\s+(the\s+)?(defendant|plaintiff|party)"
    ]
    
    ATTORNEY_PATTERNS = [
        r"\b(attorney|lawyer|counsel|esquire|esq|represent)\b",
        r"who\s+(is|represents?)\s+(the\s+)?(attorney|lawyer|counsel)",
        r"for\s+[^?]+\s+(attorney|lawyer|counsel)"
    ]
    
    DATE_PATTERNS = [
        r"\b(date|when|occurred|happened|executed|signed)\b",
        r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",  # Date formats
        r"(january|february|march|april|may|june|july|august|september|october|november|december)"
    ]
    
    AMOUNT_PATTERNS = [
        r"\b(amount|cost|price|value|payment|dollar|dollars|\$)\b",
        r"\$\d+",  # Dollar amounts
        r"\d+\s*(million|thousand|billion)"
    ]
    
    TERM_PATTERNS = [
        r"\b(term|clause|provision|condition|agreement)\b",
        r"what\s+(are|is)\s+(the\s+)?(term|clause|provision)"
    ]
    
    WITNESS_PATTERNS = [
        r"\b(witness|testimony|deposition|said|stated|testified)\b",
        r"what\s+did\s+[^?]+\s+(say|state|testify)"
    ]
    
    def classify_question(self, question: str) -> FactType:
        """
        Classify question into fact type using pattern matching.
        
        Args:
            question: User's question
        
        Returns:
            FactType classification
        """
        question_lower = question.lower()
        
        # Check patterns in order of specificity
        if any(re.search(pattern, question_lower, re.IGNORECASE) for pattern in self.PARTY_PATTERNS):
            return "party"
        
        if any(re.search(pattern, question_lower, re.IGNORECASE) for pattern in self.ATTORNEY_PATTERNS):
            return "attorney"
        
        if any(re.search(pattern, question_lower, re.IGNORECASE) for pattern in self.WITNESS_PATTERNS):
            return "witness_statement"
        
        if any(re.search(pattern, question_lower, re.IGNORECASE) for pattern in self.DATE_PATTERNS):
            return "date"
        
        if any(re.search(pattern, question_lower, re.IGNORECASE) for pattern in self.AMOUNT_PATTERNS):
            return "amount"
        
        if any(re.search(pattern, question_lower, re.IGNORECASE) for pattern in self.TERM_PATTERNS):
            return "term"
        
        return "general"
    
    def get_section_filter(self, fact_type: FactType) -> Dict:
        """
        Get section filter for fact type.
        
        Args:
            fact_type: Classified fact type
        
        Returns:
            Dict with filter criteria (e.g., {"page_range": (1, 5)})
        """
        section_hint = self.FACT_TYPE_SECTIONS.get(fact_type, ["all"])
        
        if "pages_1_5" in section_hint:
            return {"page_range": (1, 5), "priority": "early_pages"}
        elif "pages_1_10" in section_hint:
            return {"page_range": (1, 10), "priority": "early_pages"}
        else:
            return {"page_range": None, "priority": "all"}
    
    def requires_reasoning(self, question: str) -> bool:
        """
        Determine if question requires reasoning (vs simple extraction).
        
        Args:
            question: User's question
        
        Returns:
            True if reasoning required (synthesis, comparison, contradiction detection)
        """
        reasoning_keywords = [
            "compare", "contradict", "inconsist", "analyze", "synthesize",
            "summarize", "explain", "why", "how", "what are the implications"
        ]
        
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in reasoning_keywords)


