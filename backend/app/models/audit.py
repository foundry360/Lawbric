"""
Audit log model for compliance and security tracking
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
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


