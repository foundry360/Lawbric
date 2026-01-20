'use client'

import { supabase } from './supabase'
import { User } from '@supabase/supabase-js'

export interface SupabaseUser {
  id: string
  email: string
  role?: string  // user or admin (permissions)
  title?: string  // attorney, paralegal, finance, etc. (job title)
  full_name?: string
  avatar_url?: string  // URL to profile avatar in Supabase storage
}

/**
 * Sign up a new user with Supabase
 */
export async function signUp(email: string, password: string, metadata?: { full_name?: string; role?: string }) {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: metadata || {}
    }
  })
  
  if (error) throw error
  return data
}

/**
 * Sign in a user with Supabase
 */
export async function signIn(email: string, password: string) {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })
  
  if (error) throw error
  return data
}

/**
 * Sign out the current user
 */
export async function signOut() {
  const { error } = await supabase.auth.signOut()
  if (error) throw error
}

/**
 * Get the current session
 */
export async function getSession() {
  const { data: { session }, error } = await supabase.auth.getSession()
  if (error) throw error
  return session
}

/**
 * Get the current user
 */
export async function getCurrentUser(): Promise<User | null> {
  const { data: { user }, error } = await supabase.auth.getUser()
  if (error) throw error
  return user
}

/**
 * Listen to auth state changes
 */
export function onAuthStateChange(callback: (event: string, session: any) => void) {
  return supabase.auth.onAuthStateChange(callback)
}

/**
 * Get user profile from Supabase profiles table
 */
export async function getUserProfile(userId: string) {
  try {
    console.log('🔍 Fetching profile for user ID:', userId)
    
    // Verify we have a session before querying
    const { data: { session } } = await supabase.auth.getSession()
    console.log('🔐 Current session exists:', !!session)
    console.log('🔐 Session user ID:', session?.user?.id)
    console.log('🔐 Requested user ID:', userId)
    console.log('🔐 IDs match:', session?.user?.id === userId)
    
    if (!session) {
      console.error('❌ No active session - cannot fetch profile (RLS requires auth)')
      return null
    }
    
    const { data, error } = await supabase
      .from('profiles')
      .select('id, email, full_name, role, title, avatar_url, is_active, created_at, updated_at')
      .eq('id', userId)
      .single()
    
    if (error) {
      console.error('❌ Supabase error fetching profile:', error)
      console.error('   Error code:', error.code, 'message:', error.message)
      throw error
    }
    
    if (data) {
      console.log('✅ Profile fetched successfully')
      console.log('   Full profile data:', data)
      console.log('   avatar_url value:', data.avatar_url)
      console.log('   avatar_url type:', typeof data.avatar_url)
      console.log('   avatar_url is null:', data.avatar_url === null)
      console.log('   avatar_url is undefined:', data.avatar_url === undefined)
      console.log('   avatar_url truthy:', !!data.avatar_url)
    } else {
      console.warn('⚠️ Profile query returned no data')
    }
    return data
  } catch (error: any) {
    console.error('❌ Error in getUserProfile (catch block):', error)
    console.error('   Error type:', typeof error)
    console.error('   Error keys:', Object.keys(error || {}))
    
    if (error?.code === 'PGRST116') {
      console.error('   → Profile not found (PGRST116)')
    } else if (error?.code === '42501') {
      console.error('   → Permission denied - RLS policy issue (42501)')
    }
    
    return null
  }
}

/**
 * Convert Supabase User to app user format
 * Optionally fetches role from profiles table
 */
export async function mapSupabaseUserWithProfile(user: User | null): Promise<SupabaseUser | null> {
  if (!user) return null
  
  // Defaults (only used if profile fetch fails)
  let role = 'user'
  let title = 'attorney'
  let full_name = user.user_metadata?.full_name || user.user_metadata?.fullName || undefined
  
  // Defaults (only used if profile fetch fails)
  let avatar_url: string | undefined = undefined
  
  // Try to get role and title from profiles table (this is the source of truth)
  try {
    const profile = await getUserProfile(user.id)
    
    if (profile) {
      // Use profile data as source of truth
      role = profile.role ?? user.user_metadata?.role ?? 'user'
      title = profile.title ?? user.user_metadata?.title ?? 'attorney'
      full_name = profile.full_name ?? user.user_metadata?.full_name ?? user.user_metadata?.fullName ?? undefined
      // Explicitly handle avatar_url - convert null to undefined, keep string as-is
      avatar_url = profile.avatar_url && profile.avatar_url !== 'null' && profile.avatar_url.trim() !== '' 
        ? profile.avatar_url 
        : undefined
    } else {
      console.warn('⚠️ Profile is null, falling back to metadata')
      role = user.user_metadata?.role ?? 'user'
      title = user.user_metadata?.title ?? 'attorney'
    }
  } catch (error) {
    // Fall back to user_metadata if profile fetch fails
    console.error('❌ Error fetching profile, using metadata:', error)
    role = user.user_metadata?.role ?? 'user'
    title = user.user_metadata?.title ?? 'attorney'
  }
  
  console.log('📤 Returning user object - role:', role, 'title:', title, 'avatar_url:', avatar_url) // Debug log
  console.log('📤 Full return object:', { id: user.id, email: user.email || '', role, title, full_name, avatar_url })
  // #region agent log
  const returnUser = {
    id: user.id,
    email: user.email || '',
    role: role,
    title: title,
    full_name: full_name,
    avatar_url: avatar_url || undefined, // Explicitly convert null to undefined
  };
  fetch('http://127.0.0.1:7242/ingest/5a0998ac-8afa-45a8-961d-0dd6f96371b5',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'supabase-auth.ts:177',message:'Returning user object with avatar_url',data:{userId:returnUser.id,avatarUrl:returnUser.avatar_url,hasAvatarUrl:!!returnUser.avatar_url,returnObject:returnUser},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'H1'})}).catch(()=>{});
  // #endregion
  return returnUser;
}

/**
 * Convert Supabase User to app user format (legacy - uses metadata only)
 */
export function mapSupabaseUser(user: User | null): SupabaseUser | null {
  if (!user) return null
  
  return {
    id: user.id,
    email: user.email || '',
    role: user.user_metadata?.role || 'user',
    title: user.user_metadata?.title || 'attorney',
    full_name: user.user_metadata?.full_name || user.user_metadata?.fullName || undefined,
    avatar_url: user.user_metadata?.avatar_url || undefined,
  }
}

/**
 * Update user metadata
 */
export async function updateUserMetadata(updates: { full_name?: string; role?: string }) {
  const { data, error } = await supabase.auth.updateUser({
    data: updates
  })
  
  if (error) throw error
  return data
}

/**
 * Reset password
 */
export async function resetPassword(email: string) {
  const { data, error } = await supabase.auth.resetPasswordForEmail(email, {
    redirectTo: `${window.location.origin}/reset-password`,
  })
  
  if (error) throw error
  return data
}

