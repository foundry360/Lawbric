# Quick Start Guide

## Simple Startup (Recommended)

**Double-click these files:**

1. **`start-all.bat`** - Starts both backend and frontend (easiest!)
   - Opens 2 windows automatically
   - Backend on port 9000
   - Frontend on port 3000

2. **OR start separately:**
   - `start-backend.bat` - Backend only
   - `start-frontend.bat` - Frontend only

## First Time Setup

1. **Backend dependencies:**
   ```powershell
   cd backend
   py -m pip install -r requirements.txt
   ```

2. **Frontend dependencies:**
   ```powershell
   cd frontend
   npm install
   ```

## Verify It's Working

1. **Backend:** http://localhost:9000/health
   - Should show: `{"status":"ok"}`

2. **Frontend:** http://localhost:3000
   - Should load the app

## Troubleshooting

### Backend won't start:
- Make sure Python is installed: `py --version`
- Install dependencies: `cd backend && py -m pip install -r requirements.txt`
- Check for error messages in the backend window

### Frontend won't start:
- Make sure Node.js is installed: `node --version`
- Install dependencies: `cd frontend && npm install`
- Clear cache: `rm -r .next` (if exists)

### Port already in use:
- Stop other instances: Close the windows with the servers
- Or change ports in:
  - Backend: `backend/run.py` (line 51: `port=9000`)
  - Frontend: `frontend/.env.local` (set `NEXT_PUBLIC_API_URL`)

## For Production (GCP)

These scripts are for development. For production on GCP:
- Use Cloud Run or App Engine
- Containerize with Docker (recommended)
- Use environment variables for configuration


