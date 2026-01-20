# Google OAuth Setup Instructions

To enable Google Drive integration, you need to set up Google OAuth credentials.

## Steps:

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Create a new project or select an existing one

2. **Enable Google Drive API**
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"

3. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - If prompted, configure the OAuth consent screen first:
     - Choose "External" (unless you have a Google Workspace)
     - Fill in required fields (App name, User support email, Developer contact)
     - Add scopes: `https://www.googleapis.com/auth/drive.readonly`
     - Add test users if needed
   - Application type: "Web application"
   - Name: "Legal AI Platform" (or any name)
   - Authorized redirect URIs: `http://localhost:3000/connected-apps/callback`
   - Click "Create"

4. **Copy Credentials**
   - You'll see a dialog with your Client ID and Client Secret
   - Copy both values

5. **Create `.env` file in the `backend` directory**
   ```env
   GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret-here
   GOOGLE_REDIRECT_URI=http://localhost:3000/connected-apps/callback
   ```

6. **Restart the backend server**
   - The server will automatically load the new environment variables

## Notes:
- The redirect URI must exactly match what you configured in Google Cloud Console
- For production, update the redirect URI to your production domain
- Keep your Client Secret secure and never commit it to version control


