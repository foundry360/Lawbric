"""
Supabase client configuration for backend
"""

from supabase import create_client, Client
from app.core.config import settings

# Create Supabase client for backend operations
# Use service role key for server-side operations that bypass RLS
supabase: Client | None = None

if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY:
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
else:
    print("Warning: Supabase credentials not configured. Supabase features will be disabled.")


def get_supabase_client() -> Client | None:
    """Get Supabase client instance"""
    return supabase




