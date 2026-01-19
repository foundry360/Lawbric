# Supabase Setup Guide

This application uses Supabase as the single source of truth for all user data and authentication.

## Prerequisites

1. Create a Supabase project at https://supabase.com
2. Get your Supabase URL and API keys from the project settings

## Database Setup

### 1. Create the Profiles Table

Run the migration file to create the profiles table and set up Row Level Security:

```sql
-- Run this in Supabase SQL Editor
-- File: backend/supabase/migrations/001_create_profiles_table.sql
```

This migration will:
- Create a `profiles` table that extends `auth.users`
- Set up Row Level Security (RLS) policies
- Create triggers to automatically create profiles when users are created
- Set up automatic `updated_at` timestamp updates

### 2. Environment Variables

Add these to your `.env` files:

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

1. Go to Authentication > Settings in Supabase Dashboard
2. Disable "Enable email confirmations"
3. This allows users to log in immediately after creation

## Initial Admin User

The first admin user should be created through one of these methods:

### Option 1: Via Supabase Dashboard
1. Go to Authentication > Users in Supabase Dashboard
2. Click "Add User" > "Create new user"
3. Enter email and password
4. In User Metadata, add:
   ```json
   {
     "role": "admin",
     "full_name": "Admin User"
   }
   ```
5. The profile will be created automatically by the trigger

### Option 2: Via Supabase SQL
```sql
-- First create the user (you'll need to set a password hash)
-- Or use the dashboard to create the user, then run:
UPDATE public.profiles
SET role = 'admin'
WHERE email = 'admin@lawfirm.com';
```

### Option 3: Via Backend API (if you have service role access)
Use the user management API once you have one admin user created.

## Architecture

### Authentication Flow
1. Frontend uses Supabase Auth for login/logout
2. Backend verifies Supabase JWT tokens
3. User data is stored in `auth.users` and `public.profiles`

### User Management
- All user operations go through Supabase
- Admin users can create/manage users via the Settings page
- User profiles are automatically created via database trigger

## Tables

### `auth.users` (Built-in)
- Managed by Supabase Auth
- Contains: id, email, encrypted_password, user_metadata
- Automatically created when users sign up

### `public.profiles`
- Extends `auth.users` with application-specific data
- Contains: id (references auth.users), email, full_name, role, is_active
- Automatically created via trigger when user is created in auth.users

## Security

- Row Level Security (RLS) is enabled on profiles table
- Users can only view their own profile
- Only admins can view/modify all profiles
- All operations use Supabase service role key on the backend
