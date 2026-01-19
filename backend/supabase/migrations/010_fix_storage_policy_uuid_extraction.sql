-- Fix storage policy to correctly extract UUID from filename
-- The issue: split_part(name, '-', 1) only gets the first segment of UUID
-- Filename format: {uuid}-{timestamp}.{ext}
-- UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx (36 chars)

-- Drop existing storage policies
DROP POLICY IF EXISTS "Users can upload own avatar" ON storage.objects;
DROP POLICY IF EXISTS "Users can update own avatar" ON storage.objects;
DROP POLICY IF EXISTS "Users can delete own avatar" ON storage.objects;

-- Policy: Allow authenticated users to upload files
-- Check if filename starts with auth.uid() followed by a dash
CREATE POLICY "Users can upload own avatar"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'profile-avatars'
  AND name LIKE auth.uid()::text || '-%'  -- Filename starts with user UUID followed by dash
);

-- Policy: Allow authenticated users to update their own files
CREATE POLICY "Users can update own avatar"
ON storage.objects
FOR UPDATE
TO authenticated
USING (
  bucket_id = 'profile-avatars'
  AND name LIKE auth.uid()::text || '-%'  -- Filename starts with user UUID followed by dash
)
WITH CHECK (
  bucket_id = 'profile-avatars'
  AND name LIKE auth.uid()::text || '-%'  -- Filename starts with user UUID followed by dash
);

-- Policy: Allow authenticated users to delete their own files
CREATE POLICY "Users can delete own avatar"
ON storage.objects
FOR DELETE
TO authenticated
USING (
  bucket_id = 'profile-avatars'
  AND name LIKE auth.uid()::text || '-%'  -- Filename starts with user UUID followed by dash
);

-- Keep public read policy (should already exist, but ensure it's there)
DROP POLICY IF EXISTS "Public can view avatars" ON storage.objects;
CREATE POLICY "Public can view avatars"
ON storage.objects
FOR SELECT
TO public
USING (bucket_id = 'profile-avatars');

