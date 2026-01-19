'use client'

import { createContext, useContext, useState, useEffect, useRef, ReactNode } from 'react'
import { supabase } from './supabase'
import { signIn, signUp, getSession, getCurrentUser, onAuthStateChange, mapSupabaseUser, mapSupabaseUserWithProfile } from './supabase-auth'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface User {
  id: string | number
  email: string
  role: string  // user or admin (permissions)
  title?: string  // attorney, paralegal, finance, etc. (job title)
  full_name?: string
  avatar_url?: string  // URL to profile avatar in Supabase storage
}

interface AuthContextType {
  user: User | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const hasInitializedRef = useRef(false)

  useEffect(() => {
    // If already initialized, ensure loading state is correct
    if (hasInitializedRef.current) {
      // If we have user or token, loading should be false
      if ((user || token) && loading) {
        setLoading(false)
        return
      }
      
      // If still loading but no user/token, check localStorage and set loading to false
      // This prevents infinite loading if initialization didn't complete
      if (loading && !user && !token) {
        if (typeof window !== 'undefined') {
          const storedToken = localStorage.getItem('token')
          const devBypass = localStorage.getItem('devBypass') === 'true'
          
          if (storedToken || devBypass) {
            // We have a token or dev bypass, so we're authenticated
            // Set loading to false - user data will load in background if needed
            setLoading(false)
          } else {
            // No token and no dev bypass - set loading to false anyway after short delay
            // This prevents infinite loading screen
            const timeout = setTimeout(() => {
              setLoading(false)
            }, 500)
            return () => clearTimeout(timeout)
          }
        } else {
          // Server-side, just set loading to false
          setLoading(false)
        }
      }
      return
    }
    
    let mounted = true
    let safetyTimeout: NodeJS.Timeout | null = null
    let supabaseUserLoaded = false // Track if Supabase successfully loaded user

    const initializeAuth = async () => {
      hasInitializedRef.current = true
      
      // Quick check: if we already have user/token in state, skip loading
      if (user || token) {
        setLoading(false)
        return
      }
      
      // Quick check: if we have token in localStorage, set loading false early
      if (typeof window !== 'undefined') {
        const storedToken = localStorage.getItem('token')
        if (storedToken) {
          // We have a token, so we're likely authenticated - don't show loading
          // But still try to get user data in background
        }
      }
      // Safety timeout to ensure loading is always set to false
      // This prevents infinite loading if something goes wrong
      safetyTimeout = setTimeout(() => {
        if (mounted) {
          console.warn('Auth loading timeout - forcing loading to false')
          setLoading(false)
        }
      }, 5000) // 5 second timeout - should be enough for auth to complete

      try {
        // Wait for client-side only
        if (typeof window === 'undefined') {
          setLoading(false)
          if (safetyTimeout) clearTimeout(safetyTimeout)
          return
        }

        // Try Supabase first
        try {
          // Supabase might need a moment to restore session from localStorage
          // Wait a bit before checking session
          await new Promise(resolve => setTimeout(resolve, 100))
          
          // Add timeout for getSession to prevent hanging
          const sessionPromise = getSession()
          const timeoutPromise = new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Session timeout')), 8000) // Increased timeout to 8s
          )
          const session = await Promise.race([sessionPromise, timeoutPromise]) as any
          if (session?.user && session?.access_token) {
            // Fetch user with profile to get accurate role from profiles table
            const appUser = await mapSupabaseUserWithProfile(session.user)
            if (appUser) {
              // Mark that Supabase successfully loaded a user
              supabaseUserLoaded = true
              
              // Always set user if we have appUser, even if mounted is false
              // The component might have unmounted during async operations, but we still want to restore the session
              console.log('✅ Loaded user with role from profile:', appUser.role)
              setUser({
                id: appUser.id,
                email: appUser.email,
                role: appUser.role || 'user',
                title: appUser.title,
                full_name: appUser.full_name,
                avatar_url: appUser.avatar_url
              })
              // Store Supabase access token (not user ID)
              setToken(session.access_token)
              if (typeof window !== 'undefined') {
                localStorage.setItem('token', session.access_token)
              }
              if (safetyTimeout) clearTimeout(safetyTimeout)
              setLoading(false)
              return
            }
          } else {
            // No active session, but check if we have a stored token
            // This handles the case where session expired but we still have a token
            const storedToken = typeof window !== 'undefined' ? localStorage.getItem('token') : null
            if (storedToken && !storedToken.startsWith('dev-token-')) {
              // We have a stored Supabase token, but getSession() returned null
              // This might mean the session expired. Try to get user directly which might trigger a refresh
              console.log('No active Supabase session, but found stored token, trying to get user...')
              try {
                // Try to get the user directly - this might refresh the session automatically
                const currentUser = await getCurrentUser()
                if (currentUser) {
                  // Got user, now get session again
                  const newSession = await getSession()
                  if (newSession?.access_token) {
                    const appUser = await mapSupabaseUserWithProfile(currentUser)
                    if (appUser && mounted) {
                      console.log('✅ Restored session and loaded user:', appUser.role)
                      setUser({
                        id: appUser.id,
                        email: appUser.email,
                        role: appUser.role || 'user',
                        title: appUser.title,
                        full_name: appUser.full_name,
                        avatar_url: appUser.avatar_url
                      })
                      setToken(newSession.access_token)
                      if (typeof window !== 'undefined') {
                        localStorage.setItem('token', newSession.access_token)
                      }
                      if (safetyTimeout) clearTimeout(safetyTimeout)
                      setLoading(false)
                      return
                    }
                  }
                }
              } catch (getUserError) {
                console.log('Could not get user, will check legacy auth:', getUserError)
              }
              // If that failed, continue to legacy auth check below
            }
          }
        } catch (supabaseError) {
          // Supabase not available or not configured, fall through to legacy auth
          console.log('Supabase auth not available, trying legacy auth:', supabaseError)
          // Make sure we continue to legacy auth even if Supabase fails
        }

        // Check for stored token (legacy auth) - but only if Supabase didn't already load a user
        // If Supabase already loaded a user, don't check legacy auth
        if (supabaseUserLoaded) {
          if (safetyTimeout) clearTimeout(safetyTimeout)
          return
        }
        
        const storedToken = localStorage.getItem('token')
        
        if (storedToken && storedToken.startsWith('dev-token-')) {
          // Dev token - set user immediately
          const mockUser = {
            id: 1,
            email: 'dev@lawfirm.com',
            role: 'attorney',
            full_name: 'Development User'
          }
          if (mounted) {
            setUser(mockUser)
            setToken(storedToken)
            setLoading(false)
            if (safetyTimeout) clearTimeout(safetyTimeout)
          }
          return
        }

        if (storedToken) {
          // Real token - try to fetch user from backend
          setToken(storedToken)
          try {
            const response = await axios.get(`${API_URL}/api/v1/auth/me`, {
              headers: { Authorization: `Bearer ${storedToken}` },
              timeout: 3000
            })
            if (mounted) {
              setUser(response.data)
              setLoading(false)
              if (safetyTimeout) clearTimeout(safetyTimeout)
            }
          } catch (error) {
            // Backend unavailable - don't create dev user automatically
            // If the token is a Supabase token, we should have gotten user from Supabase already
            // If we're here, it means we have a token but can't validate it - likely an expired token
            console.warn('Backend unavailable or token invalid:', error)
            // Don't set user - let the dashboard layout redirect to login
            if (mounted) {
              setLoading(false)
              if (safetyTimeout) clearTimeout(safetyTimeout)
            }
          }
        } else {
          // No token - don't create dev user automatically
          // Let the user go to login page instead
          if (mounted) {
            setLoading(false)
            if (safetyTimeout) clearTimeout(safetyTimeout)
          }
          // Don't set user - this will allow the dashboard layout to redirect to login
        }
      } catch (error) {
        // Any error - don't create dev user, just set loading to false
        // This allows the dashboard layout to handle redirect to login
        console.warn('Auth initialization error:', error)
        if (mounted) {
          setLoading(false)
          if (safetyTimeout) clearTimeout(safetyTimeout)
        }
      }
    }

    initializeAuth()

    // Listen for Supabase auth changes
    const { data: { subscription } } = onAuthStateChange((event, session) => {
      if (!mounted) return

      if (event === 'SIGNED_IN' && session?.user) {
        // Fetch user with profile to get accurate role from profiles table
        mapSupabaseUserWithProfile(session.user).then((appUser) => {
          if (appUser && session.access_token && mounted) {
            console.log('✅ User signed in with role from profile:', appUser.role)
            setUser({
              id: appUser.id,
              email: appUser.email,
              role: appUser.role || 'user',
              title: appUser.title,
              full_name: appUser.full_name,
              avatar_url: appUser.avatar_url
            })
            // Store Supabase access token (not user ID)
            setToken(session.access_token)
            if (typeof window !== 'undefined') {
              localStorage.setItem('token', session.access_token)
            }
            setLoading(false)
          }
        }).catch((error) => {
          console.error('Error fetching user profile in auth state change:', error)
          // Fall back to basic user if profile fetch fails
          const basicUser = mapSupabaseUser(session.user)
          if (basicUser && session.access_token && mounted) {
            setUser({
              id: basicUser.id,
              email: basicUser.email,
              role: basicUser.role || 'user',
              title: basicUser.title,
              full_name: basicUser.full_name,
              avatar_url: basicUser.avatar_url
            })
            setToken(session.access_token)
            if (typeof window !== 'undefined') {
              localStorage.setItem('token', session.access_token)
            }
            setLoading(false)
          }
        })
      } else if (event === 'SIGNED_OUT') {
        setUser(null)
        setToken(null)
        localStorage.removeItem('token')
        localStorage.removeItem('devBypass')
      }
    })

    return () => {
      mounted = false
      if (safetyTimeout) clearTimeout(safetyTimeout)
      subscription.unsubscribe()
    }
  }, []) // Empty dependency array - only run once on mount

  const login = async (email: string, password: string) => {
    // Check if Supabase is properly configured
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
    const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''
    
    if (!supabaseUrl || !supabaseKey || supabaseUrl === 'https://placeholder.supabase.co') {
      console.error('❌ Supabase not configured. Please check your .env.local file.')
      throw new Error('Supabase is not configured. Please check environment variables.')
    }

    try {
      // Try Supabase authentication first
      console.log('🔐 Attempting Supabase sign in...')
      const { data: signInData, error: signInError } = await supabase.auth.signInWithPassword({
        email,
        password,
      })

      if (signInError) {
        console.log('⚠️ Sign in error:', signInError.message)
        
        // If sign in fails - don't auto-create accounts
        // Users must be created by admin in settings
        throw new Error('Invalid email or password. Please contact your administrator for access.')
      }

      if (signInData.user && signInData.session) {
        console.log('✅ Sign in successful! User:', signInData.user.id)
        // Sign in successful - fetch profile to get accurate role from profiles table
        const appUser = await mapSupabaseUserWithProfile(signInData.user)
        if (appUser) {
          console.log('✅ Loaded user with role from profile:', appUser.role)
          setUser({
            id: appUser.id,
            email: appUser.email,
            role: appUser.role || 'user',
            title: appUser.title,
            full_name: appUser.full_name
          })
          // Store Supabase access token (not user ID)
          const accessToken = signInData.session.access_token
          setToken(accessToken)
          // Store token in localStorage for API calls
          if (typeof window !== 'undefined') {
            localStorage.setItem('token', accessToken)
            localStorage.removeItem('devBypass')
          }
          console.log('✅ User logged in successfully')
          return
        }
      }

      throw new Error('Unexpected error during authentication')
    } catch (error: any) {
      // If it's already a user-friendly error, re-throw it
      if (error.message && !error.message.includes('Failed to fetch') && !error.message.includes('Network')) {
        console.error('❌ Auth error:', error.message)
        throw error
      }

      // Network/connection error - try legacy backend
      console.log('⚠️ Supabase auth failed, trying legacy backend:', error.message)
      
      try {
        const response = await axios.post(`${API_URL}/api/v1/auth/login`, {
          email,
          password
        }, {
          timeout: 3000
        })
        
        const { access_token, user: userData } = response.data
        setToken(access_token)
        setUser(userData)
        if (typeof window !== 'undefined') {
          localStorage.setItem('token', access_token)
          localStorage.setItem('devBypass', 'false')
        }
      } catch (legacyError: any) {
        // If all auth methods fail, throw the original error
        console.error('❌ All auth methods failed')
        throw new Error(error.message || 'Authentication failed. Please check your credentials and try again.')
      }
    }
  }

  const logout = async () => {
    try {
      // Sign out from Supabase
      await supabase.auth.signOut()
    } catch (error) {
      console.warn('Supabase sign out failed:', error)
    }
    
    setToken(null)
    setUser(null)
    try {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token')
        localStorage.removeItem('devBypass')
      }
    } catch (e) {
      // localStorage might not be available
    }
  }

  const refreshUser = async () => {
    try {
      // Get current session
      const session = await getSession()
      if (session?.user) {
        // Fetch user with profile to get updated data including avatar
        const appUser = await mapSupabaseUserWithProfile(session.user)
        if (appUser) {
          console.log('Refreshing user - avatar_url:', appUser.avatar_url)
          setUser({
            id: appUser.id,
            email: appUser.email,
            role: appUser.role || 'user',
            title: appUser.title,
            full_name: appUser.full_name,
            avatar_url: appUser.avatar_url || undefined // Explicitly handle null
          })
          if (session.access_token) {
            setToken(session.access_token)
          }
        }
      }
    } catch (error) {
      console.error('Error refreshing user:', error)
    }
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

