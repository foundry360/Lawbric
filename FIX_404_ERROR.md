# Fix: 404 Error on http://localhost:3000/

## The Problem

You're getting repeated 404 errors for `http://localhost:3000/`. This means the Next.js dev server either:
1. **Not running** - The server was never started or crashed
2. **Port conflict** - Something else is using port 3000
3. **Build error** - Next.js failed to compile
4. **Cache issue** - Stale `.next` cache causing issues

## Quick Fix Steps

### Step 1: Check if Server is Running

**Check if Node.js is running:**
```powershell
Get-Process -Name node -ErrorAction SilentlyContinue
```

If you see no processes, the server isn't running.

**Check if port 3000 is in use:**
```powershell
Test-NetConnection -ComputerName localhost -Port 3000
```

If it shows `TcpTestSucceeded: True`, something is listening on port 3000.

### Step 2: Kill All Node Processes

If there are stuck Node processes:

```powershell
# Kill all Node processes
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force
```

### Step 3: Clear Next.js Cache

```powershell
cd frontend
Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue
```

### Step 4: Restart the Dev Server

```powershell
cd frontend
npm run dev
```

**Wait for:**
```
✓ Ready in X seconds
○ Compiling / ...
✓ Compiled / in X ms
```

### Step 5: Verify Server is Running

Open browser to `http://localhost:3000` - you should see the login page, not 404 errors.

## Troubleshooting

### If Server Won't Start

**Check for errors in terminal:**
- Look for compilation errors
- Check for missing dependencies
- Verify `.env.local` exists

**Reinstall dependencies:**
```powershell
cd frontend
Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
npm install
```

### If Port 3000 is Already in Use

**Find what's using port 3000:**
```powershell
netstat -ano | findstr :3000
```

**Kill the process:**
```powershell
taskkill /PID <PID> /F
```

**Or use a different port:**
```powershell
# In frontend/package.json, change:
"dev": "next dev -p 3001"

# Or set environment variable:
$env:PORT=3001; npm run dev
```

### If Still Getting 404 Errors

**Check the terminal output** - There should be compilation logs showing which pages are being served.

**Verify the page exists:**
- `frontend/app/page.tsx` should exist (this is your login page)

**Clear browser cache:**
- Hard refresh: `Ctrl + Shift + R` or `Ctrl + F5`
- Or clear browser cache completely

## Expected Behavior

**When server is running correctly:**
- Terminal shows: `✓ Ready` and compilation messages
- Browser console shows NO 404 errors for `http://localhost:3000/`
- Page loads correctly (login page with logo)

**When server is NOT running:**
- Browser shows connection refused or 404 errors
- Terminal shows no Node.js processes
- Port 3000 is not listening

## Quick Checklist

- [ ] Node.js is installed (`node --version`)
- [ ] Dependencies are installed (`npm install` completed)
- [ ] `.env.local` file exists in `frontend` directory
- [ ] No errors in terminal when running `npm run dev`
- [ ] Server shows "Ready" message
- [ ] Port 3000 is not blocked by firewall
- [ ] Browser cache is cleared
- [ ] `.next` cache is cleared



