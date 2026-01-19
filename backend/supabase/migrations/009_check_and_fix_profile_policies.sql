-- Fix profile UPDATE policies - ensure users can update their own profiles
-- This drops all conflicting UPDATE policies and creates a clean one

-- Drop ALL existing UPDATE policies to start clean
DROP POLICY IF EXISTS "Admins can update profiles" ON public.profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can update their own profile" ON public.profiles;

-- Enable RLS if not already enabled
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Create a simple UPDATE policy that allows users to update their own profile
-- USING: checks if you can see the row (auth.uid() must match the id)
-- WITH CHECK: checks if the update is allowed (same condition)
CREATE POLICY "Users can update own profile"
  ON public.profiles
  FOR UPDATE
  TO authenticated
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- Optional: Also allow admins to update any profile via JWT metadata
-- Uncomment if needed:
-- CREATE POLICY "Admins can update any profile"
--   ON public.profiles
--   FOR UPDATE
--   TO authenticated
--   USING (
--     auth.uid() = id
--     OR (auth.jwt() -> 'user_metadata' ->> 'role') = 'admin'
--     OR (auth.jwt() -> 'raw_user_meta_data' ->> 'role') = 'admin'
--   )
--   WITH CHECK (
--     auth.uid() = id
--     OR (auth.jwt() -> 'user_metadata' ->> 'role') = 'admin'
--     OR (auth.jwt() -> 'raw_user_meta_data' ->> 'role') = 'admin'
--   );

