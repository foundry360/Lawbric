'use client'

import { useEffect, useState, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { integrationsApi } from '@/lib/api'
import { Loader2, CheckCircle, AlertCircle } from 'lucide-react'

export default function OAuthCallbackPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [message, setMessage] = useState('')
  const processedRef = useRef(false)

  useEffect(() => {
    // Prevent duplicate processing (React Strict Mode can cause double execution)
    if (processedRef.current) {
      return
    }

    const handleCallback = async () => {
      const code = searchParams.get('code')
      const error = searchParams.get('error')

      if (error) {
        processedRef.current = true
        setStatus('error')
        setMessage('Authorization was cancelled or failed. Please try again.')
        setTimeout(() => {
          router.push('/connected-apps')
        }, 3000)
        return
      }

      if (!code) {
        processedRef.current = true
        setStatus('error')
        setMessage('No authorization code received. Please try again.')
        setTimeout(() => {
          router.push('/connected-apps')
        }, 3000)
        return
      }

      // Mark as processed immediately to prevent duplicate calls
      processedRef.current = true

      try {
        // Use the API client to handle the callback
        const response = await integrationsApi.google.callback(code)
        setStatus('success')
        setMessage(response.data.message || 'Google Drive connected successfully!')
        setTimeout(() => {
          router.push('/connected-apps')
        }, 2000)
      } catch (err: any) {
        console.error('OAuth callback error:', err)
        setStatus('error')
        const errorMessage = err.response?.data?.detail || err.message || 'Failed to connect Google Drive. Please try again.'
        setMessage(errorMessage)
        setTimeout(() => {
          router.push('/connected-apps')
        }, 3000)
      }
    }

    handleCallback()
  }, [searchParams, router])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
        {status === 'loading' && (
          <>
            <Loader2 className="w-12 h-12 animate-spin text-gray-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Connecting Google Drive...</h2>
            <p className="text-sm text-gray-600">Please wait while we complete the connection.</p>
          </>
        )}
        {status === 'success' && (
          <>
            <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Connected!</h2>
            <p className="text-sm text-gray-600">{message}</p>
            <p className="text-xs text-gray-500 mt-2">Redirecting to App Directory...</p>
          </>
        )}
        {status === 'error' && (
          <>
            <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Connection Failed</h2>
            <p className="text-sm text-gray-600">{message}</p>
            <p className="text-xs text-gray-500 mt-2">Redirecting to App Directory...</p>
          </>
        )}
      </div>
    </div>
  )
}

