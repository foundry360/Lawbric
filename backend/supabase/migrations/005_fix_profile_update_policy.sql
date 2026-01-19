-- Fix RLS policy to allow users to update their own profile
-- The UPDATE policy needs WITH CHECK clause for UPDATE operations

-- Drop existing "Admins can update profiles" policy from migration 003
DROP POLICY IF EXISTS "Admins can update profiles" ON public.profiles;

-- Create policy that allows users to update their own profile AND admins to update any profile
CREATE POLICY "Users can update own profile"
  ON public.profiles
  FOR UPDATE
  USING (
    -- Users can update their own profile
    auth.uid() = id
    OR
    -- Admins can update any profile (check metadata, not profiles table to avoid recursion)
    (
      (auth.jwt() -> 'user_metadata' ->> 'role') = 'admin'
      OR
      (auth.jwt() -> 'raw_user_meta_data' ->> 'role') = 'admin'
    )
  )
  WITH CHECK (
    -- Same conditions for WITH CHECK (required for UPDATE)
    auth.uid() = id
    OR
    (
      (auth.jwt() -> 'user_metadata' ->> 'role') = 'admin'
      OR
      (auth.jwt() -> 'raw_user_meta_data' ->> 'role') = 'admin'
    )
  );

