"""
Client onboarding endpoints for Lawbric super admins
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.auth import get_super_admin
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.models.case import Case
from app.core.security import get_password_hash
from app.schemas.tenant import TenantCreate
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class ClientOnboardingRequest(BaseModel):
    tenant: TenantCreate
    admin_email: EmailStr
    admin_password: str
    admin_full_name: Optional[str] = None


class ClientOnboardingResponse(BaseModel):
    tenant_id: int
    tenant_slug: str
    admin_user_id: int  # User ID from PostgreSQL
    admin_email: str
    message: str


@router.post("/clients", response_model=ClientOnboardingResponse)
async def onboard_client(
    request: ClientOnboardingRequest,
    db: Session = Depends(get_db),
    super_admin: tuple = Depends(get_super_admin)
):
    """Onboard a new client: create tenant + admin user (super admin only)"""
    user_id, _ = super_admin
    
    # Step 1: Create tenant
    try:
        # Validate slug
        import re
        if not re.match(r'^[a-z0-9_-]+$', request.tenant.slug):
            raise HTTPException(
                status_code=400,
                detail="Slug must contain only lowercase letters, numbers, hyphens, and underscores"
            )
        
        # Check if tenant already exists
        existing_tenant = db.query(Tenant).filter(Tenant.slug == request.tenant.slug).first()
        if existing_tenant:
            raise HTTPException(
                status_code=400,
                detail=f"Tenant with slug '{request.tenant.slug}' already exists"
            )
        
        tenant = Tenant(
            name=request.tenant.name,
            slug=request.tenant.slug,
            description=request.tenant.description,
            domain=request.tenant.domain,
            logo_url=request.tenant.logo_url
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        logger.info(f"Tenant created: {tenant.id} ({tenant.slug}) by super admin {user_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating tenant: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create tenant: {str(e)}")
    
    # Step 2: Create admin user in PostgreSQL
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == request.admin_email).first()
        if existing_user:
            # Rollback tenant creation
            db.delete(tenant)
            db.commit()
            raise HTTPException(
                status_code=400,
                detail="User with this email already exists"
            )
        
        # Hash password
        hashed_password = get_password_hash(request.admin_password)
        
        # Create admin user with ADMIN role so they can manage other users
        admin_user = User(
            email=request.admin_email,
            hashed_password=hashed_password,
            full_name=request.admin_full_name or request.admin_email.split('@')[0],
            role=UserRole.ADMIN,  # Admin role - allows them to add/manage other users
            tenant_id=tenant.id,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        logger.info(f"Admin user created: {admin_user.id} ({admin_user.email}) for tenant {tenant.id} with role {admin_user.role}")
        
    except HTTPException:
        # Rollback tenant if user creation failed
        db.delete(tenant)
        db.commit()
        raise
    except Exception as e:
        # Rollback tenant if user creation failed
        db.delete(tenant)
        db.commit()
        logger.error(f"Error creating admin user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create admin user: {str(e)}")
    
    return ClientOnboardingResponse(
        tenant_id=tenant.id,
        tenant_slug=tenant.slug,
        admin_user_id=admin_user.id,
        admin_email=request.admin_email,
        message=f"Client '{tenant.name}' onboarded successfully. Admin user: {request.admin_email}"
    )


@router.get("/clients")
async def list_clients(
    db: Session = Depends(get_db),
    super_admin: tuple = Depends(get_super_admin),
    skip: int = 0,
    limit: int = 100
):
    """List all clients/tenants (super admin only)"""
    tenants = db.query(Tenant).filter(
        Tenant.is_active == True
    ).offset(skip).limit(limit).all()
    
    # Get user counts for each tenant
    result = []
    for tenant in tenants:
        user_count = db.query(User).filter(User.tenant_id == tenant.id).count()
        case_count = db.query(Case).filter(Case.tenant_id == tenant.id).count()
        
        result.append({
            "id": tenant.id,
            "name": tenant.name,
            "slug": tenant.slug,
            "description": tenant.description,
            "domain": tenant.domain,
            "is_active": tenant.is_active,
            "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
            "user_count": user_count,
            "case_count": case_count
        })
    
    return result

