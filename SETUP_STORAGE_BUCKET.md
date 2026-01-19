# Setup Storage Bucket for Profile Avatars

## Problem
You're getting RLS errors when trying to upload avatars because the storage bucket doesn't have policies configured.

## Solution

### Step 1: Verify the Bucket Exists

1. Go to your Supabase Dashboard
2. Navigate to **Storage**
3. Check if the bucket `profile-avatars` exists
4. If it doesn't exist:
   - Click **New bucket**
   - Name: `profile-avatars`
   - Set it as **Public** (checkbox)
   - Click **Create bucket**

### Step 2: Run the Storage Policies Migration

Run the SQL from `backend/supabase/migrations/007_create_storage_policies.sql` in the Supabase SQL Editor:

1. Go to **SQL Editor** in Supabase Dashboard
2. Click **New Query**
3. Copy and paste the entire contents of `backend/supabase/migrations/007_create_storage_policies.sql`
4. Click **Run** (or press Ctrl+Enter)

### Step 3: Verify Policies Were Created

After running the migration, check that the policies exist:

1. Go to **Storage** → **Policies** tab
2. Select the `profile-avatars` bucket
3. You should see these policies:
   - "Users can upload own avatar" (INSERT)
   - "Users can update own avatar" (UPDATE)
   - "Users can delete own avatar" (DELETE)
   - "Public can view avatars" (SELECT)

### What These Policies Do

- **INSERT**: Authenticated users can upload files with their user ID in the filename
- **UPDATE**: Users can update files with their user ID in the filename
- **DELETE**: Users can delete files with their user ID in the filename
- **SELECT**: Public read access so avatars can be displayed

The policies check that the filename starts with the user's ID (format: `{user_id}-{timestamp}.{ext}`).

