'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { casesApi, Case } from '@/lib/api'
import { Plus, FileText, Calendar } from 'lucide-react'

export default function DashboardPage() {
  const [cases, setCases] = useState<Case[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newCaseName, setNewCaseName] = useState('')
  const [newCaseNumber, setNewCaseNumber] = useState('')
  const router = useRouter()

  useEffect(() => {
    loadCases()
    
    // Listen for custom event to open new case modal
    const handleOpenModal = () => {
      setShowCreateModal(true)
    }
    window.addEventListener('openNewCaseModal', handleOpenModal)
    
    return () => {
      window.removeEventListener('openNewCaseModal', handleOpenModal)
    }
  }, [])

  const loadCases = async () => {
    try {
      const response = await casesApi.list()
      setCases(response.data || [])
    } catch (error: any) {
      console.error('Failed to load cases:', error)
      // If backend is unavailable, use empty array (dev mode)
      if (error.code === 'ECONNREFUSED' || error.message?.includes('Network Error') || error.isDevBypass) {
        setCases([]) // Empty cases list for dev mode
      }
    } finally {
      setLoading(false)
    }
  }

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await casesApi.create({
        name: newCaseName,
        case_number: newCaseNumber || undefined,
      })
      setShowCreateModal(false)
      setNewCaseName('')
      setNewCaseNumber('')
      loadCases()
    } catch (error: any) {
      console.error('Failed to create case:', error)
      // In dev mode, create a mock case locally
      if (error.code === 'ECONNREFUSED' || error.message?.includes('Network Error') || error.isDevBypass) {
        const mockCase: Case = {
          id: Date.now(),
          name: newCaseName,
          case_number: newCaseNumber || undefined,
          description: undefined,
          created_at: new Date().toISOString(),
          updated_at: undefined,
          is_active: true
        }
        setCases([...cases, mockCase])
        setShowCreateModal(false)
        setNewCaseName('')
        setNewCaseNumber('')
      } else {
        alert('Failed to create case. Backend is not available.')
      }
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-lg">Loading cases...</div>
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Cases</h1>
            <p className="text-gray-600 mt-2">Manage your legal cases and documents</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            New Case
          </button>
        </div>

        {cases.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No cases yet</h3>
            <p className="text-gray-600 mb-4">Create your first case to get started</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
            >
              Create Case
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {cases.map((caseItem) => (
              <div
                key={caseItem.id}
                onClick={() => router.push(`/dashboard/cases/${caseItem.id}`)}
                className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer p-6"
              >
                <div className="flex items-start justify-between mb-4">
                  <FileText className="w-8 h-8 text-primary-600" />
                  {caseItem.case_number && (
                    <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
                      {caseItem.case_number}
                    </span>
                  )}
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {caseItem.name}
                </h3>
                {caseItem.description && (
                  <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                    {caseItem.description}
                  </p>
                )}
                <div className="flex items-center text-sm text-gray-500">
                  <Calendar className="w-4 h-4 mr-2" />
                  {new Date(caseItem.created_at).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-2xl font-bold mb-4">Create New Case</h2>
            <form onSubmit={handleCreateCase}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Case Name *
                </label>
                <input
                  type="text"
                  value={newCaseName}
                  onChange={(e) => setNewCaseName(e.target.value)}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500"
                  placeholder="e.g., Smith v. Jones"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Case Number
                </label>
                <input
                  type="text"
                  value={newCaseNumber}
                  onChange={(e) => setNewCaseNumber(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500"
                  placeholder="e.g., 2024-CV-001"
                />
              </div>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false)
                    setNewCaseName('')
                    setNewCaseNumber('')
                  }}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

