# Debug Avatar Upload RLS Error

## Steps to Diagnose

1. **Check Browser Console Logs**
   - Open browser DevTools (F12)
   - Try uploading an avatar
   - Look for detailed console logs showing:
     - Upload status
     - User ID
     - Session information
     - Exact error messages

2. **Verify Policies in Supabase**
   
   Run this in Supabase SQL Editor to see all policies:
   ```sql
   SELECT policyname, cmd, qual, with_check
   FROM pg_policies 
   WHERE tablename = 'profiles' AND schemaname = 'public';
   ```
   
   You should see:
   - A SELECT policy allowing users to view their own profile
   - An UPDATE policy with both `qual` and `with_check` clauses

3. **Check Storage Policies**
   
   Run this in Supabase SQL Editor:
   ```sql
   SELECT policyname, cmd, qual, with_check
   FROM pg_policies 
   WHERE tablename = 'objects' 
   AND schemaname = 'storage'
   AND policyname LIKE '%avatar%';
   ```

4. **Test the UPDATE Directly**
   
   Run this in Supabase SQL Editor while logged in:
   ```sql
   -- First, get your user ID
   SELECT auth.uid() as current_user_id;
   
   -- Then try to update your profile (replace with your actual user ID)
   UPDATE public.profiles
   SET avatar_url = 'https://test.com/avatar.jpg'
   WHERE id = auth.uid()
   RETURNING *;
   ```

5. **Run Migration 009**
   
   Run `backend/supabase/migrations/009_check_and_fix_profile_policies.sql` to ensure clean policies.

## Common Issues

- **No WITH CHECK clause**: UPDATE policies need both USING and WITH CHECK
- **Conflicting policies**: Multiple UPDATE policies can interfere with each other
- **Wrong role**: Policy might be checking for admin role when user is not admin
- **Storage vs Database**: Error might be from storage upload, not database update



