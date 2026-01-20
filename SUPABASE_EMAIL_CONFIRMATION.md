# Fix: Enable Users Without Email Confirmation

## Problem
Users are being created in Supabase but not appearing because email confirmation is enabled by default.

## Solution: Disable Email Confirmation

1. Go to your Supabase Dashboard: https://supabase.com/dashboard
2. Select your project: `erzumnwlvokamhuwcfyf`
3. Navigate to **Authentication** → **Settings**
4. Scroll down to **Email Auth**
5. Find **Enable email confirmations** toggle
6. **Turn OFF** the toggle (disable it)
7. Click **Save**

## Why This Is Needed

By default, Supabase requires users to confirm their email before they can sign in. This means:
- Users are created in Supabase
- But they're not "confirmed" until they click the confirmation email
- The app can't find them because they're not confirmed yet

For MVP/development, it's better to disable email confirmation so users can sign in immediately.

## Alternative: Keep Email Confirmation Enabled

If you want to keep email confirmation enabled for production:

1. Users will need to check their email after signing up
2. They'll click a confirmation link
3. Then they can sign in

The code will now show a helpful error message: "Please check your email and confirm your account before signing in."

## Test After Disabling

1. Disable email confirmation in Supabase dashboard
2. Restart your Next.js dev server (to pick up any changes)
3. Try logging in with a new email/password
4. Check Supabase → Authentication → Users to see the new user
5. The user should appear immediately after signup



