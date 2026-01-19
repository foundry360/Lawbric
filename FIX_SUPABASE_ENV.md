# Fix: Supabase Environment Variables Not Loading

## The Problem

Even though `.env.local` exists with correct values, Next.js isn't loading them. This happens because:
1. Next.js caches environment variables on startup
2. Environment variables are only loaded when the dev server starts
3. The `.next` cache might have stale data

## Quick Fix (3 Steps)

### Step 1: Stop the Dev Server
Press `Ctrl+C` in the terminal where `npm run dev` is running.

### Step 2: Clear Next.js Cache
```powershell
cd frontend
Remove-Item -Recurse -Force .next
```

### Step 3: Restart the Dev Server
```powershell
npm run dev
```

## Verify It's Working

After restarting, check the browser console. You should see:

```
✅ Supabase client initialized successfully
```

**NOT:**
```
❌ Supabase URL and Anon Key are required
```

## Alternative: Use the Fix Script

I've created a script to automate this:

```powershell
cd frontend
.\fix-env.ps1
npm run dev
```

## Why This Happens

Next.js loads environment variables when the server starts:
- Variables are embedded into the JavaScript bundle at build/start time
- If you create/update `.env.local` while the server is running, it won't pick up changes
- The `.next` folder caches these values

## Prevention

**Always restart the dev server after:**
- Creating `.env.local`
- Updating environment variables in `.env.local`
- Changing `next.config.js`

## Verify Environment Variables

To check if variables are loaded, open browser console and type:
```javascript
process.env.NEXT_PUBLIC_SUPABASE_URL
```

You should see: `"https://erzumnwlvokamhuwcfyf.supabase.co"`

If you see `undefined`, the variables aren't loading.

