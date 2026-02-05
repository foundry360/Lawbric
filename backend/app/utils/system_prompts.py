"""
Intent-aware system prompts for Claude queries
System prompts removed - starting fresh (user-driven document analysis)
"""

from typing import Literal

IntentType = Literal["summarize_section", "extract_facts", "check_contradictions", "general"]


def get_system_prompt(intent: IntentType, document_text: str = None) -> str:
    """
    Get intent-aware system prompt for Claude queries.
    System prompts removed - starting fresh (user-driven document analysis).
    """
    return ""


def get_system_prompt_with_sources(intent: IntentType, document_text: str = None) -> str:
    """
    Get intent-aware system prompt with sources included.
    System prompts removed - starting fresh.
    """
    return ""
