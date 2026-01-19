-- Simplified profile UPDATE policy - more permissive to ensure it works
-- This policy allows users to update their own profile based on auth.uid()

-- Drop any existing UPDATE policies
DROP POLICY IF EXISTS "Admins can update profiles" ON public.profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;

-- Create a simple policy that allows users to update their own profile
-- The USING clause checks if the user can see the row
-- The WITH CHECK clause checks if the update is allowed
CREATE POLICY "Users can update own profile"
  ON public.profiles
  FOR UPDATE
  USING (
    -- Users can always update their own profile
    auth.uid() = id
  )
  WITH CHECK (
    -- Users can always update their own profile
    auth.uid() = id
  );

-- Also create a separate policy for admins (if needed later)
-- For now, we'll keep it simple and allow users to update their own profiles only

