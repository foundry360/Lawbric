"""
User management endpoints (admin only) - Supabase only
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from app.core.supabase import get_supabase_client
from app.core.supabase_db import (
    get_user_profile,
    list_all_profiles,
    create_profile,
    update_profile,
    delete_profile,
    check_user_is_admin
)

router = APIRouter()
security = HTTPBearer()


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "user"  # user or admin (permissions)
    title: str = "attorney"  # attorney, paralegal, finance, admin, user (job title)


class UserResponse(BaseModel):
    id: str  # UUID from Supabase
    email: str
    full_name: Optional[str]
    role: str  # user or admin (permissions)
    title: Optional[str]  # attorney, paralegal, finance, etc. (job title)
    is_active: bool


def verify_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify user is an admin using Supabase"""
    token = credentials.credentials
    supabase = get_supabase_client()
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        # Verify token with Supabase
        response = supabase.auth.get_user(token)
        if not response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = response.user.id
        
        # Check if user is admin
        if not check_user_is_admin(user_id):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        return {
            'id': user_id,
            'email': response.user.email,
            'user': response.user
        }
    except Exception as e:
        print(f"Error verifying admin: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: CreateUserRequest,
    admin: dict = Depends(verify_admin_user)
):
    """Create a new user (admin only)"""
    supabase = get_supabase_client()
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    # Validate role (permissions)
    valid_roles = ['user', 'admin']
    if user_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {valid_roles}"
        )
    
    # Validate title (job title)
    valid_titles = ['attorney', 'paralegal', 'finance', 'admin', 'user']
    if user_data.title not in valid_titles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid title. Must be one of: {valid_titles}"
        )
    
    # Check if user already exists
    existing_profile = supabase.table('profiles').select('*').eq('email', user_data.email).execute()
    if existing_profile.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    try:
        # Create user in Supabase auth
        auth_response = supabase.auth.admin.create_user({
                "email": user_data.email,
                "password": user_data.password,
                "email_confirm": True,  # Skip email confirmation
                "user_metadata": {
                    "role": user_data.role,
                    "title": user_data.title,
                    "full_name": user_data.full_name or user_data.email.split('@')[0]
                }
            })
        
        if not auth_response.user:
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        user_id = auth_response.user.id
        
        # Profile is created automatically by trigger, but update it with role and title
        # The trigger might not set role/title correctly, so update it
        profile_updates = {
            'role': user_data.role,
            'title': user_data.title,
            'full_name': user_data.full_name
        }
        
        # Wait a moment for trigger to complete, then update profile
        import time
        time.sleep(0.1)
        
        updated_profile = update_profile(user_id, profile_updates)
        
        if not updated_profile:
            # Try to create profile manually if trigger didn't work
            create_profile(user_id, user_data.email, user_data.full_name, user_data.role, user_data.title)
            profile = get_user_profile(user_id)
            # Update with title if profile was created
            if profile:
                update_profile(user_id, {'title': user_data.title})
                profile = get_user_profile(user_id)
        else:
            profile = updated_profile
        
        if not profile:
            raise HTTPException(status_code=500, detail="Failed to create user profile")
        
        return {
            "id": profile['id'],
            "email": profile['email'],
            "full_name": profile.get('full_name'),
            "role": profile.get('role', user_data.role),
            "title": profile.get('title', user_data.title),
            "is_active": profile.get('is_active', True)
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    admin: dict = Depends(verify_admin_user)
):
    """List all users (admin only)"""
    try:
        profiles = list_all_profiles()
        return [
            {
                "id": profile['id'],
                "email": profile['email'],
                "full_name": profile.get('full_name'),
                "role": profile.get('role', 'user'),
                "title": profile.get('title', 'attorney'),
                "is_active": profile.get('is_active', True)
            }
            for profile in profiles
        ]
    except Exception as e:
        print(f"Error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: dict = Depends(verify_admin_user)
):
    """Delete a user (admin only)"""
    # Prevent deleting yourself
    if user_id == admin['id']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    try:
        success = delete_profile(user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    admin: dict = Depends(verify_admin_user)
):
    """Deactivate a user (admin only)"""
    # Prevent deactivating yourself
    if user_id == admin['id']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    try:
        updated_profile = update_profile(user_id, {'is_active': False})
        if not updated_profile:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "id": updated_profile['id'],
            "email": updated_profile['email'],
            "full_name": updated_profile.get('full_name'),
            "role": updated_profile.get('role', 'user'),
            "title": updated_profile.get('title', 'attorney'),
            "is_active": updated_profile.get('is_active', False)
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deactivating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate user: {str(e)}"
        )
