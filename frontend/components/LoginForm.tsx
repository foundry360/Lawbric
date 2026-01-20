'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth'
import { useRouter } from 'next/navigation'
import Image from 'next/image'

export default function LoginForm() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login(email, password)
      // Use replace to avoid adding to history and prevent double redirects
      router.replace('/workspace')
    } catch (err: any) {
      console.error('Login error:', err)
      // Show user-friendly error messages
      let errorMessage = err.message || 'Login failed'
      
      // Handle common Supabase errors
      if (errorMessage.includes('Email not confirmed')) {
        errorMessage = 'Please check your email and confirm your account before signing in.'
      } else if (errorMessage.includes('Invalid login')) {
        errorMessage = 'Invalid email or password. If this is your first time, an account will be created.'
      } else if (errorMessage.includes('User already registered')) {
        errorMessage = 'An account with this email already exists. Please sign in instead.'
      } else if (errorMessage.includes('Password')) {
        errorMessage = 'Password must be at least 6 characters long.'
      }
      
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white shadow-lg rounded-lg p-8">
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
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
            Email
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none text-gray-900 bg-white placeholder:text-gray-400"
            placeholder="attorney@lawfirm.com"
          />
        </div>
        <div>
          <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none text-gray-900 bg-white placeholder:text-gray-400"
            placeholder="••••••••"
          />
        </div>
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-primary-600 text-white py-2 px-4 rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Logging in...' : 'Login'}
        </button>
        <p className="text-sm text-gray-500 text-center">
            Need access? Contact your law firm administrator to create an account.
        </p>
      </form>
    </div>
  )
}

