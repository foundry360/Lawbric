# Avatar Upload Setup

## Migration Required

Run this SQL in Supabase SQL Editor:

```sql
-- Add avatar_url column to profiles table
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS avatar_url TEXT;
```

Or run the migration file: `backend/supabase/migrations/004_add_avatar_url.sql`

## Storage Bucket Setup

The `profile-avatars` bucket should already be created. Make sure:

1. **Bucket is public** (or policies allow read access)
   - Go to Storage → profile-avatars → Policies
   - Add policy: "Anyone can view avatars" with SELECT permission

2. **Users can upload their own avatars**
   - Add policy: "Users can upload own avatar" with INSERT permission
   - Using: `bucket_id = 'profile-avatars' AND (storage.foldername(name))[1] = auth.uid()::text`

Or simpler (if bucket is public):
- Public bucket with INSERT policy for authenticated users

## Features Added

1. **Avatar Upload UI** in Settings → Account tab
   - Shows current avatar or initials
   - Upload button to select image
   - Remove button to delete avatar
   - Preview while uploading

2. **Avatar Display**
   - Settings page shows avatar
   - Dashboard header shows avatar (replaces initials)

3. **Validation**
   - Image files only (JPG, PNG, GIF)
   - Max file size: 2MB
   - File naming: `{user_id}-{timestamp}.{ext}`

## Testing

1. Run the migration
2. Go to Settings → Account tab
3. Click "Upload" to select an image
4. Avatar should appear immediately
5. Check dashboard header - should show avatar instead of initials



