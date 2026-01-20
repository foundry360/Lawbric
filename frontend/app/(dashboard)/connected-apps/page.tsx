'use client'

import { useState, useEffect } from 'react'
import { integrationsApi } from '@/lib/api'
import { Plug2, Loader2, AlertCircle } from 'lucide-react'
import Image from 'next/image'

export default function ConnectedAppsPage() {
  const [googleDriveConnected, setGoogleDriveConnected] = useState(false)
  const [loading, setLoading] = useState(true)
  const [disconnecting, setDisconnecting] = useState(false)

  useEffect(() => {
    checkGoogleDriveStatus()
  }, [])

  const checkGoogleDriveStatus = async () => {
    setLoading(true)
    try {
      // Add timeout to prevent hanging
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Request timeout')), 10000)
      )
      const response = await Promise.race([
        integrationsApi.google.getStatus(),
        timeoutPromise
      ]) as any
      setGoogleDriveConnected(response.data.connected)
    } catch (error: any) {
      console.error('Failed to check Google Drive status:', error)
      // If it's an auth error (401), don't assume disconnected - token might just be expired
      // Only set to false if we're sure it's not an auth issue
      if (error.response?.status === 401) {
        // Auth error - could be expired session token, not necessarily disconnected
        // Keep current state rather than assuming disconnected
        console.warn('Auth error checking Google Drive status - token may be expired')
      } else {
        // Other errors (network, etc.) - assume disconnected
        setGoogleDriveConnected(false)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleConnectGoogleDrive = async () => {
    try {
      const response = await integrationsApi.google.getAuthUrl()
      window.location.href = response.data.url
    } catch (error: any) {
      console.error('Failed to get Google Drive auth URL:', error)
      alert(error.response?.data?.detail || 'Failed to connect to Google Drive')
    }
  }

  const handleDisconnectGoogleDrive = async () => {
    if (!confirm('Are you sure you want to disconnect Google Drive? You will need to reconnect to import files.')) {
      return
    }

    setDisconnecting(true)
    try {
      await integrationsApi.google.disconnect()
      setGoogleDriveConnected(false)
    } catch (error: any) {
      console.error('Failed to disconnect Google Drive:', error)
      alert(error.response?.data?.detail || 'Failed to disconnect Google Drive')
    } finally {
      setDisconnecting(false)
    }
  }


  return (
    <div className="h-full overflow-y-auto p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">App Directory</h1>
          <p className="text-gray-600 mt-2">Manage integrations and connected third-party applications</p>
        </div>

        {/* Available Apps */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-8">
            <div 
              className="relative border border-gray-200 rounded-lg hover:shadow-lg transition-shadow bg-white p-4"
            >
              {/* Toggle Switch - Top Right */}
              <div className="absolute top-3 right-3">
                <button
                  onClick={googleDriveConnected ? handleDisconnectGoogleDrive : handleConnectGoogleDrive}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                    googleDriveConnected 
                      ? 'bg-black hover:bg-gray-800' 
                      : 'bg-gray-200 hover:bg-gray-300'
                  }`}
                  role="switch"
                  aria-checked={googleDriveConnected}
                >
                  <span 
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      googleDriveConnected ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
              
              {/* Left-aligned content */}
              <div className="flex flex-col pr-12">
                <div className="w-10 h-10 flex items-center justify-center flex-shrink-0 overflow-hidden mb-2">
                  <Image
                    src="/Google_Drive_logo.png"
                    alt="Google Drive"
                    width={40}
                    height={40}
                    className="object-contain"
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium text-gray-900 mb-1">Google Drive</h3>
                  <p className="text-xs text-gray-500 line-clamp-2">Import documents directly from your Google Drive account</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}


