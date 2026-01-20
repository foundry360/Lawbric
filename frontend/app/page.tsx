'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import LoginForm from '@/components/LoginForm'
import { useAuth } from '@/lib/auth'

export default function Home() {
  const { user, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    // Only redirect if user is already logged in (not during login process)
    // Check if we're still on home page to avoid double redirects
    if (!loading && user && typeof window !== 'undefined') {
      const currentPath = window.location.pathname
      if (currentPath === '/' || currentPath === '') {
        // Use replace instead of push to avoid adding to history
        router.replace('/workspace')
      }
    }
  }, [user, loading, router])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <div className="text-lg text-gray-900">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-white">
      <div className="w-full max-w-md">
        <LoginForm />
      </div>
    </div>
  )
}



