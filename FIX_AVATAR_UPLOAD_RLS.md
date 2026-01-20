# Fix Avatar Upload RLS Policy Error

## Problem
You're getting the error: `Failed to upload avatar: new row violates row-level security policy`

This happens because the UPDATE policy for the `profiles` table is missing the `WITH CHECK` clause, which Supabase requires for UPDATE operations.

## Solution

Run migration `005_fix_profile_update_policy.sql` in your Supabase SQL Editor:

1. Go to your Supabase Dashboard
2. Navigate to **SQL Editor**
3. Click **New Query**
4. Copy and paste the entire contents of `backend/supabase/migrations/005_fix_profile_update_policy.sql`
5. Click **Run** (or press Ctrl+Enter)

## What This Migration Does

The migration:
1. Drops the old "Admins can update profiles" policy (from migration 003) which was missing the `WITH CHECK` clause
2. Creates a new "Users can update own profile" policy with both `USING` and `WITH CHECK` clauses

This allows:
- Users to update their own profile (including `avatar_url`)
- Admins to update any profile

## Verify It Worked

After running the migration, try uploading an avatar again. If it still fails, check:
- You're logged in with a valid session
- The user ID in your session matches the profile you're trying to update
- Check the Supabase logs for more detailed error messages



