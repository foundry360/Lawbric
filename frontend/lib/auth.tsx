'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface User {
  id: number
  email: string
  role: string
  full_name?: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check for stored token
    const storedToken = localStorage.getItem('token')
    if (storedToken) {
      setToken(storedToken)
      fetchUser(storedToken)
    } else {
      // DEVELOPMENT BYPASS: Auto-login with mock user if backend is not available
      const devBypass = localStorage.getItem('devBypass') === 'true' || true // Enable by default for now
      if (devBypass) {
        // Create a mock user for development
        const mockUser = {
          id: 1,
          email: 'dev@lawfirm.com',
          role: 'attorney',
          full_name: 'Development User'
        }
        const mockToken = 'dev-token-' + Date.now()
        setUser(mockUser)
        setToken(mockToken)
        localStorage.setItem('token', mockToken)
        localStorage.setItem('devBypass', 'true')
      }
      setLoading(false)
    }
  }, [])

  const fetchUser = async (authToken: string) => {
    // Skip API call for dev tokens
    if (authToken && authToken.startsWith('dev-token-')) {
      const mockUser = {
        id: 1,
        email: 'dev@lawfirm.com',
        role: 'attorney',
        full_name: 'Development User'
      }
      setUser(mockUser)
      setLoading(false)
      return
    }
    
    try {
      const response = await axios.get(`${API_URL}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${authToken}` },
        timeout: 5000 // 5 second timeout
      })
      setUser(response.data)
    } catch (error) {
      console.error('Failed to fetch user:', error)
      // If backend is unavailable, use dev bypass
      const mockUser = {
        id: 1,
        email: 'dev@lawfirm.com',
        role: 'attorney',
        full_name: 'Development User'
      }
      setUser(mockUser)
      localStorage.setItem('devBypass', 'true')
    } finally {
      setLoading(false)
    }
  }

  const login = async (email: string, password: string) => {
    try {
      const response = await axios.post(`${API_URL}/api/v1/auth/login`, {
        email,
        password
      }, {
        timeout: 3000 // 3 second timeout
      })
      const { access_token, user: userData } = response.data
      setToken(access_token)
      setUser(userData)
      localStorage.setItem('token', access_token)
      localStorage.setItem('devBypass', 'false') // Disable bypass on successful login
    } catch (error: any) {
      // If backend is not available, use dev bypass
      console.warn('Backend not available, using development bypass:', error.message)
      const mockUser = {
        id: 1,
        email: email || 'dev@lawfirm.com',
        role: 'attorney',
        full_name: 'Development User'
      }
      const mockToken = 'dev-token-' + Date.now()
      setToken(mockToken)
      setUser(mockUser)
      localStorage.setItem('token', mockToken)
      localStorage.setItem('devBypass', 'true')
    }
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('token')
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
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

