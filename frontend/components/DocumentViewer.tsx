'use client'

import { useState } from 'react'
import { Document, documentsApi } from '@/lib/api'
import { FileText, Calendar, User, Hash, MoreVertical, X, Eye, AlertCircle } from 'lucide-react'
import { format } from 'date-fns'

interface DocumentViewerProps {
  document: Document | { id: string | number; [key: string]: any } // Support both UUID and integer IDs
  onDocumentDeleted?: () => void
}

export default function DocumentViewer({ document, onDocumentDeleted }: DocumentViewerProps) {
  const [showMenu, setShowMenu] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [deleteConfirmText, setDeleteConfirmText] = useState('')
  const [isDeleting, setIsDeleting] = useState(false)
  return (
    <div className="h-full bg-white p-6">
      <div className="max-w-4xl mx-auto">
        {/* Document Header */}
        <div className="border-b border-gray-200 pb-4 mb-6">
          <div className="flex items-start gap-4">
            <div className="flex-1">
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-base font-bold text-gray-900">
                  {document.original_filename}
                </h2>
                <div className="relative">
                  <button
                    onClick={() => setShowMenu(!showMenu)}
                    className="p-1 hover:bg-gray-200 rounded transition-colors"
                  >
                    <MoreVertical className="w-5 h-5 text-gray-600" />
                  </button>
                  {showMenu && (
                    <>
                      <div
                        className="fixed inset-0 z-40"
                        onClick={() => setShowMenu(false)}
                      />
                      <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
                        <div className="py-1">
                          <button
                            className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                            onClick={() => {
                              setShowMenu(false)
                              setShowDeleteModal(true)
                            }}
                          >
                            Delete Document
                          </button>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-4 text-xs text-gray-600 flex-wrap">
                <div className="flex items-center gap-2">
                  <FileText className="w-3 h-3" />
                  <span>{document.file_type.toUpperCase()}</span>
                </div>
                {document.page_count && (
                  <div className="flex items-center gap-2">
                    <span>{document.page_count} pages</span>
                  </div>
                )}
                <div className="flex items-center gap-2">
                  <Calendar className="w-3 h-3" />
                  <span>Uploaded {format(new Date(document.uploaded_at), 'MMM d, yyyy')}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Eye className="w-3 h-3" />
                  <span>{document.view_count || 0} views</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Metadata */}
        {(document.bates_number || document.custodian || document.author) && (
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <h3 className="text-xs font-semibold text-gray-900 mb-3">Document Metadata</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {document.bates_number && (
                <div className="flex items-center gap-2">
                  <Hash className="w-3 h-3 text-gray-700" />
                  <span className="text-xs text-gray-900">Bates Number:</span>
                  <span className="text-xs font-medium text-gray-900">{document.bates_number}</span>
                </div>
              )}
              {document.custodian && (
                <div className="flex items-center gap-2">
                  <User className="w-3 h-3 text-gray-700" />
                  <span className="text-xs text-gray-900">Custodian:</span>
                  <span className="text-xs font-medium text-gray-900">{document.custodian}</span>
                </div>
              )}
              {document.author && (
                <div className="flex items-center gap-2">
                  <User className="w-3 h-3 text-gray-700" />
                  <span className="text-xs text-gray-900">Author:</span>
                  <span className="text-xs font-medium text-gray-900">{document.author}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Error Message */}
        {document.status === 'error' && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-red-900 mb-1">Processing Error</h3>
                <p className="text-sm text-red-800">
                  {document.error_message || 'An error occurred while processing this document. Please try reprocessing or re-uploading.'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Document Preview */}
        <div className="border border-gray-200 rounded-lg p-6 bg-gray-50">
          <p className="text-sm text-gray-600 mb-4">
            Document preview and full text extraction will be displayed here.
            In a production version, this would show the actual document content
            with page-by-page navigation and search capabilities.
          </p>
          <p className="text-xs text-gray-500">
            For PDFs, this would render the document pages. For text documents,
            this would show the extracted text with proper formatting.
          </p>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900">Delete Document</h2>
              <button
                onClick={() => {
                  setShowDeleteModal(false)
                  setDeleteConfirmText('')
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              This action cannot be undone. This will permanently delete the document and all associated data.
            </p>
            <p className="text-sm text-gray-700 mb-2 font-medium">
              Type <span className="font-mono bg-gray-100 px-2 py-1 rounded">delete</span> to confirm:
            </p>
            <input
              type="text"
              value={deleteConfirmText}
              onChange={(e) => setDeleteConfirmText(e.target.value)}
              placeholder="Type 'delete' to confirm"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-0 focus:border-gray-300 mb-4"
              autoFocus
            />
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => {
                  setShowDeleteModal(false)
                  setDeleteConfirmText('')
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700"
                disabled={isDeleting}
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  if (deleteConfirmText.toLowerCase() === 'delete') {
                    setIsDeleting(true)
                    try {
                      // Check if document ID is a UUID (string) or integer
                      const docId = document.id
                      if (typeof docId === 'string' && docId.includes('-')) {
                        // UUID - delete from Supabase
                        const { supabase } = await import('@/lib/supabase')
                        const { error } = await supabase
                          .from('documents')
                          .delete()
                          .eq('id', docId)
                        
                        if (error) throw error
                      } else {
                        // Integer ID - delete from backend API
                        await documentsApi.delete(Number(docId))
                      }
                      
                      setShowDeleteModal(false)
                      setDeleteConfirmText('')
                      if (onDocumentDeleted) {
                        onDocumentDeleted()
                      }
                    } catch (error: any) {
                      console.error('Failed to delete document:', error)
                      // Extract error message properly
                      let errorMessage = 'Failed to delete document'
                      if (error?.response?.data?.detail) {
                        errorMessage = typeof error.response.data.detail === 'string' 
                          ? error.response.data.detail 
                          : JSON.stringify(error.response.data.detail)
                      } else if (error?.message) {
                        errorMessage = error.message
                      } else if (typeof error === 'string') {
                        errorMessage = error
                      }
                      alert(errorMessage)
                    } finally {
                      setIsDeleting(false)
                    }
                  }
                }}
                disabled={deleteConfirmText.toLowerCase() !== 'delete' || isDeleting}
                className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isDeleting ? 'Deleting...' : 'Delete Document'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

