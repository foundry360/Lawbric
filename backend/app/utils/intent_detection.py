"""
Intent detection utility for determining user intent from queries
"""

import re
import logging
from typing import Literal

logger = logging.getLogger(__name__)

# Intent types
IntentType = Literal["summarize_section", "extract_facts", "check_contradictions", "general"]


def detect_intent(query: str) -> IntentType:
    """
    Detect user intent from query text.
    
    Rules:
    - If query is a direct question (who/what/when/where/how/which) → general (Q&A)
    - If query contains "Summarize Section X" or similar → summarize_section
    - If query asks about testimony, statements, or facts → extract_facts
    - If query asks about contradictions, conflicts, or discrepancies → check_contradictions
    - Otherwise → general
    
    Args:
        query: User query text
        
    Returns:
        Detected intent type
    """
    query_lower = query.lower().strip()
    
    # FIRST: Check for direct questions - these should be general Q&A, not fact extraction
    # Direct questions typically start with question words and ask for specific information
    direct_question_patterns = [
        r"^who\s+(are|is|was|were|did|does|do)",
        r"^what\s+(are|is|was|were|did|does|do|was|is)",
        r"^when\s+(did|does|do|was|is|were|are)",
        r"^where\s+(did|does|do|was|is|were|are)",
        r"^how\s+(many|much|did|does|do|was|is|were|are)",
        r"^which\s+(are|is|was|were|did|does|do)",
        r"^who\s+are\s+the\s+",  # "Who are the defendants?"
        r"^what\s+are\s+the\s+",  # "What are the key terms?"
        r"^list\s+the\s+",  # "List the defendants"
        r"^name\s+the\s+",  # "Name the parties"
    ]
    
    for pattern in direct_question_patterns:
        if re.match(pattern, query_lower):
            logger.info(f"Detected intent: general (direct question pattern: {pattern})")
            return "general"
    
    # Check for summarization intent
    summarize_patterns = [
        r"summarize\s+section\s+\w+",
        r"summarize\s+the\s+section",
        r"provide\s+a\s+summary\s+of\s+section",
        r"summary\s+of\s+section",
        r"summarize\s+document",
        r"summarize\s+the\s+document",
    ]
    for pattern in summarize_patterns:
        if re.search(pattern, query_lower):
            logger.info(f"Detected intent: summarize_section (pattern: {pattern})")
            return "summarize_section"
    
    # Check for fact extraction intent
    facts_patterns = [
        r"testimony",
        r"statements?",
        r"facts?",
        r"what\s+did\s+.*\s+say",
        r"what\s+was\s+stated",
        r"extract\s+facts?",
        r"what\s+facts?",
        r"identify\s+facts?",
        r"list\s+facts?",
    ]
    for pattern in facts_patterns:
        if re.search(pattern, query_lower):
            logger.info(f"Detected intent: extract_facts (pattern: {pattern})")
            return "extract_facts"
    
    # Check for contradiction detection intent
    contradiction_patterns = [
        r"contradict",
        r"conflict",
        r"discrepanc",
        r"inconsist",
        r"disagree",
        r"differ",
        r"compare\s+.*\s+versus",
        r"compare\s+.*\s+vs",
        r"are\s+there\s+contradictions",
        r"check\s+for\s+contradictions",
    ]
    for pattern in contradiction_patterns:
        if re.search(pattern, query_lower):
            logger.info(f"Detected intent: check_contradictions (pattern: {pattern})")
            return "check_contradictions"
    
    # Default to general
    logger.info("Detected intent: general (no specific pattern matched)")
    return "general"

