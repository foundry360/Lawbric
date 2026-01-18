"""
Audit logging utilities for compliance and security
"""

from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from typing import Optional
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


