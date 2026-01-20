# Supabase Environment Variables Setup Guide

This guide explains how to get your Supabase credentials and set them up in your environment files.

## Getting Your Supabase Credentials

### Step 1: Go to Supabase Dashboard
1. Go to https://supabase.com/dashboard
2. Select your project (or create a new one)

### Step 2: Get Your Project URL
1. Go to **Settings** > **API** (or **Project Settings** > **API**)
2. Copy your **Project URL** (looks like: `https://xxxxx.supabase.co`)

### Step 3: Get Your API Keys
In the same **Settings** > **API** page, you'll find:

1. **anon/public key** (starts with `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`)
   - This is safe to use in the frontend
   - Used for client-side authentication

2. **service_role key** (also starts with `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`)
   - **⚠️ KEEP THIS SECRET - NEVER EXPOSE TO FRONTEND**
   - This is for backend/server-side operations only
   - Bypasses Row Level Security (RLS)
   - Used for admin operations like creating users

## Environment Variables Setup

### Backend Environment Variables

Create or update `backend/.env`:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-role-key-here
```

**Where to find these:**
- `SUPABASE_URL`: Project Settings > API > Project URL
- `SUPABASE_KEY`: Project Settings > API > Project API keys > `anon` `public`
- `SUPABASE_SERVICE_KEY`: Project Settings > API > Project API keys > `service_role` `secret`

### Frontend Environment Variables

Create or update `frontend/.env.local`:

```env
# Supabase Configuration (Public - Safe for frontend)
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
```

**Where to find these:**
- `NEXT_PUBLIC_SUPABASE_URL`: Same as backend SUPABASE_URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Same as backend SUPABASE_KEY (anon/public key)

**⚠️ Important:**
- Never put `SUPABASE_SERVICE_KEY` in frontend environment variables
- Only use `NEXT_PUBLIC_` prefix for variables that need to be accessible in the browser
- The anon key is safe for frontend use (it's limited by RLS policies)

## Quick Setup Script

If you already have your Supabase credentials, you can quickly set them up:

**Windows (PowerShell):**
```powershell
# Navigate to your project
cd C:\LegalAI

# Backend .env
@"
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
"@ | Out-File -FilePath backend\.env -Encoding utf8

# Frontend .env.local
@"
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
"@ | Out-File -FilePath frontend\.env.local -Encoding utf8
```

**Linux/Mac:**
```bash
# Backend .env
cat > backend/.env << EOF
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
EOF

# Frontend .env.local
cat > frontend/.env.local << EOF
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
EOF
```

## Verifying Your Setup

### Check Backend Configuration
```bash
cd backend
python -c "from app.core.config import settings; print('URL:', settings.SUPABASE_URL[:30] + '...'); print('Key set:', bool(settings.SUPABASE_KEY)); print('Service key set:', bool(settings.SUPABASE_SERVICE_KEY))"
```

### Check Frontend Configuration
After starting the frontend dev server, check the browser console for:
```
✅ Supabase client initialized successfully
```

If you see an error, check that:
1. Your `.env.local` file exists in the `frontend` directory
2. The variable names are correct (including `NEXT_PUBLIC_` prefix)
3. You've restarted the dev server after adding the variables

## Security Notes

1. **Never commit `.env` or `.env.local` files to git**
   - These files are already in `.gitignore`
   - Keep your service_role key secret

2. **Service Role Key is Powerful**
   - It bypasses all Row Level Security policies
   - Only use it on the backend
   - Never expose it to the frontend or client-side code

3. **Anon Key is Safe**
   - It's designed to be public (used in frontend)
   - It's limited by RLS policies
   - Can be safely committed if needed (though not recommended)

## Troubleshooting

### "Supabase not configured" error
- Check that your `.env` files exist
- Verify the variable names are correct
- Restart your dev servers after changing environment variables

### "Invalid token" errors
- Make sure you're using the service_role key on the backend
- Make sure you're using the anon key on the frontend
- Check that the keys match what's in your Supabase dashboard

### "Permission denied" errors
- Check your RLS policies in Supabase
- Verify user roles are set correctly
- Make sure the service_role key is being used for admin operations



