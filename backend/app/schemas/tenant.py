"""
Pydantic schemas for Tenant-related API requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TenantBase(BaseModel):
    """Base tenant schema"""
    name: str = Field(..., description="Tenant name")
    slug: str = Field(..., description="URL-friendly tenant identifier")
    description: Optional[str] = Field(None, description="Tenant description")
    domain: Optional[str] = Field(None, description="Optional domain for subdomain routing")
    logo_url: Optional[str] = Field(None, description="URL to tenant logo")


class TenantCreate(TenantBase):
    """Schema for creating a tenant"""
    pass


class TenantUpdate(BaseModel):
    """Schema for updating a tenant"""
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: Optional[bool] = None


class TenantResponse(TenantBase):
    """Schema for tenant response"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True



