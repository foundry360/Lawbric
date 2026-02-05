# How to Open WSL2 Terminal - Step by Step

## Method 1: From Start Menu (Easiest)

1. **Click the Windows Start button** (bottom left corner of your screen)
2. **Type "Ubuntu"** in the search box
3. **Click on "Ubuntu-22.04"** (or whatever Ubuntu version you have)
4. A black terminal window will open - this is WSL2!

## Method 2: From PowerShell

1. **Open PowerShell** (you already have this open)
2. **Type this command:**
   ```powershell
   wsl
   ```
3. Press Enter
4. You'll now be in WSL2!

## Method 3: From Run Dialog

1. **Press `Windows Key + R`** (hold Windows key, press R)
2. **Type:** `wsl`
3. **Press Enter**
4. WSL2 terminal opens!

---

## Once WSL2 is Open:

You'll see something like:
```
jgelsomino@DESKTOP-XXXXX:~$
```

This means you're in WSL2 (Linux), not Windows PowerShell.

**Then run these commands:**
```bash
cd /mnt/c/LegalAI
sudo ./setup_gpu_wsl2.sh
```

When it asks for a password, type your WSL2 password (the one you set when you first installed Ubuntu). The password won't show as you type - that's normal!

---

## Still Can't Find It?

If you don't see "Ubuntu" in the Start Menu, WSL2 might not be installed. Let me know and I'll help you install it!



