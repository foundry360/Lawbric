# Migration to Supabase-Only Architecture

This document outlines the changes made to remove the local database and use Supabase exclusively.

## Summary

The application has been refactored to use Supabase as the single source of truth for all user data and authentication. The local database `users` table has been removed.

## Changes Made

### Backend Changes

1. **New Supabase Database Helper** (`backend/app/core/supabase_db.py`)
   - Helper functions for managing user profiles in Supabase
   - Functions: `get_user_profile`, `list_all_profiles`, `create_profile`, `update_profile`, `delete_profile`, `check_user_is_admin`

2. **Updated User Management API** (`backend/app/api/v1/users.py`)
   - Removed all SQLAlchemy/database dependencies
   - Now uses Supabase exclusively for user management
   - Uses Supabase auth tokens for authentication
   - Returns UUID strings (Supabase user IDs) instead of integers

3. **Updated Authentication API** (`backend/app/api/v1/auth.py`)
   - Removed login endpoint (handled by Supabase on frontend)
   - `/me` endpoint now uses Supabase tokens
   - Verifies Supabase JWT tokens

4. **Supabase Migration** (`backend/supabase/migrations/001_create_profiles_table.sql`)
   - Creates `profiles` table that extends `auth.users`
   - Sets up Row Level Security (RLS) policies
   - Creates triggers for automatic profile creation
   - Sets up automatic `updated_at` timestamp

### Frontend Changes

1. **Updated Auth Context** (`frontend/lib/auth.tsx`)
   - Now stores Supabase access tokens (not user IDs)
   - Uses Supabase session tokens for API authentication
   - Removed legacy backend auth fallback (optional)

2. **Updated API Client** (`frontend/lib/api.ts`)
   - Updated `AppUser` interface to use `string` ID (UUID) instead of `number`
   - Token interceptor now sends Supabase JWT tokens

3. **Updated Settings Page** (`frontend/app/dashboard/settings/page.tsx`)
   - Updated to use string IDs instead of numbers
   - Works with Supabase-only backend

### Database Schema

**Supabase `public.profiles` Table:**
```sql
CREATE TABLE public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  email TEXT UNIQUE NOT NULL,
  full_name TEXT,
  role TEXT NOT NULL DEFAULT 'user',
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE,
  updated_at TIMESTAMP WITH TIME ZONE
);
```

## Setup Instructions

### 1. Run Database Migration

Execute the migration file in Supabase SQL Editor:
- File: `backend/supabase/migrations/001_create_profiles_table.sql`

### 2. Update Environment Variables

**Backend `.env`:**
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
```

**Frontend `.env.local`:**
```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

### 3. Disable Email Confirmation

In Supabase Dashboard:
1. Go to Authentication > Settings
2. Disable "Enable email confirmations"

### 4. Create Initial Admin User

Create the first admin user via:
- Supabase Dashboard (Authentication > Users)
- Or via SQL (update profile role to 'admin')

## Breaking Changes

1. **User IDs are now UUIDs (strings)** instead of integers
2. **Authentication is handled entirely by Supabase** on the frontend
3. **No local database users table** - all user data is in Supabase
4. **Backend login endpoint removed** - use Supabase auth directly

## Notes

- The local database (`legalai.db`) is still used for cases, documents, queries, etc.
- Only user management has been moved to Supabase
- Row Level Security (RLS) is enabled on the profiles table
- Service role key is required for backend operations (bypasses RLS)

## Testing

1. Verify Supabase connection
2. Create an admin user
3. Test login with Supabase auth
4. Test user management in Settings page
5. Verify all API calls use Supabase tokens

