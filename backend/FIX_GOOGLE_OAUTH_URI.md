# Fix Google OAuth Redirect URI Mismatch

## Current Redirect URI
Your application is using:
```
http://localhost:3000/connected-apps/callback
```

## Steps to Fix in Google Cloud Console

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Select your project

2. **Navigate to OAuth 2.0 Client IDs**
   - Go to "APIs & Services" > "Credentials"
   - Find your OAuth 2.0 Client ID (the one you're using)
   - Click on it to edit

3. **Add/Update Authorized Redirect URIs**
   - In the "Authorized redirect URIs" section, make sure you have EXACTLY:
     ```
     http://localhost:3000/connected-apps/callback
     ```
   
   **Important:**
   - Must be EXACTLY this (case-sensitive)
   - No trailing slashes
   - Must include `http://` (not `https://`)
   - Must match the port (3000)

4. **Save the Changes**
   - Click "Save"
   - Wait a few seconds for changes to propagate

5. **Try Again**
   - Go back to your application
   - Try connecting Google Drive again

## Common Issues

### Issue: "redirect_uri_mismatch" error
**Solution:** Make sure the URI in Google Cloud Console matches EXACTLY:
- `http://localhost:3000/connected-apps/callback` ✅
- `http://localhost:3000/connected-apps/callback/` ❌ (trailing slash)
- `https://localhost:3000/connected-apps/callback` ❌ (https instead of http)
- `http://127.0.0.1:3000/connected-apps/callback` ❌ (different host)

### Issue: Changes not taking effect
**Solution:** 
- Wait 1-2 minutes after saving
- Clear browser cache
- Try in an incognito/private window

## Alternative: If you need to change the redirect URI

If you want to use a different redirect URI, you need to update it in TWO places:

1. **Backend `.env` file:**
   ```env
   GOOGLE_REDIRECT_URI=http://localhost:3000/your-new-path
   ```

2. **Google Cloud Console:**
   - Add the new URI to "Authorized redirect URIs"

3. **Restart the backend server**


