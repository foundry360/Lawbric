# Update Existing Users: Role vs Title

After running the migration, you need to update existing users in your Supabase database.

## SQL to Update Existing Users

Run this in Supabase SQL Editor:

```sql
-- First, add the title column if it doesn't exist (should be done by migration)
-- This is just a safety check
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS title TEXT DEFAULT 'attorney' 
CHECK (title IN ('attorney', 'paralegal', 'finance', 'admin', 'user'));

-- Update existing users:
-- Set title based on current role, then fix role to be 'user' or 'admin'
UPDATE public.profiles
SET 
  title = CASE 
    WHEN role = 'attorney' THEN 'attorney'
    WHEN role = 'paralegal' THEN 'paralegal'
    WHEN role = 'finance' THEN 'finance'
    WHEN role = 'admin' THEN 'admin'
    ELSE 'attorney'  -- Default for any other value
  END,
  role = CASE
    WHEN role = 'admin' THEN 'admin'
    ELSE 'user'  -- Everyone else becomes 'user' role (permissions)
  END
WHERE title IS NULL OR title = '';
```

## Verify Changes

After running the update:

```sql
SELECT id, email, role, title, full_name 
FROM public.profiles 
ORDER BY created_at;
```

You should see:
- `role` is either 'user' or 'admin' (permissions)
- `title` is 'attorney', 'paralegal', 'finance', etc. (job title)



