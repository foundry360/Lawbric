-- Create storage bucket policies for profile-avatars
-- This allows authenticated users to upload and manage their own avatars
-- Files are stored as: {user_id}-{timestamp}.{ext} in the bucket root

-- First, ensure the bucket exists and is public
-- Note: This should already be created in Supabase dashboard
-- If the bucket doesn't exist, create it via Supabase dashboard first:
-- Storage > New bucket > Name: profile-avatars > Public: Yes

-- Policy: Allow authenticated users to upload files
-- Users can upload files with their own user ID in the filename
-- Filename format: {user_id}-{timestamp}.{ext}
CREATE POLICY "Users can upload own avatar"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'profile-avatars'
  AND auth.uid()::text = split_part(name, '-', 1)  -- Filename starts with user ID
);

-- Policy: Allow authenticated users to update their own files
CREATE POLICY "Users can update own avatar"
ON storage.objects
FOR UPDATE
TO authenticated
USING (
  bucket_id = 'profile-avatars'
  AND auth.uid()::text = split_part(name, '-', 1)  -- Filename starts with user ID
)
WITH CHECK (
  bucket_id = 'profile-avatars'
  AND auth.uid()::text = split_part(name, '-', 1)  -- Filename starts with user ID
);

-- Policy: Allow authenticated users to delete their own files
CREATE POLICY "Users can delete own avatar"
ON storage.objects
FOR DELETE
TO authenticated
USING (
  bucket_id = 'profile-avatars'
  AND auth.uid()::text = split_part(name, '-', 1)  -- Filename starts with user ID
);

-- Policy: Allow public read access (since avatars are public)
CREATE POLICY "Public can view avatars"
ON storage.objects
FOR SELECT
TO public
USING (bucket_id = 'profile-avatars');

