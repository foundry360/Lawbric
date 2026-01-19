# Fix: Stuck on "Loading..." Screen

## The Problem

The app is stuck on the "Loading..." screen, which means the auth context is stuck in a loading state.

## Quick Fix

### Step 1: Clear Browser Storage

Open browser console and run:
```javascript
localStorage.clear()
sessionStorage.clear()
location.reload()
```

### Step 2: Check Browser Console

Look for these errors:
- `❌ Supabase not configured` - Environment variables not loading
- `Auth loading timeout` - Auth initialization taking too long
- `Session timeout` - Supabase session check timing out

### Step 3: Verify Environment Variables

Check if Supabase environment variables are loaded:
```javascript
// In browser console:
process.env.NEXT_PUBLIC_SUPABASE_URL
```

If `undefined`, restart the dev server:
```powershell
# Stop server (Ctrl+C)
cd frontend
npm run dev
```

## Common Causes

1. **Environment Variables Not Loaded**
   - Solution: Restart dev server after creating/updating `.env.local`

2. **Supabase Session Check Hanging**
   - Solution: Code now has 2-second timeout to prevent infinite loading

3. **Stale Browser Storage**
   - Solution: Clear localStorage/sessionStorage

4. **Backend Not Running**
   - Solution: Start backend server on port 8000

## Code Changes Made

1. Added timeout to `getSession()` call (2 seconds)
2. Increased safety timeout from 1s to 2s
3. Auto-create dev user if auth times out (prevents infinite loading)
4. Better error logging

## Verify Fix

After clearing storage and restarting:
1. Open browser console
2. You should see auth initialization messages
3. Loading should complete within 2 seconds
4. Should see login page or dashboard (if logged in)

