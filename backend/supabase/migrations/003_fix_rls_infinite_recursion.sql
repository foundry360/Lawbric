-- Fix infinite recursion in RLS policies
-- The issue is that admin policies query the profiles table,
-- which triggers the policy check again, causing infinite recursion.

-- Drop the problematic policies that cause recursion
DROP POLICY IF EXISTS "Admins can view all profiles" ON public.profiles;
DROP POLICY IF EXISTS "Admins can insert profiles" ON public.profiles;
DROP POLICY IF EXISTS "Admins can update profiles" ON public.profiles;
DROP POLICY IF EXISTS "Admins can delete profiles" ON public.profiles;

-- Create fixed policies that check admin role from user_metadata (avoids recursion)
-- This works because user_metadata is stored in auth.users, not profiles table

CREATE POLICY "Admins can view all profiles"
  ON public.profiles
  FOR SELECT
  USING (
    -- Users can always view their own profile
    auth.uid() = id
    OR
    -- Admins can view all profiles (check metadata, not profiles table)
    (
      (auth.jwt() -> 'user_metadata' ->> 'role') = 'admin'
      OR
      (auth.jwt() -> 'raw_user_meta_data' ->> 'role') = 'admin'
    )
  );

CREATE POLICY "Admins can insert profiles"
  ON public.profiles
  FOR INSERT
  WITH CHECK (
    (auth.jwt() -> 'user_metadata' ->> 'role') = 'admin'
    OR
    (auth.jwt() -> 'raw_user_meta_data' ->> 'role') = 'admin'
  );

CREATE POLICY "Admins can update profiles"
  ON public.profiles
  FOR UPDATE
  USING (
    auth.uid() = id
    OR
    (
      (auth.jwt() -> 'user_metadata' ->> 'role') = 'admin'
      OR
      (auth.jwt() -> 'raw_user_meta_data' ->> 'role') = 'admin'
    )
  );

CREATE POLICY "Admins can delete profiles"
  ON public.profiles
  FOR DELETE
  USING (
    (auth.jwt() -> 'user_metadata' ->> 'role') = 'admin'
    OR
    (auth.jwt() -> 'raw_user_meta_data' ->> 'role') = 'admin'
  );

