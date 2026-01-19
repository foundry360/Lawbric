# Test Profile Fetch

## Manual Test in Browser Console

Open browser console (F12) and run this to test profile fetch directly:

```javascript
// First, get your Supabase client
import { supabase } from '@/lib/supabase'

// Then fetch your profile
const { data, error } = await supabase
  .from('profiles')
  .select('*')
  .eq('id', '44824a1c-c498-4905-83bb-fb81b80b85e3')
  .single()

console.log('Profile data:', data)
console.log('Error:', error)

// Or fetch by email
const { data: dataByEmail, error: errorByEmail } = await supabase
  .from('profiles')
  .select('*')
  .eq('email', 'jgelsomino@foundry360.us')
  .single()

console.log('Profile by email:', dataByEmail)
console.log('Error by email:', errorByEmail)
```

## Check Current Session

```javascript
const { data: { session } } = await supabase.auth.getSession()
console.log('Current session:', session)
console.log('User ID:', session?.user?.id)
```

## Check RLS Policies

The RLS policy "Users can view own profile" uses `auth.uid() = id`. This should work if:
1. User is authenticated (has a valid session)
2. The session user ID matches the profile ID

## Expected Profile Data

Based on your database:
```json
{
  "id": "44824a1c-c498-4905-83bb-fb81b80b85e3",
  "email": "jgelsomino@foundry360.us",
  "role": "admin",
  "title": "paralegal",
  "full_name": "Jason Gelsomino"
}
```

This should show up in the settings page as:
- Role: admin
- Title: paralegal

