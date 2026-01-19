-- Fix RLS policy to allow admins to list all profiles
-- Create a SECURITY DEFINER function to check admin status without recursion

-- Create a function that checks if the current user is an admin
-- This function bypasses RLS to avoid recursion
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN AS $$
DECLARE
  user_role TEXT;
BEGIN
  -- Get role from profiles table (bypasses RLS due to SECURITY DEFINER)
  SELECT role INTO user_role
  FROM public.profiles
  WHERE id = auth.uid();
  
  RETURN user_role = 'admin';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Update the "Admins can view all profiles" policy to use the function
DROP POLICY IF EXISTS "Admins can view all profiles" ON public.profiles;

CREATE POLICY "Admins can view all profiles"
  ON public.profiles
  FOR SELECT
  USING (
    -- Users can always view their own profile
    auth.uid() = id
    OR
    -- Admins can view all profiles (check via function to avoid recursion)
    public.is_admin()
  );

