"""
Tenant/Organization model for multi-tenant architecture
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Tenant(Base):
    """Tenant/Organization model for multi-tenant isolation"""
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, index=True)
    slug = Column(String, unique=True, nullable=False, index=True)  # URL-friendly identifier
    description = Column(Text, nullable=True)
    
    # Organization details
    domain = Column(String, nullable=True, index=True)  # Optional domain for subdomain routing
    logo_url = Column(String, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="tenant")
    cases = relationship("Case", back_populates="tenant", cascade="all, delete-orphan")

