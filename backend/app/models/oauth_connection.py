"""
OAuth connection model for third-party integrations
"""

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class OAuthConnection(Base):
    """OAuth connection model for storing third-party integration tokens"""
    __tablename__ = "oauth_connections"
    
    id = Column(String, primary_key=True, index=True)  # UUID as string
    user_id = Column(String, ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False, index=True)  # UUID as string
    provider = Column(String, nullable=False, index=True)  # e.g., 'google_drive'
    access_token = Column(String, nullable=False)  # Encrypted
    refresh_token = Column(String, nullable=True)  # Encrypted
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    connected_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

