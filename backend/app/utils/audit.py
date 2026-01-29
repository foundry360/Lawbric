"""
Audit logging utilities for compliance and security
"""

from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.services.immutable_logger import ImmutableLogger
from typing import Optional, Dict, Any
from datetime import datetime


def log_audit_event(
    db: Session,
    user_id: Optional[int],
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    case_id: Optional[int] = None,
    document_id: Optional[int] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """
    Log an audit event
    
    Args:
        db: Database session
        user_id: User ID performing the action
        action: Action type (upload, query, view, delete, etc.)
        resource_type: Type of resource (document, case, query, etc.)
        resource_id: ID of the resource
        case_id: Associated case ID
        document_id: Associated document ID
        details: Additional details as dict
        ip_address: Client IP address
        user_agent: Client user agent
    """
    audit_log = AuditLog(
        user_id=user_id,
        case_id=case_id,
        document_id=document_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=str(details) if details else None,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(audit_log)
    db.commit()


def log_immutable_audit(
    db: Session,
    user_id: str,
    action: str,
    document_id: str,
    risk_score: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
    case_id: Optional[str] = None
) -> str:
    """
    Log an immutable audit event for Profile C (high-risk) actions only
    
    This function wraps ImmutableLogger and should only be called when
    risk assessment determines the action requires immutable logging.
    
    Args:
        db: Database session
        user_id: User ID performing the action (can be UUID string or integer)
        action: Action type (e.g., "document_access", "document_delete")
        document_id: Document ID being accessed/modified (can be UUID string or integer)
        risk_score: Risk assessment details from RiskEngine
        metadata: Additional metadata
        case_id: Optional case ID (can be UUID string or integer)
    
    Returns:
        log_entry_id: Unique identifier for the log entry
    """
    immutable_logger = ImmutableLogger()
    return immutable_logger.log_action(
        db=db,
        user_id=user_id,
        action=action,
        document_id=document_id,
        risk_score=risk_score,
        metadata=metadata,
        case_id=case_id
    )






