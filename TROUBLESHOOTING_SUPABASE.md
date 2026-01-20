# Troubleshooting Supabase Configuration Error

If you're getting an error that "Supabase is not configured" when logging in, follow these steps:

## Step 1: Verify Environment Variables

**Check that `.env.local` exists in `frontend` directory:**
```powershell
cd frontend
if (Test-Path .env.local) {
    Write-Host "✅ .env.local exists"
    Get-Content .env.local | Select-String "SUPABASE"
} else {
    Write-Host "❌ .env.local NOT FOUND"
}
```

**It should contain:**
```env
NEXT_PUBLIC_SUPABASE_URL=https://erzumnwlvokamhuwcfyf.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Step 2: Restart the Frontend Dev Server

**This is the most common fix!** Next.js only loads environment variables on startup.

1. **Stop the frontend dev server** (Press `Ctrl+C` in the terminal where it's running)
2. **Start it again:**
   ```powershell
   cd frontend
   npm run dev
   ```

## Step 3: Clear Next.js Cache (if restart doesn't work)

Sometimes Next.js caches old values:

```powershell
cd frontend
Remove-Item -Recurse -Force .next
npm run dev
```

## Step 4: Verify in Browser Console

After restarting, check the browser console. You should see:

```
✅ Supabase client initialized successfully
```

**Or check the console log:**
```
Supabase Config: { url: "https://erzumnwlvokamhuwcfyf...", key: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", configured: true }
```

If you see `configured: false`, the environment variables aren't loading.

## Step 5: Check for Typos

Common mistakes:
- ❌ `NEXT_PUBLIC_SUPABASE_URL` (missing `NEXT_PUBLIC_` prefix)
- ❌ `NEXT_PUBLIC_SUPABASE_KEY` (should be `NEXT_PUBLIC_SUPABASE_ANON_KEY`)
- ❌ Extra spaces or quotes around values
- ❌ File is named `.env` instead of `.env.local`

## Step 6: Verify Environment Variables Are Accessible

Check that Next.js can access them:

1. Open browser console
2. Type: `process.env.NEXT_PUBLIC_SUPABASE_URL`
3. You should see your Supabase URL

**Note:** Only `NEXT_PUBLIC_` prefixed variables are available in the browser.

## Step 7: Recreate .env.local (Last Resort)

If nothing works, recreate the file:

```powershell
cd frontend
@"
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://erzumnwlvokamhuwcfyf.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVyenVtbndsdm9rYW1odXdjZnlmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg3NzA5ODAsImV4cCI6MjA4NDM0Njk4MH0.nxgtb_xsbwamZ2OIGvHA6xyXoKnsnAIDi6mGAVNi8jA
"@ | Out-File -FilePath .env.local -Encoding utf8
```

Then restart the dev server.

## Quick Fix Checklist

- [ ] `.env.local` exists in `frontend` directory
- [ ] Variables start with `NEXT_PUBLIC_`
- [ ] No extra spaces or quotes in values
- [ ] Dev server has been restarted after creating/updating `.env.local`
- [ ] Browser console shows Supabase client initialized
- [ ] No typos in variable names



