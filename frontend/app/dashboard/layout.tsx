'use client'

import Sidebar from '@/components/Sidebar'
import { useAuth } from '@/lib/auth'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { Fullscreen, LogOut, Search, Settings } from 'lucide-react'
import Image from 'next/image'

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
    logout()
    router.push('/')
  }

  useEffect(() => {
    // Allow dev bypass users to access dashboard
    try {
      const devBypass = typeof window !== 'undefined' && localStorage.getItem('devBypass') === 'true'
      // Only redirect if we're sure there's no user and no dev bypass
      if (!loading && !user && !devBypass) {
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
  }, [user, loading, router])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    )
  }

  // Allow dev bypass - show dashboard even without user if devBypass is set
  const devBypass = typeof window !== 'undefined' && localStorage.getItem('devBypass') === 'true'
  if (!user && !devBypass) {
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
            onClick={() => router.push('/dashboard/settings')}
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
            {user?.avatar_url ? (
              <div className="relative w-10 h-10 rounded-full overflow-hidden border-2 border-gray-200">
                <Image
                  src={user.avatar_url}
                  alt="Profile avatar"
                  fill
                  className="object-cover"
                />
              </div>
            ) : (
              <div className="w-10 h-10 rounded-full bg-primary-600 flex items-center justify-center text-white font-semibold">
                {((user?.full_name || user?.email || 'DU')[0]).toUpperCase()}
              </div>
            )}
          </div>
        </div>
      </header>
      
      {/* Content area with sidebar and main */}
      <div className="flex flex-1 overflow-hidden bg-white">
        <Sidebar />
        <main className="flex-1 overflow-hidden bg-white">
          {children}
        </main>
      </div>
    </div>
  )
}

