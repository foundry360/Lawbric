'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9001'

// Log API URL in development to help debug connection issues
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  console.log('API URL configured as:', API_URL)
}

interface User {
  id: number
  email: string
  role: string  // admin, attorney, paralegal
  title: string  // attorney, paralegal, finance, etc. (job title - required)
  full_name?: string
  avatar_url?: string  // URL to profile avatar
  tenant_id?: number
  tenant_name?: string
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

  useEffect(() => {
    // Check for stored token on mount
    if (typeof window !== 'undefined') {
      const storedToken = localStorage.getItem('token')
      if (storedToken) {
        setToken(storedToken)
        // Add safety timeout to ensure loading is always set to false
        const safetyTimeout = setTimeout(() => {
          console.warn('Auth check safety timeout reached, forcing loading to false')
          setLoading(false)
        }, 10000) // 10 second maximum timeout
        
        loadUser(storedToken).finally(() => {
          clearTimeout(safetyTimeout)
        })
      } else {
        setLoading(false)
      }
    } else {
      setLoading(false)
    }
  }, [])

  const loadUser = async (authToken: string) => {
    try {
      console.log('Attempting to load user from:', `${API_URL}/api/v1/auth/me`)
      // Use a more aggressive timeout and better error handling
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 8000)
      
      try {
        const response = await axios.get(`${API_URL}/api/v1/auth/me`, {
          headers: { Authorization: `Bearer ${authToken}` },
          timeout: 8000,
          signal: controller.signal
        })
        clearTimeout(timeoutId)
        setUser(response.data)
        console.log('User loaded successfully')
      } catch (requestError: any) {
        clearTimeout(timeoutId)
        if (requestError.code === 'ERR_NETWORK' || requestError.message === 'Network Error') {
          console.error('Network error connecting to backend at:', API_URL)
          console.error('Please ensure the backend is running and accessible')
        }
        throw requestError
      }
    } catch (error: any) {
      console.error('Failed to load user:', error)
      // Token might be invalid - clear it
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token')
      }
      setToken(null)
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  // Check if backend is ready before making requests
  const checkBackendHealth = async (maxRetries = 6, delay = 1200): Promise<boolean> => {
    for (let i = 0; i < maxRetries; i++) {
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 5000) // Reduced timeout
        
        const response = await fetch(`${API_URL}/health`, {
          method: 'GET',
          signal: controller.signal,
          cache: 'no-cache',
          headers: {
            'Accept': 'application/json',
          }
        })
        
        clearTimeout(timeoutId)
        
        if (response.ok) {
          const data = await response.json()
          // Check if database is connected (if health check includes this)
          if (data.status === 'healthy' || data.status === 'degraded') {
            return true
          }
        }
      } catch (error: any) {
        // Log specific error types for debugging
        if (error.name === 'AbortError') {
          console.log(`Health check attempt ${i + 1}/${maxRetries} timed out, retrying...`)
        } else if (error.message?.includes('ERR_EMPTY_RESPONSE') || error.message?.includes('Connection closed')) {
          console.log(`Health check attempt ${i + 1}/${maxRetries} failed: Backend connection closed. The backend may need to be restarted.`)
        } else {
          console.log(`Health check attempt ${i + 1}/${maxRetries} failed: ${error.message || error}`)
        }
      }
      
      if (i < maxRetries - 1) {
        await new Promise((resolve) => setTimeout(resolve, delay))
        delay *= 1.5 // Exponential backoff
      }
    }
    return false
  }

  const login = async (email: string, password: string) => {
    try {
      // Check backend health before attempting login
      const isReady = await checkBackendHealth()

      const attemptLogin = async (attempt: number): Promise<any> => {
        try {
          return await axios.post(
            `${API_URL}/api/v1/auth/login`,
            { email, password },
            { timeout: 30000 }
          )
        } catch (err: any) {
          const isNetwork =
            err?.code === 'ERR_NETWORK' ||
            err?.code === 'ECONNABORTED' ||
            err?.message === 'Network Error' ||
            err?.message?.includes('ERR_EMPTY_RESPONSE')

          if (isNetwork && attempt < 3) {
            const delay = Math.pow(2, attempt - 1) * 1000
            await new Promise((resolve) => setTimeout(resolve, delay))
            return attemptLogin(attempt + 1)
          }
          throw err
        }
      }

      if (!isReady) {
        // Backend may still accept login even if health check fails; try anyway.
        console.warn('Health check failed, attempting login anyway...')
      }

      const response = await attemptLogin(1)
      
      const { access_token } = response.data
      setToken(access_token)
      if (typeof window !== 'undefined') {
        localStorage.setItem('token', access_token)
      }
      
      // Load user info
      await loadUser(access_token)
    } catch (error: any) {
      console.error('Login error:', error)
      let errorMessage = 'Invalid email or password'
      
      if (error.message?.includes('Backend is not ready')) {
        errorMessage = error.message
      } else if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
        errorMessage = 'Unable to connect to server. Please ensure the backend is running and try again.'
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.message) {
        errorMessage = error.message
      }
      
      throw new Error(errorMessage)
    }
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token')
    }
  }

  const refreshUser = async () => {
    if (token) {
      await loadUser(token)
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


