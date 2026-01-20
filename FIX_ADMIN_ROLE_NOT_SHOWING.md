# Fix: Admin Role Not Showing User Management Tab

## The Problem

You have an admin role in the Supabase `profiles` table, but the "User Management" tab isn't showing in Settings.

## Root Cause

The frontend was only reading the role from `user_metadata`, but the actual role is stored in the `profiles` table in Supabase.

## Solution Applied

I've updated the code to:
1. Fetch user profile from Supabase `profiles` table
2. Get the role from the profile instead of just `user_metadata`
3. Use the profile role for admin checks

## What You Need to Do

### Option 1: Refresh the Page (Easiest)

The auth code now fetches the profile on initialization. Just refresh the page:
- Press `F5` or `Ctrl+R`
- The role should be loaded from the profiles table

### Option 2: Log Out and Log Back In

1. Click logout
2. Log back in with your admin credentials
3. The User Management tab should appear

### Option 3: Clear Browser Storage

Open browser console (F12) and run:
```javascript
localStorage.clear()
location.reload()
```

Then log in again.

## Verify It's Working

After refreshing/logging in:

1. **Check browser console** - You should see:
   ```
   ✅ Loaded user with role from profile: admin
   ```

2. **Go to Settings page** - You should see:
   ```
   Settings page - Current user: { role: 'admin', isAdmin: true }
   ```

3. **User Management tab should appear** below Appearance tab

## Debug

If it's still not working, check the browser console:

```javascript
// Check what role is stored in user object
// Open console and look at the Settings page logs
```

Or manually check:
```javascript
// In browser console:
JSON.parse(localStorage.getItem('user') || '{}')
```

## Common Issues

1. **Profile doesn't exist** - Make sure there's a row in `profiles` table for your user
2. **Role is different** - Check the exact role value in Supabase (should be `'admin'`)
3. **RLS blocking** - Make sure Row Level Security allows you to read your own profile

## Check Your Profile in Supabase

Run this SQL in Supabase SQL Editor to check:
```sql
SELECT id, email, role, full_name 
FROM public.profiles 
WHERE email = 'your-email@example.com';
```

Make sure `role` is exactly `'admin'` (lowercase).



