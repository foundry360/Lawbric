"""
User management endpoints (admin only) - PostgreSQL
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Tuple

from app.core.database import get_db
from app.core.auth import get_current_user_and_tenant
from app.core.security import get_password_hash
from app.models.user import User, UserRole
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "user"  # admin or user
    title: str  # attorney, paralegal, finance, etc. (job title - required for access control)


class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    title: Optional[str] = None  # Optional for updates, but if provided must be valid
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    role: str  # super_admin, admin, user
    title: str  # attorney, paralegal, finance, etc. (job title - required for access control)
    is_active: bool
    tenant_id: int

    class Config:
        from_attributes = True


async def verify_admin_user(
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant),
    db: Session = Depends(get_db)
) -> Tuple[int, int]:
    """Verify user is an admin (admin or super_admin)"""
    user_id, tenant_id = user_tenant
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is admin or super_admin
    if user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    return (user_id, tenant_id)


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    user_tenant: Tuple[int, int] = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """List all users in the current tenant (admin only)"""
    user_id, tenant_id = user_tenant
    
    try:
        # Get all users in the same tenant
        users = db.query(User).filter(User.tenant_id == tenant_id).all()
        
        return [
            UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                title=user.title,
                is_active=user.is_active,
                tenant_id=user.tenant_id
            )
            for user in users
        ]
    except Exception as e:
        logger.error(f"Error listing users: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: CreateUserRequest,
    user_tenant: Tuple[int, int] = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new user in the current tenant (admin only)"""
    user_id, tenant_id = user_tenant
    
    logger.info(f"Creating user: email={user_data.email}, role={user_data.role}, title={user_data.title}")
    
    # Validate role
    valid_roles = ['admin', 'user']
    if user_data.role not in valid_roles:
        error_msg = f"Invalid role '{user_data.role}'. Must be one of: {valid_roles}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Validate title (required for access control)
    valid_titles = ['attorney', 'paralegal', 'finance', 'legal_assistant', 'case_manager', 'legal_secretary']
    if not user_data.title or user_data.title not in valid_titles:
        error_msg = f"Invalid title '{user_data.title}'. Must be one of: {valid_titles}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    try:
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Create user in PostgreSQL
        new_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name or user_data.email.split('@')[0],
            role=user_data.role,
            title=user_data.title,
            tenant_id=tenant_id,  # Users belong to the same tenant as the admin
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"User created: {new_user.id} ({new_user.email}) in tenant {tenant_id} by admin {user_id}")
        
        return UserResponse(
            id=new_user.id,
            email=new_user.email,
            full_name=new_user.full_name,
            role=new_user.role,
            title=new_user.title,
            is_active=new_user.is_active,
            tenant_id=new_user.tenant_id
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UpdateUserRequest,
    user_tenant: Tuple[int, int] = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """Update a user (admin only)"""
    admin_id, tenant_id = user_tenant
    
    # Prevent updating yourself (for now, allow it but could restrict certain fields)
    # Get the user to update
    user = db.query(User).filter(User.id == user_id, User.tenant_id == tenant_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent changing super_admin role (only super_admins can manage super_admins)
    admin_user = db.query(User).filter(User.id == admin_id).first()
    if user.role == UserRole.SUPER_ADMIN and admin_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Cannot modify super admin users"
        )
    
    try:
        # Update fields
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        if user_data.role is not None:
            # Validate role
            valid_roles = ['admin', 'user']
            if user_data.role not in valid_roles:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role. Must be one of: {valid_roles}"
                )
            user.role = user_data.role
        if user_data.title is not None:
            # Validate title
            valid_titles = ['attorney', 'paralegal', 'finance', 'legal_assistant', 'case_manager', 'legal_secretary']
            if user_data.title not in valid_titles:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid title. Must be one of: {valid_titles}"
                )
            user.title = user_data.title
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"User updated: {user.id} ({user.email}) by admin {admin_id}")
        
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            title=user.title,
            is_active=user.is_active,
            tenant_id=user.tenant_id
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    user_tenant: Tuple[int, int] = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a user (admin only)"""
    admin_id, tenant_id = user_tenant
    
    # Prevent deleting yourself
    if user_id == admin_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Get the user to delete
    user = db.query(User).filter(User.id == user_id, User.tenant_id == tenant_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting super_admin (only super_admins can delete super_admins)
    admin_user = db.query(User).filter(User.id == admin_id).first()
    if user.role == UserRole.SUPER_ADMIN and admin_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Cannot delete super admin users"
        )
    
    try:
        db.delete(user)
        db.commit()
        
        logger.info(f"User deleted: {user_id} by admin {admin_id}")
        
        return {"message": "User deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.patch("/users/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: int,
    user_tenant: Tuple[int, int] = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """Deactivate a user (admin only)"""
    admin_id, tenant_id = user_tenant
    
    # Prevent deactivating yourself
    if user_id == admin_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    # Get the user to deactivate
    user = db.query(User).filter(User.id == user_id, User.tenant_id == tenant_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        user.is_active = False
        db.commit()
        db.refresh(user)
        
        logger.info(f"User deactivated: {user_id} by admin {admin_id}")
        
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            title=user.title,
            is_active=user.is_active,
            tenant_id=user.tenant_id
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error deactivating user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate user: {str(e)}"
        )
