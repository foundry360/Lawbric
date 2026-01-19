-- Ensure profile UPDATE policy is correct (with WITH CHECK clause)
-- This migration ensures the policy exists correctly regardless of previous migrations

-- Drop any existing UPDATE policies to start fresh
DROP POLICY IF EXISTS "Admins can update profiles" ON public.profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;

-- Create the correct policy with both USING and WITH CHECK
CREATE POLICY "Users can update own profile"
  ON public.profiles
  FOR UPDATE
  USING (
    -- Users can update their own profile
    auth.uid() = id
    OR
    -- Admins can update any profile (check metadata to avoid recursion)
    (
      (auth.jwt() -> 'user_metadata' ->> 'role') = 'admin'
      OR
      (auth.jwt() -> 'raw_user_meta_data' ->> 'role') = 'admin'
    )
  )
  WITH CHECK (
    -- Same conditions for WITH CHECK (required for UPDATE operations)
    auth.uid() = id
    OR
    (
      (auth.jwt() -> 'user_metadata' ->> 'role') = 'admin'
      OR
      (auth.jwt() -> 'raw_user_meta_data' ->> 'role') = 'admin'
    )
  );


