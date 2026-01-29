"""
User model for authentication and authorization
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class UserRole(str, enum.Enum):
    """User roles"""
    SUPER_ADMIN = "super_admin"  # Lawbric employees - internal admin portal access
    ADMIN = "admin"  # Client admins - manage their own tenant
    USER = "user"  # Regular users


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String(20), default=UserRole.USER.value, nullable=False)
    title = Column(String(50), nullable=False, default='attorney')  # Job title: attorney, paralegal, finance, legal_assistant, etc. (required for access control)
    is_active = Column(Boolean, default=True)
    
    # Multi-tenant: User belongs to a tenant
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")






