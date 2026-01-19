-- Add title column to profiles table
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS title TEXT DEFAULT 'attorney';

-- Update existing role constraint (remove old one, add new one)
-- First, we need to update existing roles to be 'user' or 'admin'
UPDATE public.profiles
SET role = CASE
  WHEN role = 'admin' THEN 'admin'
  ELSE 'user'
END
WHERE role NOT IN ('user', 'admin');

-- Add constraint for role (user or admin only)
ALTER TABLE public.profiles
DROP CONSTRAINT IF EXISTS profiles_role_check;

ALTER TABLE public.profiles
ADD CONSTRAINT profiles_role_check 
CHECK (role IN ('user', 'admin'));

-- Add constraint for title
ALTER TABLE public.profiles
DROP CONSTRAINT IF EXISTS profiles_title_check;

ALTER TABLE public.profiles
ADD CONSTRAINT profiles_title_check 
CHECK (title IN ('attorney', 'paralegal', 'finance', 'admin', 'user'));

-- Set default title for existing users based on their old role
UPDATE public.profiles
SET title = CASE
  WHEN title IS NULL OR title = '' THEN
    CASE
      WHEN role = 'admin' THEN 'admin'
      ELSE 'attorney'
    END
  ELSE title
END
WHERE title IS NULL OR title = '';

-- Update the trigger function to include title
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name, role, title)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1)),
    COALESCE(NEW.raw_user_meta_data->>'role', 'user'),
    COALESCE(NEW.raw_user_meta_data->>'title', 'attorney')
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

