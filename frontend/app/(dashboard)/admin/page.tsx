'use client'

import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { useAuth } from '@/lib/auth'
import { useRouter } from 'next/navigation'
import { CheckCircle } from 'lucide-react'
// Removed Supabase import - using JWT auth

interface Tenant {
  id: number
  name: string
  slug: string
  description?: string
  domain?: string
  is_active: boolean
  created_at: string
  user_count: number
  case_count: number
}

interface OnboardingRequest {
  tenant: {
    name: string
    slug: string
    description?: string
    domain?: string
  }
  admin_email: string
  admin_password: string
  admin_full_name?: string
}

export default function AdminPortal() {
  const { user } = useAuth()
  const router = useRouter()
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showOnboarding, setShowOnboarding] = useState(false)
  const [onboardingData, setOnboardingData] = useState<OnboardingRequest>({
    tenant: {
      name: '',
      slug: '',
      description: ''
    },
    admin_email: '',
    admin_password: '',
    admin_full_name: ''
  })
  const [onboardingLoading, setOnboardingLoading] = useState(false)
  const [showSuccessModal, setShowSuccessModal] = useState(false)
  const [successData, setSuccessData] = useState<{ tenant_slug: string; admin_email: string } | null>(null)

  // Check if user is super admin (Lawbric employee - internal admin portal access)
  const isSuperAdmin = user?.role === 'super_admin' || user?.role === 'SUPER_ADMIN'

  useEffect(() => {
    if (!user) {
      return
    }
    
    if (!isSuperAdmin) {
      router.push('/workspace')
      return
    }
    loadTenants()
  }, [isSuperAdmin, user, router])

  const getAuthToken = (): string | null => {
    // Get JWT token from localStorage
    if (typeof window !== 'undefined') {
      return localStorage.getItem('token')
    }
    return null
  }

  const loadTenants = async () => {
    try {
      const token = getAuthToken()
      if (!token) {
        setError('Not authenticated')
        setLoading(false)
        return
      }

      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9001'
      const response = await fetch(`${API_URL}/api/v1/onboarding/clients`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        if (response.status === 403) {
          setError('Super admin access required')
          setLoading(false)
          return
        }
        throw new Error('Failed to load tenants')
      }

      const data = await response.json()
      setTenants(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load tenants')
    } finally {
      setLoading(false)
    }
  }

  const handleOnboardClient = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setOnboardingLoading(true)

    try {
      const token = getAuthToken()
      if (!token) {
        setError('Not authenticated')
        setOnboardingLoading(false)
        return
      }

      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9001'
      const response = await fetch(`${API_URL}/api/v1/onboarding/clients`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(onboardingData)
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to onboard client')
      }

      const result = await response.json()
      
      // Show success modal
      setSuccessData({
        tenant_slug: result.tenant_slug,
        admin_email: result.admin_email
      })
      setShowSuccessModal(true)
      
      // Reset form and reload tenants
      setOnboardingData({
        tenant: { name: '', slug: '', description: '' },
        admin_email: '',
        admin_password: '',
        admin_full_name: ''
      })
      setShowOnboarding(false)
      loadTenants()
    } catch (err: any) {
      setError(err.message || 'Failed to onboard client')
    } finally {
      setOnboardingLoading(false)
    }
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isSuperAdmin) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Access Denied</h1>
          <p className="text-gray-600">Super admin access required (Lawbric employees only)</p>
          <p className="text-sm text-gray-500 mt-2">Your email: {user.email}</p>
          <p className="text-sm text-gray-500 mt-1">Your role: {user.role}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-8 flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Lawbric Admin Portal</h1>
          <p className="text-gray-600">Manage clients and tenants</p>
        </div>
        <button
          onClick={() => setShowOnboarding(!showOnboarding)}
          className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-900 transition-colors"
        >
          {showOnboarding ? 'Cancel' : '+ Onboard New Client'}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg">
          {error}
        </div>
      )}

      {showOnboarding && (
        <div className="mb-8 p-6 bg-white border border-gray-200 rounded-lg shadow-sm">
          <h2 className="text-xl font-bold mb-4">Onboard New Client</h2>
          <form onSubmit={handleOnboardClient} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-900">Tenant Name *</label>
                <input
                  type="text"
                  value={onboardingData.tenant.name}
                  onChange={(e) => setOnboardingData({
                    ...onboardingData,
                    tenant: { ...onboardingData.tenant, name: e.target.value }
                  })}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black text-gray-900 bg-white"
                  placeholder="Acme Law Firm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-900">Tenant Slug *</label>
                <input
                  type="text"
                  value={onboardingData.tenant.slug}
                  onChange={(e) => {
                    // Only allow lowercase letters, numbers, hyphens, and underscores
                    const sanitized = e.target.value.toLowerCase().replace(/[^a-z0-9_-]/g, '')
                    setOnboardingData({
                      ...onboardingData,
                      tenant: { ...onboardingData.tenant, slug: sanitized }
                    })
                  }}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black text-gray-900 bg-white"
                  placeholder="acme-law"
                />
                <p className="text-xs text-gray-600 mt-1">Lowercase, numbers, hyphens, underscores only</p>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-900">Description</label>
              <textarea
                value={onboardingData.tenant.description || ''}
                onChange={(e) => setOnboardingData({
                  ...onboardingData,
                  tenant: { ...onboardingData.tenant, description: e.target.value }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black text-gray-900 bg-white"
                rows={2}
              />
            </div>
            <div className="border-t pt-4 mt-4">
              <h3 className="font-semibold mb-3 text-gray-900">Admin User</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-900">Admin Email *</label>
                  <input
                    type="email"
                    value={onboardingData.admin_email}
                    onChange={(e) => setOnboardingData({ ...onboardingData, admin_email: e.target.value })}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black text-gray-900 bg-white"
                    placeholder="admin@client.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-900">Admin Password *</label>
                  <input
                    type="password"
                    value={onboardingData.admin_password}
                    onChange={(e) => setOnboardingData({ ...onboardingData, admin_password: e.target.value })}
                    required
                    minLength={6}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black text-gray-900 bg-white"
                  />
                </div>
              </div>
              <div className="mt-4">
                <label className="block text-sm font-medium mb-2 text-gray-900">Admin Full Name</label>
                <input
                  type="text"
                  value={onboardingData.admin_full_name || ''}
                  onChange={(e) => setOnboardingData({ ...onboardingData, admin_full_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black text-gray-900 bg-white"
                  placeholder="John Doe"
                />
              </div>
            </div>
            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={() => setShowOnboarding(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-gray-900 bg-white"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={onboardingLoading}
                className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {onboardingLoading ? 'Onboarding...' : 'Onboard Client'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-bold">All Clients ({tenants.length})</h2>
        </div>
        {loading ? (
          <div className="p-8 text-center text-gray-600">Loading tenants...</div>
        ) : tenants.length === 0 ? (
          <div className="p-8 text-center text-gray-600">No tenants found. Onboard your first client above.</div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-900">Name</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-900">Slug</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-900">Users</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-900">Cases</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-900">Status</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-900">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {tenants.map((tenant) => (
                <tr key={tenant.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm text-gray-900">{tenant.name}</td>
                  <td className="px-6 py-4 text-sm text-gray-600 font-mono">{tenant.slug}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{tenant.user_count}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{tenant.case_count}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs rounded ${
                      tenant.is_active 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {tenant.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {tenant.created_at ? new Date(tenant.created_at).toLocaleDateString() : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Success Modal */}
      {showSuccessModal && successData && typeof window !== 'undefined' && createPortal(
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setShowSuccessModal(false)}>
          <div className="bg-white rounded-lg p-6 w-full max-w-md shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-3 mb-4">
              <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0" />
              <h3 className="text-lg font-bold text-gray-900">Client Onboarded Successfully</h3>
            </div>
            <div className="space-y-4">
              <div className="space-y-2">
                <div>
                  <p className="text-sm font-medium text-gray-700">Tenant Slug:</p>
                  <p className="text-sm text-gray-900 font-mono bg-gray-50 px-3 py-2 rounded mt-1">{successData.tenant_slug}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700">Admin Email:</p>
                  <p className="text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded mt-1">{successData.admin_email}</p>
                </div>
              </div>
              <div className="flex justify-end pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowSuccessModal(false)
                    setSuccessData(null)
                  }}
                  className="px-4 py-2 text-sm bg-black text-white rounded-lg hover:bg-gray-900 transition-colors"
                >
                  OK
                </button>
              </div>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  )
}


