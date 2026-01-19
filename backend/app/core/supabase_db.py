"""
Supabase database helper functions for user management
"""

from typing import Optional, List, Dict, Any
from app.core.supabase import get_supabase_client
from uuid import UUID

def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user profile from Supabase"""
    supabase = get_supabase_client()
    if not supabase:
        return None
    
    try:
        response = supabase.table('profiles').select('*').eq('id', user_id).single().execute()
        return response.data if response.data else None
    except Exception as e:
        print(f"Error fetching user profile: {e}")
        return None


def get_user_profile_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user profile by email from Supabase"""
    supabase = get_supabase_client()
    if not supabase:
        return None
    
    try:
        response = supabase.table('profiles').select('*').eq('email', email).single().execute()
        return response.data if response.data else None
    except Exception as e:
        print(f"Error fetching user profile by email: {e}")
        return None


def list_all_profiles() -> List[Dict[str, Any]]:
    """List all user profiles (admin only)"""
    supabase = get_supabase_client()
    if not supabase:
        return []
    
    try:
        response = supabase.table('profiles').select('*').order('created_at', desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error listing profiles: {e}")
        return []


def create_profile(user_id: str, email: str, full_name: Optional[str] = None, role: str = 'user', title: str = 'attorney') -> Optional[Dict[str, Any]]:
    """Create a user profile in Supabase"""
    supabase = get_supabase_client()
    if not supabase:
        return None
    
    try:
        profile_data = {
            'id': user_id,
            'email': email,
            'full_name': full_name,
            'role': role,
            'title': title,
            'is_active': True
        }
        response = supabase.table('profiles').insert(profile_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error creating profile: {e}")
        return None


def update_profile(user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update a user profile in Supabase"""
    supabase = get_supabase_client()
    if not supabase:
        return None
    
    try:
        response = supabase.table('profiles').update(updates).eq('id', user_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error updating profile: {e}")
        return None


def delete_profile(user_id: str) -> bool:
    """Delete a user profile from Supabase"""
    supabase = get_supabase_client()
    if not supabase:
        return False
    
    try:
        # Delete from auth.users (this will cascade delete profile via CASCADE constraint)
        response = supabase.auth.admin.delete_user(user_id)
        return True
    except Exception as e:
        print(f"Error deleting profile: {e}")
        # Try to delete profile directly if auth delete fails
        try:
            supabase.table('profiles').delete().eq('id', user_id).execute()
            return True
        except:
            return False


def check_user_is_admin(user_id: str) -> bool:
    """Check if user is admin"""
    profile = get_user_profile(user_id)
    return profile is not None and profile.get('role') == 'admin'

