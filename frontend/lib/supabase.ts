import { createClient, SupabaseClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

// Log configuration status (only in development)
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  console.log('Supabase Config:', {
    url: supabaseUrl ? `${supabaseUrl.substring(0, 30)}...` : 'NOT SET',
    key: supabaseAnonKey ? `${supabaseAnonKey.substring(0, 20)}...` : 'NOT SET',
    configured: !!(supabaseUrl && supabaseAnonKey)
  })
}

// Create a dummy client if credentials are not set (prevents crashes)
let supabase: SupabaseClient

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('❌ Supabase URL and Anon Key are required. Please check your environment variables.')
  console.error('Make sure .env.local exists in the frontend directory with NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY')
  // Create a client with placeholder values to prevent crashes
  // This allows the app to run even if Supabase isn't configured yet
  supabase = createClient(
    supabaseUrl || 'https://placeholder.supabase.co',
    supabaseAnonKey || 'placeholder-key',
    {
      auth: {
        autoRefreshToken: false,
        persistSession: false,
        detectSessionInUrl: false
      }
    }
  )
} else {
  console.log('✅ Supabase client initialized successfully')
  supabase = createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true
    }
  })
}

export { supabase }

