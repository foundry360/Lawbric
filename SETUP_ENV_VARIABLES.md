# Quick Setup: Environment Variables

## Your Current Supabase Credentials

Based on your setup script, here are your Supabase credentials:

**Project URL:** `https://erzumnwlvokamhuwcfyf.supabase.co`

**Anon Key:**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVyenVtbndsdm9rYW1odXdjZnlmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg3NzA5ODAsImV4cCI6MjA4NDM0Njk4MH0.nxgtb_xsbwamZ2OIGvHA6xyXoKnsnAIDi6mGAVNi8jA
```

**Service Role Key:**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVyenVtbndsdm9rYW1odXdjZnlmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODc3MDk4MCwiZXhwIjoyMDg0MzQ2OTgwfQ.u7ktKuVZ3Q3mGWzxUPZ1ehRSnIsJobDV9ZvF4OSG65A
```

## Setup Instructions

### Option 1: Manual Setup

**1. Backend (`backend/.env`):**
```env
SUPABASE_URL=https://erzumnwlvokamhuwcfyf.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVyenVtbndsdm9rYW1odXdjZnlmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg3NzA5ODAsImV4cCI6MjA4NDM0Njk4MH0.nxgtb_xsbwamZ2OIGvHA6xyXoKnsnAIDi6mGAVNi8jA
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVyenVtbndsdm9rYW1odXdjZnlmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODc3MDk4MCwiZXhwIjoyMDg0MzQ2OTgwfQ.u7ktKuVZ3Q3mGWzxUPZ1ehRSnIsJobDV9ZvF4OSG65A
```

**2. Frontend (`frontend/.env.local`):**
```env
NEXT_PUBLIC_SUPABASE_URL=https://erzumnwlvokamhuwcfyf.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVyenVtbndsdm9rYW1odXdjZnlmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg3NzA5ODAsImV4cCI6MjA4NDM0Njk4MH0.nxgtb_xsbwamZ2OIGvHA6xyXoKnsnAIDi6mGAVNi8jA
```

### Option 2: Use Setup Script

Run the PowerShell script:
```powershell
.\setup-env.ps1
```

### Option 3: Check Current Setup

**Backend:**
```powershell
cd backend
if (Test-Path .env) {
    Get-Content .env | Select-String "SUPABASE"
} else {
    Write-Host ".env file not found in backend directory"
}
```

**Frontend:**
```powershell
cd frontend
if (Test-Path .env.local) {
    Get-Content .env.local | Select-String "SUPABASE"
} else {
    Write-Host ".env.local file not found in frontend directory"
}
```

## Verify Setup

After setting up, restart your servers:
1. Backend: Stop and restart the Python server
2. Frontend: Stop and restart the Next.js dev server (Ctrl+C then `npm run dev`)

The frontend console should show:
```
✅ Supabase client initialized successfully
```

## Important Notes

- **Backend** uses both `SUPABASE_KEY` (anon) and `SUPABASE_SERVICE_KEY` (service role)
- **Frontend** only needs `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- **Never** put the service role key in frontend environment variables
- Make sure `.env` and `.env.local` are in `.gitignore` (they should be already)



