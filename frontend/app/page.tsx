'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Image from 'next/image'
import LoginForm from '@/components/LoginForm'
import { useAuth } from '@/lib/auth'

export default function Home() {
  const { user, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && user) {
      router.push('/dashboard')
    }
  }, [user, loading, router])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-white">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <Image 
              src="/logo.png" 
              alt="Legal Discovery AI Logo" 
              width={200} 
              height={80}
              className="h-auto w-auto max-w-full"
              style={{ width: 'auto', height: 'auto' }}
              priority
            />
          </div>
          <p className="text-gray-600">
            AI-powered document analysis for legal professionals
          </p>
        </div>
        <LoginForm />
      </div>
    </div>
  )
}



