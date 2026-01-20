# Role vs Title Separation

## Changes Made

We've separated **Role** (permissions) from **Title** (job position):

### Role (Permissions)
- **Values:** `user` or `admin`
- **Purpose:** Controls access level and permissions
- **Admin:** Can manage users, access User Management tab
- **User:** Standard access, cannot manage users

### Title (Job Title)
- **Values:** `attorney`, `paralegal`, `finance`, `admin`, `user`
- **Purpose:** Describes the person's job position/title
- **Display:** Shows in user profile, header, etc.
- **Not used for:** Access control or permissions

## Database Changes

The `profiles` table now has:
- `role` TEXT - 'user' or 'admin' (permissions)
- `title` TEXT - 'attorney', 'paralegal', 'finance', etc. (job title)

## Migration Required

**⚠️ IMPORTANT: You need to run the updated migration in Supabase:**

1. Go to Supabase SQL Editor
2. Run the updated migration: `backend/supabase/migrations/001_create_profiles_table.sql`

This will:
- Add the `title` column to the `profiles` table
- Update the `role` CHECK constraint to only allow 'user' or 'admin'
- Update the trigger function to include `title`

## Update Existing Users

After running the migration, update existing users in Supabase:

```sql
-- Update existing admin user to have title
UPDATE public.profiles
SET title = 'attorney'
WHERE role = 'admin' AND title IS NULL;

-- Update other users based on their current role
UPDATE public.profiles
SET 
  title = CASE 
    WHEN role = 'attorney' THEN 'attorney'
    WHEN role = 'paralegal' THEN 'paralegal'
    WHEN role = 'admin' THEN 'admin'
    ELSE 'attorney'
  END,
  role = CASE
    WHEN role = 'admin' THEN 'admin'
    ELSE 'user'
  END;
```

## Frontend Changes

1. **Settings Page:**
   - Shows both "Role" (permissions) and "Title" (job title)
   - User Management table shows both columns
   - Create user form has separate fields for Role and Title

2. **User Creation:**
   - Role dropdown: User or Admin (permissions)
   - Title dropdown: Attorney, Paralegal, Finance, Admin, User (job title)

3. **Header:**
   - Shows title (job title) instead of role

## Backend Changes

1. **API Endpoints:**
   - Create user accepts both `role` and `title`
   - User responses include both `role` and `title`

2. **Validation:**
   - Role must be 'user' or 'admin'
   - Title must be one of: 'attorney', 'paralegal', 'finance', 'admin', 'user'

## Next Steps

1. **Run the migration** in Supabase SQL Editor
2. **Update existing users** using the SQL above
3. **Restart both servers** (backend and frontend)
4. **Test creating a new user** - should see Role and Title fields



