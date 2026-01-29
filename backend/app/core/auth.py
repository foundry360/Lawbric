"""
Authentication dependencies with multi-tenant support - Pure JWT
"""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Tuple

from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User, UserRole

import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def get_current_user_and_tenant(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Tuple[int, int]:
    """
    Get current user ID and tenant ID from JWT token.
    Returns (user_id, tenant_id) tuple.
    """
    token = credentials.credentials
    
    # Verify JWT token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # sub is stored as string in JWT, convert to int
    user_id = int(payload.get("sub"))
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")
    
    if not user.tenant_id:
        raise HTTPException(
            status_code=403,
            detail="User is not associated with a tenant"
        )
    
    return (user.id, user.tenant_id)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> int:
    """Get current user ID from token (backward compatibility)"""
    user_id, _ = await get_current_user_and_tenant(credentials, db)
    return user_id


async def get_current_tenant_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> int:
    """Get current tenant ID from token"""
    _, tenant_id = await get_current_user_and_tenant(credentials, db)
    return tenant_id


async def get_super_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Tuple[int, int]:
    """Get current user and verify they are a super admin (Lawbric employee)"""
    user_id, tenant_id = await get_current_user_and_tenant(credentials, db)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is super admin (Lawbric employee)
    if user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Super admin access required (Lawbric employees only)"
        )
    
    return (user_id, tenant_id)
