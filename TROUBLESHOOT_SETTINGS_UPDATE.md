# Troubleshooting: Settings Page Not Updating

## Issue
The settings page isn't showing updated Role/Title fields.

## Quick Fix Steps

### 1. **Hard Refresh the Browser**
- Press `Ctrl + Shift + R` (Windows) or `Cmd + Shift + R` (Mac)
- Or open DevTools (F12) → Right-click refresh button → "Empty Cache and Hard Reload"

### 2. **Check Browser Console**
Open DevTools (F12) → Console tab, look for:
```
✅ Loaded user with role from profile: admin
Settings page - Current user: { role: 'admin', title: 'attorney', ... }
```

If `title` is missing or `undefined`, the profile fetch isn't working.

### 3. **Log Out and Log Back In**
The user data is loaded when you log in. After running the migration:
1. Click Logout
2. Log back in
3. This will fetch the updated profile from Supabase

### 4. **Verify Profile in Supabase**
Run this SQL in Supabase SQL Editor:
```sql
SELECT id, email, role, title, full_name 
FROM public.profiles 
WHERE email = 'your-email@example.com';
```

Make sure:
- `title` column exists
- `title` has a value (not NULL)
- `role` is 'user' or 'admin'

### 5. **Check if Migration Was Run**
Verify the `title` column exists:
```sql
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'profiles' 
AND column_name = 'title';
```

If it doesn't exist, run the migration `002_add_title_column.sql`.

## Debugging

Open browser console and check what's logged:
```javascript
// Should see:
Settings page - Current user: { 
  id: "...", 
  email: "...", 
  role: "admin", 
  title: "attorney",  // <-- This should be present
  isAdmin: true 
}
```

If `title` is missing:
- Profile fetch failed (check network tab)
- Migration wasn't run
- User logged in before migration was applied

## Solution

1. **Run the migration** `002_add_title_column.sql` in Supabase
2. **Update your existing user** in Supabase (set title field)
3. **Hard refresh** the browser (Ctrl+Shift+R)
4. **Log out and log back in** to reload profile
5. **Check console** for the debug logs

