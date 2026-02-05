"""
Rule-based risk assessment engine for document access and operations
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger(__name__)


class GovernanceProfile(Enum):
    """Risk governance profiles"""
    PROFILE_A = "A"  # Low risk - minimal controls
    PROFILE_B = "B"  # Medium risk - standard controls
    PROFILE_C = "C"  # High risk - strict controls + immutable logging


class IntentType(Enum):
    """User intent classifications"""
    QUERY = "query"
    EXPORT = "export"
    SHARE = "share"
    DELETE = "delete"
    VIEW = "view"
    ANNOTATE = "annotate"


@dataclass
class RiskScore:
    """Risk assessment result"""
    total_score: int
    pii_detected: bool
    legal_signals: List[str]
    intent_risk: int
    data_sensitivity_score: int
    governance_profile: GovernanceProfile
    requires_logging: bool


class IntentClassifier:
    """Rule-based intent classification from prompts and actions"""
    
    # Intent patterns (prompt-based)
    INTENT_PATTERNS = {
        IntentType.EXPORT: [
            r"export", r"download", r"save as", r"copy to",
            r"send to", r"email", r"share file"
        ],
        IntentType.SHARE: [
            r"share", r"grant access", r"invite", r"collaborate"
        ],
        IntentType.DELETE: [
            r"delete", r"remove", r"destroy", r"purge"
        ],
        IntentType.QUERY: [
            r"what", r"find", r"search", r"show me", r"tell me"
        ],
        IntentType.VIEW: [
            r"view", r"open", r"show", r"display", r"read"
        ]
    }
    
    # Action-based intent mapping
    ACTION_INTENT_MAP = {
        "GET /api/v1/documents/{id}/file": IntentType.VIEW,
        "POST /api/v1/documents/{id}/export": IntentType.EXPORT,
        "POST /api/v1/cases/{id}/share": IntentType.SHARE,
        "DELETE /api/v1/documents/{id}": IntentType.DELETE,
        "POST /api/v1/queries": IntentType.QUERY,
    }
    
    @classmethod
    def classify_from_prompt(cls, prompt: str) -> IntentType:
        """Classify intent from user prompt/text"""
        prompt_lower = prompt.lower()
        
        for intent, patterns in cls.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, prompt_lower):
                    return intent
        
        return IntentType.VIEW  # Default to lowest risk
    
    @classmethod
    def classify_from_action(cls, action: str) -> IntentType:
        """Classify intent from API action/endpoint"""
        return cls.ACTION_INTENT_MAP.get(action, IntentType.VIEW)


class DataSensitivityDetector:
    """Rule-based PII and legal signal detection"""
    
    # PII patterns
    PII_PATTERNS = {
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
        "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    }
    
    # Legal signal keywords
    LEGAL_SIGNALS = {
        "privileged": ["attorney-client", "privileged", "confidential", "work product"],
        "confidential": ["confidential", "proprietary", "trade secret", "nda"],
        "restricted": ["restricted", "for internal use", "do not distribute"],
        "sensitive": ["sensitive", "personal information", "pii", "phi"],
    }
    
    @classmethod
    def detect_pii(cls, text: str) -> bool:
        """Detect if text contains PII"""
        text_lower = text.lower()
        for pattern_name, pattern in cls.PII_PATTERNS.items():
            if re.search(pattern, text_lower):
                logger.info(f"PII detected: {pattern_name}")
                return True
        return False
    
    @classmethod
    def detect_legal_signals(cls, text: str) -> List[str]:
        """Detect legal sensitivity signals"""
        text_lower = text.lower()
        detected_signals = []
        
        for signal_type, keywords in cls.LEGAL_SIGNALS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected_signals.append(signal_type)
                    break
        
        return detected_signals
    
    @classmethod
    def calculate_sensitivity_score(cls, text: str) -> int:
        """Calculate data sensitivity score (0-100)"""
        score = 0
        
        # PII detection (high weight)
        if cls.detect_pii(text):
            score += 50
        
        # Legal signals (weighted)
        signals = cls.detect_legal_signals(text)
        signal_weights = {
            "privileged": 30,
            "confidential": 25,
            "restricted": 20,
            "sensitive": 15,
        }
        
        for signal in signals:
            score += signal_weights.get(signal, 10)
        
        return min(score, 100)  # Cap at 100


class RiskEngine:
    """Rule-based risk assessment engine"""
    
    # Intent risk scores
    INTENT_RISK_SCORES = {
        IntentType.VIEW: 0,
        IntentType.QUERY: 5,
        IntentType.ANNOTATE: 10,
        IntentType.SHARE: 30,
        IntentType.EXPORT: 40,
        IntentType.DELETE: 50,
    }
    
    # Threshold mapping to governance profiles
    PROFILE_THRESHOLDS = {
        GovernanceProfile.PROFILE_A: (0, 30),    # 0-30: Low risk
        GovernanceProfile.PROFILE_B: (31, 70),   # 31-70: Medium risk
        GovernanceProfile.PROFILE_C: (71, 100),   # 71-100: High risk
    }
    
    def __init__(self, profile_a_max: int = 30, profile_b_max: int = 70, profile_c_max: int = 100):
        """
        Initialize risk engine with configurable thresholds
        
        Args:
            profile_a_max: Maximum score for Profile A (default: 30)
            profile_b_max: Maximum score for Profile B (default: 70)
            profile_c_max: Maximum score for Profile C (default: 100)
        """
        self.intent_classifier = IntentClassifier()
        self.sensitivity_detector = DataSensitivityDetector()
        
        # Update thresholds from config
        self.PROFILE_THRESHOLDS = {
            GovernanceProfile.PROFILE_A: (0, profile_a_max),
            GovernanceProfile.PROFILE_B: (profile_a_max + 1, profile_b_max),
            GovernanceProfile.PROFILE_C: (profile_b_max + 1, profile_c_max),
        }
    
    def assess_risk(
        self,
        text: Optional[str] = None,
        prompt: Optional[str] = None,
        action: Optional[str] = None,
        document_metadata: Optional[Dict] = None
    ) -> RiskScore:
        """
        Assess risk based on intent, data sensitivity, and context
        
        Args:
            text: Document text or content to analyze
            prompt: User prompt/query text
            action: API action/endpoint being called
            document_metadata: Additional document metadata
        
        Returns:
            RiskScore with profile assignment
        """
        # 1. Intent classification
        intent = None
        if prompt:
            intent = self.intent_classifier.classify_from_prompt(prompt)
        elif action:
            intent = self.intent_classifier.classify_from_action(action)
        else:
            intent = IntentType.VIEW
        
        intent_risk = self.INTENT_RISK_SCORES.get(intent, 0)
        
        # 2. Data sensitivity detection
        pii_detected = False
        legal_signals = []
        data_sensitivity_score = 0
        
        if text:
            pii_detected = self.sensitivity_detector.detect_pii(text)
            legal_signals = self.sensitivity_detector.detect_legal_signals(text)
            data_sensitivity_score = self.sensitivity_detector.calculate_sensitivity_score(text)
        
        # 3. Calculate total risk score
        total_score = intent_risk + data_sensitivity_score
        
        # 4. Map to governance profile based on threshold
        governance_profile = self._map_to_profile(total_score)
        
        # 5. Determine if immutable logging required (Profile C only)
        requires_logging = governance_profile == GovernanceProfile.PROFILE_C
        
        return RiskScore(
            total_score=total_score,
            pii_detected=pii_detected,
            legal_signals=legal_signals,
            intent_risk=intent_risk,
            data_sensitivity_score=data_sensitivity_score,
            governance_profile=governance_profile,
            requires_logging=requires_logging
        )
    
    def _map_to_profile(self, score: int) -> GovernanceProfile:
        """Map risk score to governance profile based on thresholds"""
        for profile, (min_score, max_score) in self.PROFILE_THRESHOLDS.items():
            if min_score <= score <= max_score:
                return profile
        
        # Default to highest risk if score exceeds max
        return GovernanceProfile.PROFILE_C






