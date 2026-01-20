'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Case } from '@/lib/api'
import { Plus, FileText, Calendar, LayoutGrid, List, ArrowUpDown, MoreVertical, Eye, Edit, Trash2, File, ChevronLeft, ChevronRight } from 'lucide-react'
import { createPortal } from 'react-dom'
import { useDashboard } from '@/lib/dashboard-context'
import { supabase } from '@/lib/supabase'
import { useAuth } from '@/lib/auth'

export default function WorkspacePage() {
  const { cases, setCases, isLoading, setIsLoading, refreshCases } = useDashboard()
  const { user } = useAuth()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newCaseName, setNewCaseName] = useState('')
  const [newCaseNumber, setNewCaseNumber] = useState('')
  const [viewMode, setViewMode] = useState<'tile' | 'list'>('tile')
  const [sortBy, setSortBy] = useState<'name' | 'recent'>('recent')
  const [showSortModal, setShowSortModal] = useState(false)
  const [showItemsPerPageDropdown, setShowItemsPerPageDropdown] = useState(false)
  const [itemsPerPage, setItemsPerPage] = useState<50 | 75 | 100>(50)
  const [currentPage, setCurrentPage] = useState(1)
  const [openMenuId, setOpenMenuId] = useState<string | null>(null)
  const [menuPosition, setMenuPosition] = useState<{ top: number; left: number } | null>(null)
  const [itemsPerPageDropdownPosition, setItemsPerPageDropdownPosition] = useState<{ top: number; left: number } | null>(null)
  const [caseToDelete, setCaseToDelete] = useState<Case | null>(null)
  const [deleteConfirmText, setDeleteConfirmText] = useState('')
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [documentCounts, setDocumentCounts] = useState<{ [key: string]: number }>({})
  const router = useRouter()
  const hasLoadedRef = useRef(false)
  const sortButtonRef = useRef<HTMLButtonElement>(null)
  const itemsPerPageButtonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    // Only load data if context is empty and not currently loading
    // The context's refreshCases has guards to prevent duplicate loads
    if (cases.length === 0 && !isLoading) {
      refreshCases()
    }
    
    // Listen for custom event to open new case modal
    const handleOpenModal = () => {
      setShowCreateModal(true)
    }
    window.addEventListener('openNewCaseModal', handleOpenModal)
    
    return () => {
      window.removeEventListener('openNewCaseModal', handleOpenModal)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // Empty deps - only check once on mount

  // Fetch document counts for all cases
  useEffect(() => {
    const fetchDocumentCounts = async () => {
      if (cases.length === 0) return

      try {
        const counts: { [key: string]: number } = {}
        
        // Fetch counts for all cases in parallel
        await Promise.all(
          cases.map(async (caseItem) => {
            const { count, error } = await supabase
              .from('documents')
              .select('*', { count: 'exact', head: true })
              .eq('case_id', caseItem.id)

            if (!error && count !== null) {
              counts[caseItem.id] = count
            } else {
              counts[caseItem.id] = 0
            }
          })
        )

        setDocumentCounts(counts)
      } catch (error) {
        console.error('Failed to fetch document counts:', error)
      }
    }

    fetchDocumentCounts()
  }, [cases])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement
      if (showSortModal && sortButtonRef.current && !sortButtonRef.current.contains(target) && !target.closest('.sort-dropdown-container')) {
        setShowSortModal(false)
      }
      if (showItemsPerPageDropdown && itemsPerPageButtonRef.current && !itemsPerPageButtonRef.current.contains(target) && !target.closest('[data-items-per-page-dropdown]')) {
        setShowItemsPerPageDropdown(false)
        setItemsPerPageDropdownPosition(null)
      }
      if (openMenuId && !target.closest(`[data-dropdown-menu]`) && !target.closest(`[data-menu-button="${openMenuId}"]`)) {
        setOpenMenuId(null)
        setMenuPosition(null)
      }
    }

    if (showSortModal || showItemsPerPageDropdown || openMenuId) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showSortModal, showItemsPerPageDropdown, openMenuId])

  const handleMenuClick = (caseItem: Case, event: React.MouseEvent) => {
    event.stopPropagation()
    const buttonElement = event.currentTarget as HTMLElement
    const rect = buttonElement.getBoundingClientRect()
    
    if (openMenuId === String(caseItem.id)) {
      setOpenMenuId(null)
      setMenuPosition(null)
    } else {
      setOpenMenuId(String(caseItem.id))
      setMenuPosition({
        top: rect.bottom + window.scrollY,
        left: rect.left + window.scrollX
      })
    }
  }

  const handleViewCase = (caseItem: Case) => {
    setOpenMenuId(null)
    setMenuPosition(null)
    router.push(`/cases/${caseItem.id}`)
  }

  const handleEditCase = (caseItem: Case) => {
    setOpenMenuId(null)
    setMenuPosition(null)
    // TODO: Implement edit case functionality
    // For now, navigate to the case page
    router.push(`/cases/${caseItem.id}`)
  }

  const handleDeleteCase = (caseItem: Case) => {
    setOpenMenuId(null)
    setMenuPosition(null)
    setCaseToDelete(caseItem)
    setDeleteConfirmText('')
    setShowDeleteModal(true)
  }

  const confirmDeleteCase = async () => {
    if (!caseToDelete || deleteConfirmText.toLowerCase() !== 'delete case') {
      return
    }

    setDeletingId(String(caseToDelete.id))
    try {
      const { error } = await supabase
        .from('cases')
        .delete()
        .eq('id', caseToDelete.id)

      if (error) {
        throw error
      }

      // Remove from local state
      setCases(cases.filter(c => c.id !== caseToDelete.id))
      setShowDeleteModal(false)
      setCaseToDelete(null)
      setDeleteConfirmText('')
    } catch (err: any) {
      console.error('Failed to delete case:', err)
      alert(`Failed to delete case: ${err.message || 'Unknown error'}`)
    } finally {
      setDeletingId(null)
    }
  }

  // Sort cases based on selected sort option
  const sortedCases = [...cases].sort((a, b) => {
    if (sortBy === 'name') {
      return a.name.localeCompare(b.name)
    } else {
      // Most recent first
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    }
  })

  // Pagination calculations
  const totalPages = Math.ceil(sortedCases.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  const paginatedCases = sortedCases.slice(startIndex, endIndex)

  // Reset to page 1 when items per page changes or cases change
  useEffect(() => {
    setCurrentPage(1)
  }, [itemsPerPage, sortedCases.length])

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user?.id) {
      alert('You must be logged in to create a case.')
      return
    }
    
    try {
      // Create case in Supabase
      const { data, error } = await supabase
        .from('cases')
        .insert({
          name: newCaseName,
          case_number: newCaseNumber || null,
          description: null,
          created_by: user.id,
          is_active: true
        })
        .select()
        .single()
      
      if (error) {
        console.error('Failed to create case:', error)
        throw error
      }
      
      // Map the created case and add to state
      const newCase: Case = {
        id: data.id,
        name: data.name,
        case_number: data.case_number || undefined,
        description: data.description || undefined,
        created_at: data.created_at,
        updated_at: data.updated_at || undefined,
        is_active: data.is_active !== false
      }
      
      setCases([...cases, newCase])
      setShowCreateModal(false)
      setNewCaseName('')
      setNewCaseNumber('')
    } catch (error: any) {
      console.error('Failed to create case:', error)
      alert(`Failed to create case: ${error.message || 'Unknown error'}`)
    }
  }

  return (
    <div className="h-full overflow-y-auto p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Cases</h1>
            <p className="text-gray-600 mt-2">Manage your cases and documents</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1 border border-gray-300 rounded-lg p-1">
              <button
                onClick={() => setViewMode('tile')}
                className={`p-2 rounded transition-colors ${
                  viewMode === 'tile'
                    ? 'bg-gray-200 text-gray-900'
                    : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
                }`}
                title="Tile View"
              >
                <LayoutGrid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded transition-colors ${
                  viewMode === 'list'
                    ? 'bg-gray-200 text-gray-900'
                    : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
                }`}
                title="List View"
              >
                <List className="w-4 h-4" />
              </button>
            </div>
            <div className="relative sort-dropdown-container flex items-center">
              <button
                onClick={() => setShowSortModal(!showSortModal)}
                className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 text-gray-600 hover:text-gray-900 transition-colors flex items-center justify-center"
                style={{ minHeight: '40px' }}
                title="Sort"
              >
                <ArrowUpDown className="w-4 h-4" />
              </button>
              
              {/* Sort Dropdown */}
              {showSortModal && (
                <div className="absolute right-0 top-full mt-1 bg-white rounded-lg shadow-lg border border-gray-200 min-w-[180px] z-50">
                  <div className="py-1">
                    <button
                      onClick={() => {
                        setSortBy('name')
                        setShowSortModal(false)
                      }}
                      className={`w-full text-left px-3 py-2 text-sm transition-colors ${
                        sortBy === 'name'
                          ? 'bg-gray-100 text-gray-900 font-medium'
                          : 'text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      Case Name
                    </button>
                    <button
                      onClick={() => {
                        setSortBy('recent')
                        setShowSortModal(false)
                      }}
                      className={`w-full text-left px-3 py-2 text-sm transition-colors ${
                        sortBy === 'recent'
                          ? 'bg-gray-100 text-gray-900 font-medium'
                          : 'text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      Most Recent
                    </button>
                  </div>
                </div>
              )}
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-black text-white px-4 py-2 rounded-lg hover:bg-gray-900 flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              Add Case
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Create New Case Card - Always visible even during loading */}
            <div
              onClick={() => setShowCreateModal(true)}
              className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer p-4 border-2 border-dashed border-gray-200 hover:border-gray-300 flex flex-col items-center justify-center h-32"
            >
              <div className="flex flex-col items-center text-center">
                <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center mb-3">
                  <Plus className="w-5 h-5 text-gray-400" />
                </div>
                <h3 className="text-sm font-semibold text-gray-500">
                  Create Case
                </h3>
              </div>
            </div>
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="bg-white rounded-lg shadow p-6 animate-pulse"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-8 h-8 bg-gray-200 rounded"></div>
                  <div className="w-20 h-6 bg-gray-200 rounded"></div>
                </div>
                <div className="h-6 bg-gray-200 rounded mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        ) : viewMode === 'tile' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Create New Case Card - Always visible */}
            <div
              onClick={() => setShowCreateModal(true)}
              className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer p-4 border-2 border-dashed border-gray-200 hover:border-gray-300 flex flex-col items-center justify-center h-32"
            >
              <div className="flex flex-col items-center text-center">
                <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center mb-3">
                  <Plus className="w-5 h-5 text-gray-400" />
                </div>
                <h3 className="text-sm font-semibold text-gray-500">
                  Add Case
                </h3>
              </div>
            </div>

            {/* Existing Cases */}
            {sortedCases.map((caseItem) => (
              <div
                key={caseItem.id}
                onClick={() => router.push(`/cases/${caseItem.id}`)}
                className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer p-4 h-32 flex flex-col"
              >
                <div className="flex items-start justify-between mb-3">
                  <FileText className="w-6 h-6 text-gray-500" />
                  {caseItem.case_number && (
                    <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                      {caseItem.case_number}
                    </span>
                  )}
                </div>
                <div className="flex-1 flex flex-col">
                  <h3 className="text-sm font-medium text-gray-900 mb-2 line-clamp-2">
                    {caseItem.name}
                  </h3>
                  {caseItem.description && (
                    <p className="text-gray-600 text-xs mb-3 line-clamp-2 flex-1">
                      {caseItem.description}
                    </p>
                  )}
                </div>
                <div className="flex items-center justify-between text-xs text-gray-500 mt-auto">
                  <div className="flex items-center">
                    <Calendar className="w-3 h-3 mr-1.5" />
                    {new Date(caseItem.created_at).toLocaleDateString()}
                  </div>
                  <div className="flex items-center">
                    <File className="w-3 h-3 mr-1" />
                    {documentCounts[caseItem.id] ?? 0}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 uppercase tracking-wider">
                    Case Name
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 uppercase tracking-wider">
                    Case Number
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 uppercase tracking-wider">
                    Documents
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 uppercase tracking-wider w-20">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {paginatedCases.map((caseItem) => (
                  <tr
                    key={caseItem.id}
                    onClick={() => router.push(`/cases/${caseItem.id}`)}
                    className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-gray-500 flex-shrink-0" />
                        <span className="text-sm font-medium text-gray-900">
                          {caseItem.name}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-sm text-gray-600">
                        {caseItem.case_number || '-'}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-sm text-gray-600 line-clamp-1">
                        {caseItem.description || '-'}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1.5 text-sm text-gray-500">
                        <Calendar className="w-3 h-3" />
                        {new Date(caseItem.created_at).toLocaleDateString()}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1.5 text-sm text-gray-600">
                        <File className="w-3 h-3" />
                        {documentCounts[caseItem.id] ?? 0}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="relative">
                        <button
                          data-menu-button={caseItem.id}
                          onClick={(e) => handleMenuClick(caseItem, e)}
                          className="p-1.5 rounded hover:bg-gray-100 text-gray-600 hover:text-gray-900 transition-colors"
                          title="Actions"
                        >
                          <MoreVertical className="w-4 h-4" />
                        </button>
                        {openMenuId === String(caseItem.id) && menuPosition && typeof window !== 'undefined' && createPortal(
                          <div
                            data-dropdown-menu
                            className="fixed w-40 bg-white border border-gray-200 rounded-lg shadow-lg z-50"
                            style={{
                              top: `${menuPosition.top}px`,
                              left: `${menuPosition.left}px`
                            }}
                          >
                            <button
                              onClick={() => handleViewCase(caseItem)}
                              className="w-full text-left px-4 py-2 text-xs text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                            >
                              <Eye className="w-3 h-3" />
                              View
                            </button>
                            <button
                              onClick={() => handleEditCase(caseItem)}
                              className="w-full text-left px-4 py-2 text-xs text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                            >
                              <Edit className="w-3 h-3" />
                              Edit
                            </button>
                            <button
                              onClick={() => handleDeleteCase(caseItem)}
                              disabled={deletingId === caseItem.id}
                              className="w-full text-left px-4 py-2 text-xs text-red-600 hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                            >
                              <Trash2 className="w-3 h-3" />
                              {deletingId === caseItem.id ? 'Deleting...' : 'Delete'}
                            </button>
                          </div>,
                          document.body
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {cases.length === 0 && (
                  <tr>
                    <td colSpan={6} className="py-8 px-4 text-center text-sm text-gray-500">
                      No cases yet. Click "Add Case" to create your first case.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
            
            {/* Pagination Controls */}
            {sortedCases.length > 0 && (
              <div className="flex items-center justify-between px-4 py-3 bg-white">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-700">Show:</span>
                  <div className="relative items-per-page-dropdown-container">
                    <button
                      ref={itemsPerPageButtonRef}
                      onClick={(e) => {
                        const buttonElement = e.currentTarget as HTMLElement
                        const rect = buttonElement.getBoundingClientRect()
                        
                        // Position dropdown below the button
                        setItemsPerPageDropdownPosition({
                          top: rect.bottom + window.scrollY + 4,
                          left: rect.left + window.scrollX,
                        })
                        setShowItemsPerPageDropdown(!showItemsPerPageDropdown)
                      }}
                      className="px-2 py-1 text-xs border border-gray-300 rounded-md text-gray-900 bg-white hover:border-black hover:bg-gray-50 transition-colors min-w-[60px] text-left flex items-center justify-between gap-1"
                    >
                      <span>{itemsPerPage}</span>
                      <ArrowUpDown className="w-3 h-3" />
                    </button>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                    disabled={currentPage === 1}
                    className="p-1.5 rounded border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Previous page"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <span className="text-xs text-gray-700">
                    Page {currentPage} of {totalPages}
                  </span>
                  <button
                    onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                    disabled={currentPage === totalPages}
                    className="p-1.5 rounded border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Next page"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Items Per Page Dropdown - Portal */}
      {showItemsPerPageDropdown && itemsPerPageDropdownPosition && typeof window !== 'undefined' && createPortal(
        <div
          data-items-per-page-dropdown
          className="fixed w-24 bg-white border border-gray-200 rounded-lg shadow-lg z-50"
          style={{
            top: `${itemsPerPageDropdownPosition.top}px`,
            left: `${itemsPerPageDropdownPosition.left}px`
          }}
        >
          <div className="py-1">
            <button
              onClick={() => {
                setItemsPerPage(50)
                setShowItemsPerPageDropdown(false)
                setItemsPerPageDropdownPosition(null)
              }}
              className={`w-full text-left px-3 py-2 text-xs transition-colors ${
                itemsPerPage === 50
                  ? 'bg-gray-100 text-gray-900 font-medium'
                  : 'text-gray-700 hover:bg-gray-50'
              }`}
            >
              50
            </button>
            <button
              onClick={() => {
                setItemsPerPage(75)
                setShowItemsPerPageDropdown(false)
                setItemsPerPageDropdownPosition(null)
              }}
              className={`w-full text-left px-3 py-2 text-xs transition-colors ${
                itemsPerPage === 75
                  ? 'bg-gray-100 text-gray-900 font-medium'
                  : 'text-gray-700 hover:bg-gray-50'
              }`}
            >
              75
            </button>
            <button
              onClick={() => {
                setItemsPerPage(100)
                setShowItemsPerPageDropdown(false)
                setItemsPerPageDropdownPosition(null)
              }}
              className={`w-full text-left px-3 py-2 text-xs transition-colors ${
                itemsPerPage === 100
                  ? 'bg-gray-100 text-gray-900 font-medium'
                  : 'text-gray-700 hover:bg-gray-50'
              }`}
            >
              100
            </button>
          </div>
        </div>,
        document.body
      )}

      {/* Delete Case Confirmation Modal */}
      {showDeleteModal && caseToDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md shadow-2xl">
            <h3 className="text-lg font-bold mb-4 text-gray-900">Delete Case</h3>
            <div className="space-y-4">
              <p className="text-sm text-gray-700">
                Are you sure you want to delete <strong>{caseToDelete.name}</strong>? This action cannot be undone.
              </p>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Type <strong>"delete case"</strong> to confirm:
                </label>
                <input
                  type="text"
                  value={deleteConfirmText}
                  onChange={(e) => setDeleteConfirmText(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="delete case"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && deleteConfirmText.toLowerCase() === 'delete case') {
                      confirmDeleteCase()
                    }
                  }}
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => {
                    setShowDeleteModal(false)
                    setCaseToDelete(null)
                    setDeleteConfirmText('')
                  }}
                  className="flex-1 px-4 py-2 text-sm border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmDeleteCase}
                  disabled={deleteConfirmText.toLowerCase() !== 'delete case' || deletingId === caseToDelete.id}
                  className="flex-1 px-4 py-2 text-sm bg-black text-white rounded-lg hover:bg-gray-900 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-black"
                >
                  {deletingId === caseToDelete.id ? 'Deleting...' : 'Delete Case'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md shadow-2xl">
            <h2 className="text-2xl font-bold mb-4 text-gray-900">Add Case</h2>
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
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-black text-white rounded-md hover:bg-gray-900"
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

