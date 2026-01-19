"""
Authentication endpoints - Supabase only
Note: Login is handled by Supabase on the frontend.
These endpoints are for user info retrieval using Supabase tokens.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.supabase import get_supabase_client
from app.core.supabase_db import get_user_profile

router = APIRouter()
security = HTTPBearer()


@router.get("/me")
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current user information from Supabase"""
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
        
        # Get user profile
        profile = get_user_profile(user_id)
        
        if not profile:
            # Return basic info from auth if profile doesn't exist
            return {
                "id": response.user.id,
                "email": response.user.email,
                "role": response.user.user_metadata.get('role', 'user'),
                "title": response.user.user_metadata.get('title', 'attorney'),
                "full_name": response.user.user_metadata.get('full_name'),
                "avatar_url": response.user.user_metadata.get('avatar_url')
            }
        
        return {
            "id": profile['id'],
            "email": profile['email'],
            "role": profile.get('role', 'user'),
            "title": profile.get('title', 'attorney'),
            "full_name": profile.get('full_name'),
            "avatar_url": profile.get('avatar_url')
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting user info: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
