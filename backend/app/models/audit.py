"""
Audit log model for compliance and security tracking
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from app.core.database import Base


class AuditLog(Base):
    """Audit log for tracking all access and operations"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    
    action = Column(String, nullable=False, index=True)  # upload, query, view, delete, etc.
    resource_type = Column(String, nullable=False)  # document, case, query, etc.
    resource_id = Column(Integer, nullable=True)
    
    details = Column(Text, nullable=True)  # JSON with additional details
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class ImmutableAuditLog(Base):
    """Immutable audit log for Profile C (high-risk) actions only
    
    This table is append-only - records cannot be updated or deleted.
    Each record includes a hash for integrity verification.
    """
    __tablename__ = "immutable_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)  # Can be UUID string or integer
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="SET NULL"), nullable=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True)
    
    action = Column(String, nullable=False, index=True)  # document_access, document_delete, etc.
    resource_type = Column(String, nullable=False)  # document, case, query, etc.
    resource_id = Column(Integer, nullable=True)
    
    details = Column(Text, nullable=True)  # JSON with risk_score, metadata, and log_hash
    log_hash = Column(String, nullable=False, index=True)  # SHA-256 hash for integrity verification
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Note: Append-only constraint will be enforced at the database level via migration
    # SQLite doesn't support CHECK constraints for preventing UPDATE/DELETE,
    # but we can enforce this at the application level and use triggers if needed






