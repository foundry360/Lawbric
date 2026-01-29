"""
Tenant management endpoints for multi-tenant architecture
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import re

from app.core.database import get_db
from app.core.auth import get_current_user_and_tenant
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.tenant import TenantCreate, TenantResponse, TenantUpdate
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


def validate_slug(slug: str) -> bool:
    """Validate tenant slug format (alphanumeric, hyphens, underscores only)"""
    return bool(re.match(r'^[a-z0-9_-]+$', slug))


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    db: Session = Depends(get_db),
    user_tenant: tuple = Depends(get_current_user_and_tenant)
):
    """Create a new tenant (only admins can create tenants)"""
    user_id, current_tenant_id = user_tenant
    
    # Check if user is admin
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.role.value != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only administrators can create tenants"
        )
    
    # Validate slug
    if not validate_slug(tenant_data.slug):
        raise HTTPException(
            status_code=400,
            detail="Slug must contain only lowercase letters, numbers, hyphens, and underscores"
        )
    
    # Check if slug already exists
    existing = db.query(Tenant).filter(Tenant.slug == tenant_data.slug).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Tenant with this slug already exists"
        )
    
    # Create tenant
    tenant = Tenant(
        name=tenant_data.name,
        slug=tenant_data.slug,
        description=tenant_data.description,
        domain=tenant_data.domain,
        logo_url=tenant_data.logo_url
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    
    logger.info(f"Tenant created: {tenant.id} ({tenant.slug}) by user {user_id}")
    return tenant


@router.get("", response_model=List[TenantResponse])
async def list_tenants(
    db: Session = Depends(get_db),
    user_tenant: tuple = Depends(get_current_user_and_tenant),
    skip: int = 0,
    limit: int = 100
):
    """List all tenants (only admins)"""
    user_id, current_tenant_id = user_tenant
    
    # Check if user is admin
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.role.value != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only administrators can list tenants"
        )
    
    tenants = db.query(Tenant).filter(
        Tenant.is_active == True
    ).offset(skip).limit(limit).all()
    return tenants


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    user_tenant: tuple = Depends(get_current_user_and_tenant)
):
    """Get a specific tenant (users can only view their own tenant, admins can view any)"""
    user_id, current_tenant_id = user_tenant
    
    # Check if user is admin or viewing their own tenant
    user = db.query(User).filter(User.id == user_id).first()
    is_admin = user and user.role.value == "admin"
    
    if not is_admin and tenant_id != current_tenant_id:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own tenant"
        )
    
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return tenant


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: int,
    tenant_data: TenantUpdate,
    db: Session = Depends(get_db),
    user_tenant: tuple = Depends(get_current_user_and_tenant)
):
    """Update a tenant (only admins)"""
    user_id, current_tenant_id = user_tenant
    
    # Check if user is admin
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.role.value != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only administrators can update tenants"
        )
    
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Validate slug if provided
    if tenant_data.slug and not validate_slug(tenant_data.slug):
        raise HTTPException(
            status_code=400,
            detail="Slug must contain only lowercase letters, numbers, hyphens, and underscores"
        )
    
    # Check slug uniqueness if changing
    if tenant_data.slug and tenant_data.slug != tenant.slug:
        existing = db.query(Tenant).filter(Tenant.slug == tenant_data.slug).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Tenant with this slug already exists"
            )
    
    update_data = tenant_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)
    
    db.commit()
    db.refresh(tenant)
    return tenant


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    user_tenant: tuple = Depends(get_current_user_and_tenant)
):
    """Delete (deactivate) a tenant (only admins)"""
    user_id, current_tenant_id = user_tenant
    
    # Check if user is admin
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.role.value != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only administrators can delete tenants"
        )
    
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    tenant.is_active = False
    db.commit()
    return None



