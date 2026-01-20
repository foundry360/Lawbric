'use client'

import Sidebar from '@/components/Sidebar'
import { useAuth } from '@/lib/auth'
import { useRouter } from 'next/navigation'
import { useEffect, useState, useRef } from 'react'
import { Fullscreen, LogOut, Search, Settings, X } from 'lucide-react'
import Image from 'next/image'
import { getUserProfile } from '@/lib/supabase-auth'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { user, loading, logout } = useAuth()
  const router = useRouter()
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isSearchExpanded, setIsSearchExpanded] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [isInitialLoad, setIsInitialLoad] = useState(true)
  const [isOnline, setIsOnline] = useState(true)
  const [isBackendReachable, setIsBackendReachable] = useState(true)
  const [showLogoutModal, setShowLogoutModal] = useState(false)

  useEffect(() => {
    // Listen for fullscreen changes
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }

    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange)
    }
  }, [])

  useEffect(() => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9000'
    let healthCheckInterval: NodeJS.Timeout | null = null
    let isMounted = true

    // Track browser online/offline status
    const handleOnline = () => {
      if (isMounted) setIsOnline(true)
    }
    const handleOffline = () => {
      if (isMounted) setIsOnline(false)
    }
    
    // Set initial browser status
    const browserOnline = navigator.onLine
    if (isMounted) setIsOnline(browserOnline)
    
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    
    // Check backend health
    const checkBackendHealth = async () => {
      // Debug logging disabled - was causing connection refused errors
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 5000) // 5 second timeout
        
        const response = await fetch(`${API_URL}/health`, {
          method: 'GET',
          signal: controller.signal,
          cache: 'no-cache'
        })
        
        clearTimeout(timeoutId)
        
        if (isMounted) {
          setIsBackendReachable(response.ok)
        }
      } catch (error: any) {
        // Debug logging disabled
        // Backend is unreachable (network error, timeout, CORS, etc.)
        if (isMounted) {
          setIsBackendReachable(false)
        }
      }
    }

    // Initial health check
    checkBackendHealth()

    // Periodic health checks every 30 seconds
    healthCheckInterval = setInterval(checkBackendHealth, 30000)
    
    return () => {
      isMounted = false
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
      if (healthCheckInterval) {
        clearInterval(healthCheckInterval)
      }
    }
  }, [])

  // Combined status: offline if browser is offline OR backend is unreachable
  const combinedOnlineStatus = isOnline && isBackendReachable

  const toggleFullscreen = async () => {
    try {
      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen()
        setIsFullscreen(true)
      } else {
        await document.exitFullscreen()
        setIsFullscreen(false)
      }
    } catch (error) {
      console.error('Error toggling fullscreen:', error)
    }
  }

  const handleLogout = () => {
    setShowLogoutModal(true)
  }

  const confirmLogout = async () => {
    setShowLogoutModal(false)
    
    // Perform logout cleanup
    await logout()
    
    // Subtle redirect to login
    router.replace('/')
  }

  useEffect(() => {
    // Mark initial load as complete once auth is loaded
    if (!loading) {
      setIsInitialLoad(false)
    }
    // Safety timeout: force initial load to complete after 5 seconds
    const timeout = setTimeout(() => {
      setIsInitialLoad(false)
    }, 5000)
    return () => clearTimeout(timeout)
  }, [loading])

  useEffect(() => {
    // Allow dev bypass users to access dashboard
    try {
      const devBypass = typeof window !== 'undefined' && localStorage.getItem('devBypass') === 'true'
      const storedToken = typeof window !== 'undefined' ? localStorage.getItem('token') : null
      
      // Only redirect if:
      // 1. Not on initial load (give auth time to initialize)
      // 2. Auth has finished loading (loading === false)
      // 3. No user in state
      // 4. No dev bypass
      // 5. No stored token (if there's a token, we might still be loading the user)
      if (!isInitialLoad && !loading && !user && !devBypass && !storedToken) {
        // Small delay to avoid flash
        const timer = setTimeout(() => {
          router.push('/')
        }, 100)
        return () => clearTimeout(timer)
      }
    } catch (e) {
      // localStorage might not be available
      console.warn('localStorage access failed in dashboard layout:', e)
    }
  }, [user, loading, router, isInitialLoad])

  // Only show full loading screen on initial mount, not during navigation
  // Also check for dev bypass and stored token to avoid showing loading unnecessarily
  const devBypass = typeof window !== 'undefined' && localStorage.getItem('devBypass') === 'true'
  const storedToken = typeof window !== 'undefined' ? localStorage.getItem('token') : null
  const loadingTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  
  useEffect(() => {
    // If loading takes too long, force it to false
    // But only if we don't have a stored token (which means we might be authenticating)
    if (isInitialLoad && loading && !user && !devBypass && !storedToken) {
      loadingTimeoutRef.current = setTimeout(() => {
        console.warn('Loading timeout - forcing loading to false')
        // Don't set loading here, let auth context handle it
        // But we can set isInitialLoad to false to show dashboard
        setIsInitialLoad(false)
      }, 2000) // 2 second max loading
    }
    
    return () => {
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current)
      }
    }
  }, [isInitialLoad, loading, user, devBypass, storedToken])
  
  // Show loading screen if:
  // - On initial load AND
  // - Still loading AND
  // - No user yet AND
  // - But we have a token (meaning we're probably authenticating) OR no token and no dev bypass
  // BUT: Don't show loading screen for more than 3 seconds to prevent infinite loading
  const [maxLoadingTimeReached, setMaxLoadingTimeReached] = useState(false)
  useEffect(() => {
    const timeout = setTimeout(() => {
      setMaxLoadingTimeReached(true)
    }, 3000)
    return () => clearTimeout(timeout)
  }, [])
  
  if (isInitialLoad && loading && !user && (storedToken || (!devBypass && !storedToken)) && !maxLoadingTimeReached) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-lg text-gray-600">Loading...</div>
      </div>
    )
  }

  // Allow dev bypass or stored token - show dashboard even without user if we have authentication evidence
  // This prevents redirect loop while auth is initializing
  if (!user && !devBypass && !storedToken) {
    return null
  }

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      {/* Full-width Header */}
      <header className="h-16 border-b border-gray-200 bg-white flex items-center justify-between px-6 flex-shrink-0">
        {/* Logo - left justified */}
        <div className="flex items-center">
          <Image 
            src="/logo.png" 
            alt="Legal Discovery AI Logo" 
            width={120} 
            height={40}
            className="h-10 w-auto"
          />
        </div>
        <div className="flex-1"></div>
        <div className="flex items-center gap-4">
          {/* Expandable Search */}
          <div className="relative">
            {isSearchExpanded ? (
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search cases, documents, or queries..."
                    className="w-80 pl-10 pr-4 py-2 border-0 outline-none rounded-lg focus:outline-none focus:ring-0 text-sm text-gray-900 bg-gray-100 placeholder:text-gray-400"
                    autoFocus
                    onBlur={() => {
                      if (!searchQuery) {
                        setIsSearchExpanded(false)
                      }
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Escape') {
                        setSearchQuery('')
                        setIsSearchExpanded(false)
                      }
                    }}
                  />
                </div>
              </div>
            ) : (
              <button
                onClick={() => setIsSearchExpanded(true)}
                className="p-2 rounded-lg hover:bg-gray-100 text-gray-600 hover:text-gray-900 transition-colors"
                title="Search"
              >
                <Search className="w-5 h-5" />
              </button>
            )}
          </div>
          <button
            onClick={toggleFullscreen}
            className="p-2 rounded-lg hover:bg-gray-100 text-gray-600 hover:text-gray-900 transition-colors"
            title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
          >
            <Fullscreen className="w-5 h-5" />
          </button>
              <button
                onClick={() => router.push('/settings')}
                className="p-2 rounded-lg hover:bg-gray-100 text-gray-600 hover:text-gray-900 transition-colors"
                title="Settings"
              >
                <Settings className="w-5 h-5" />
              </button>
          <button
            onClick={handleLogout}
            className="p-2 rounded-lg hover:bg-gray-100 text-gray-600 hover:text-gray-900 transition-colors"
            title="Logout"
          >
            <LogOut className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-sm font-medium text-gray-900">{user?.full_name || user?.email || 'Development User'}</p>
              <p className="text-xs text-gray-600 capitalize">{user?.title || user?.role || 'attorney'}</p>
            </div>
            {user?.avatar_url && user.avatar_url.trim() !== '' ? (
              <div className="relative w-10 h-10 rounded-full">
                <div className="w-10 h-10 rounded-full overflow-hidden border-2 border-gray-200 bg-gray-100">
                  <img
                    src={user.avatar_url}
                    alt="Profile avatar"
                    className="w-full h-full object-cover"
                    key={`avatar-${user.id}-${user.avatar_url}`}
                  />
                </div>
                <div className={`absolute bottom-0 right-0 w-3 h-3 rounded-full border-2 border-white ${combinedOnlineStatus ? 'bg-green-500' : 'bg-red-500'}`}></div>
              </div>
            ) : (
              <div className="relative w-10 h-10 rounded-full">
                <div className="w-10 h-10 rounded-full bg-primary-600 flex items-center justify-center text-white font-semibold">
                  {((user?.full_name || user?.email || 'DU')[0]).toUpperCase()}
                </div>
                <div className={`absolute bottom-0 right-0 w-3 h-3 rounded-full border-2 border-white ${combinedOnlineStatus ? 'bg-green-500' : 'bg-red-500'}`}></div>
              </div>
            )}
          </div>
        </div>
      </header>
      
      {/* Content area with sidebar and main */}
      <div className="flex flex-1 overflow-hidden bg-white">
        <Sidebar />
        <main className="flex-1 overflow-hidden bg-white transition-opacity duration-200">
          {children}
        </main>
      </div>

      {/* Logout Confirmation Modal */}
      {showLogoutModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg py-10 px-6 w-full max-w-lg relative shadow-2xl">
            {/* Close Button */}
            <button
              onClick={() => setShowLogoutModal(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
            
            <div className="space-y-4 text-center">
              <p className="text-xl font-medium text-gray-900">
                You are attempting to log out of Lawbric
              </p>
              <p className="text-lg text-gray-900">
                Are you sure?
              </p>
              <p className="text-xs text-gray-500">
                logged in as {user?.email || user?.full_name || 'user'}
              </p>
              <div className="flex justify-center pt-4">
                <button
                  onClick={confirmLogout}
                  className="px-16 py-2 bg-black text-white rounded-lg hover:bg-gray-900 transition-colors font-medium text-sm"
                >
                  LOG OUT
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}

