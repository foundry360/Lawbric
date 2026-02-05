'use client'

import { useState, useEffect } from 'react'
import { Document, documentsApi } from '@/lib/api'
import { FileText, Calendar, User, Hash, MoreVertical, X, Eye, AlertCircle, Loader2, ZoomIn, ZoomOut, Download, Printer, Maximize2, Minimize2, ChevronsLeft, ChevronsRight } from 'lucide-react'
import { format } from 'date-fns'
import AdobePDFViewer from './AdobePDFViewer'

interface DocumentViewerProps {
  document: Document | { id: string | number; [key: string]: any } // Support both UUID and integer IDs
  onDocumentDeleted?: () => void
  isCollapsed?: boolean
  onToggleCollapse?: () => void
  documentListCollapsed?: boolean
  onToggleDocumentList?: () => void
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9001'

export default function DocumentViewer({ document, onDocumentDeleted, isCollapsed, onToggleCollapse, documentListCollapsed, onToggleDocumentList }: DocumentViewerProps) {
  const [showMenu, setShowMenu] = useState(false)
  const [showArchiveModal, setShowArchiveModal] = useState(false)
  const [archiveConfirmText, setArchiveConfirmText] = useState('')
  const [isArchiving, setIsArchiving] = useState(false)
  const [extractedText, setExtractedText] = useState<string | null>(null)
  const [loadingContent, setLoadingContent] = useState(false)
  const [contentError, setContentError] = useState<string | null>(null)
  const [pdfBlobUrl, setPdfBlobUrl] = useState<string | null>(null)
  const [previousStatus, setPreviousStatus] = useState<string | undefined>(document.status)
  const [textZoom, setTextZoom] = useState(100) // Zoom level for text documents (percentage)
  const [isFullscreen, setIsFullscreen] = useState(false)

  // Auto-refresh when document status changes from processing to processed
  useEffect(() => {
    // If status changed from processing/pending to processed, refetch content
    if (
      previousStatus && 
      (previousStatus === 'processing' || previousStatus === 'pending') &&
      (document.status === 'processed' || document.status === 'error')
    ) {
      // Trigger refetch by resetting state
      setPdfBlobUrl(null)
      setExtractedText(null)
      setContentError(null)
    }
    setPreviousStatus(document.status)
  }, [document.status, previousStatus])

  // Fetch document content when document changes
  useEffect(() => {
    const fetchDocumentContent = async () => {
      // Both UUID and integer IDs are now supported
      const docId = document.id

      const fileType = document.file_type?.toLowerCase() || ''
      const isTextDocument = ['txt', 'docx', 'doc'].includes(fileType)
      const isPdf = fileType === 'pdf'

      // For PDFs, try to fetch if status allows (processed, error, or even processing if we want to try)
      // But only actually fetch if status is processed or error
      if (isPdf) {
        if (document.status === 'processed' || document.status === 'error') {
          setLoadingContent(true)
          setContentError(null)
          try {
            const token = localStorage.getItem('token') || ''
            const response = await fetch(`${API_URL}/api/v1/documents/${docId}/file`, {
              headers: {
                'Authorization': `Bearer ${token}`
              }
            })
            
            if (!response.ok) {
              if (response.status === 404) {
                throw new Error('Document file not found on server')
              } else if (response.status === 401 || response.status === 403) {
                throw new Error('You do not have permission to view this document')
              } else {
                throw new Error(`Server error: ${response.status} ${response.statusText}`)
              }
            }
            
            const blob = await response.blob()
            if (blob.size === 0) {
              throw new Error('Document file is empty')
            }
            const blobUrl = URL.createObjectURL(blob)
            setPdfBlobUrl(blobUrl)
            setContentError(null) // Clear any previous errors
          } catch (error: any) {
            console.error('Error fetching document file:', error)
            setContentError(error.message || 'Failed to load document file')
            setPdfBlobUrl(null)
          } finally {
            setLoadingContent(false)
          }
        }
        return
      }

      // For text documents, fetch extracted text
      if (isTextDocument) {
        if (document.status === 'processed' || document.status === 'error') {
        setLoadingContent(true)
        setContentError(null)
        try {
          const token = localStorage.getItem('token') || ''
          const response = await fetch(`${API_URL}/api/v1/documents/${docId}/content`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })
          
          if (!response.ok) {
            if (response.status === 404) {
              throw new Error('Document content not found')
            } else if (response.status === 401 || response.status === 403) {
              throw new Error('You do not have permission to view this document')
            } else {
              throw new Error(`Server error: ${response.status} ${response.statusText}`)
            }
          }
          
          const data = await response.json()
          if (data.extracted_text) {
            setExtractedText(data.extracted_text)
            setContentError(null) // Clear any previous errors
          } else {
            setExtractedText(null)
            setContentError('No extracted text available for this document')
          }
        } catch (error: any) {
          console.error('Error fetching document content:', error)
          setContentError(error.message || 'Failed to load document content')
          setExtractedText(null)
        } finally {
          setLoadingContent(false)
        }
        } else {
          setExtractedText(null)
          // Don't set error for pending/processing documents
          if (document.status !== 'processing' && document.status !== 'pending') {
            setContentError(null)
          }
        }
      } else {
        setExtractedText(null)
        setContentError(null)
      }
    }

    fetchDocumentContent()

    // Cleanup blob URL on unmount or document change
    return () => {
      // Cleanup will be handled by the state setter
    }
  }, [document.id, document.file_type, document.status])

  // Separate effect to cleanup blob URL when it changes
  useEffect(() => {
    return () => {
      if (pdfBlobUrl) {
        URL.revokeObjectURL(pdfBlobUrl)
      }
    }
  }, [pdfBlobUrl])

  const renderDocumentContent = () => {
    const fileType = document.file_type?.toLowerCase() || ''
    
    // Show loading state
    if (loadingContent) {
      return (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-gray-400 mr-2" />
          <span className="text-sm text-gray-600">Loading document content...</span>
        </div>
      )
    }

    // Show error state
    if (contentError) {
      return (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold text-red-900 mb-1">Error Loading Content</h3>
              <p className="text-sm text-red-800">{contentError}</p>
            </div>
          </div>
        </div>
      )
    }

    // PDF viewer
    if (fileType === 'pdf') {
      if (document.status === 'processing' || document.status === 'pending') {
        return (
          <div className="bg-gray-50 rounded-lg p-6 text-center">
            <Loader2 className="w-8 h-8 animate-spin text-gray-400 mx-auto mb-4" />
            <p className="text-sm text-gray-600">Document is being processed. PDF will appear when ready.</p>
          </div>
        )
      }

      // Show error if there was a content error
      if (contentError) {
        return (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-sm font-semibold text-red-900 mb-1">Error Loading PDF</h3>
                <p className="text-sm text-red-800">{contentError}</p>
                {document.status === 'error' && (
                  <p className="text-xs text-red-700 mt-2">
                    The document had processing errors, but the original file may still be available. 
                    Try refreshing or contact support if the issue persists.
                  </p>
                )}
              </div>
            </div>
          </div>
        )
      }

      if (!pdfBlobUrl) {
        if (loadingContent) {
          return (
            <div className="bg-gray-50 rounded-lg p-6 text-center">
              <Loader2 className="w-8 h-8 animate-spin text-gray-400 mx-auto mb-4" />
              <p className="text-sm text-gray-600">Loading PDF...</p>
            </div>
          )
        }
        
        // If we got here without loading or error, the fetch might have failed silently
        return (
          <div className="bg-gray-50 rounded-lg p-6 text-center">
            <AlertCircle className="w-8 h-8 text-gray-400 mx-auto mb-4" />
            <p className="text-sm text-gray-600 font-medium mb-2">PDF not available</p>
            <p className="text-xs text-gray-500">
              {document.status === 'error' 
                ? 'The document file may not be available due to processing errors.'
                : 'The PDF file could not be loaded. Please check the document status or try refreshing.'}
            </p>
          </div>
        )
      }
      
      return (
        <AdobePDFViewer
          pdfUrl={pdfBlobUrl}
          fileName={document.original_filename}
        />
      )
    }

    // Text document viewer
    if (['txt', 'docx', 'doc'].includes(fileType)) {
      if (!extractedText) {
        if (document.status === 'processing' || document.status === 'pending') {
          return (
            <div className="bg-gray-50 rounded-lg p-6 text-center">
              <Loader2 className="w-8 h-8 animate-spin text-gray-400 mx-auto mb-4" />
              <p className="text-sm text-gray-600">Document is being processed. Content will appear when ready.</p>
            </div>
          )
        }

        // Show specific error if available
        if (contentError) {
          return (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="text-sm font-semibold text-red-900 mb-1">Error Loading Content</h3>
                  <p className="text-sm text-red-800">{contentError}</p>
                </div>
              </div>
            </div>
          )
        }
        
        return (
          <div className="bg-gray-50 rounded-lg p-6">
            <AlertCircle className="w-6 h-6 text-gray-400 mx-auto mb-3" />
            <p className="text-sm text-gray-600 mb-2 font-medium text-center">
              Text content not available
            </p>
            <p className="text-xs text-gray-500 text-center">
              {document.status === 'error'
                ? 'Text extraction failed during processing. The document may need to be reprocessed.'
                : 'The document may not have been processed yet, or text extraction is not available.'}
            </p>
          </div>
        )
      }

      // Text document viewer with toolbar
      const handleZoomIn = () => {
        setTextZoom(prev => Math.min(prev + 10, 200)) // Max 200%
      }
      
      const handleZoomOut = () => {
        setTextZoom(prev => Math.max(prev - 10, 50)) // Min 50%
      }
      
      const handleDownload = async () => {
        try {
          const token = localStorage.getItem('token') || ''
          const docId = document.id
          const response = await fetch(`${API_URL}/api/v1/documents/${docId}/file`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })
          
          if (!response.ok) {
            throw new Error('Failed to download document')
          }
          
          const blob = await response.blob()
          const url = URL.createObjectURL(blob)
          const a = window.document.createElement('a')
          a.href = url
          a.download = document.original_filename || 'document'
          window.document.body.appendChild(a)
          a.click()
          window.document.body.removeChild(a)
          URL.revokeObjectURL(url)
        } catch (error: any) {
          console.error('Error downloading document:', error)
          alert('Failed to download document: ' + (error.message || 'Unknown error'))
        }
      }
      
      const handlePrint = () => {
        const printWindow = window.open('', '_blank')
        if (printWindow) {
          printWindow.document.write(`
            <html>
              <head>
                <title>${document.original_filename}</title>
                <style>
                  body { 
                    font-family: sans-serif; 
                    padding: 20px; 
                    line-height: 1.6;
                    white-space: pre-wrap;
                  }
                </style>
              </head>
              <body>${extractedText}</body>
            </html>
          `)
          printWindow.document.close()
          printWindow.focus()
          setTimeout(() => {
            printWindow.print()
          }, 250)
        }
      }
      
      const handleToggleFullscreen = () => {
        if (!isFullscreen) {
          setIsFullscreen(true)
        } else {
          setIsFullscreen(false)
        }
      }

      return (
        <div className={`bg-white border border-gray-200 rounded-lg overflow-hidden flex flex-col w-full h-full ${isFullscreen ? 'fixed inset-0 z-50 m-0 rounded-none' : ''}`}>
          {/* Toolbar */}
          <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-b border-gray-200 flex-shrink-0">
            <div className="flex items-center gap-2">
              {/* Zoom Controls */}
              <div className="flex items-center gap-1 border-r border-gray-300 pr-2 mr-2">
                <button
                  onClick={handleZoomOut}
                  disabled={textZoom <= 50}
                  className="p-1.5 hover:bg-gray-200 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Zoom Out"
                >
                  <ZoomOut className="w-4 h-4 text-gray-700" />
                </button>
                <span className="text-xs text-gray-700 font-medium px-2 min-w-[45px] text-center">
                  {textZoom}%
                </span>
                <button
                  onClick={handleZoomIn}
                  disabled={textZoom >= 200}
                  className="p-1.5 hover:bg-gray-200 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Zoom In"
                >
                  <ZoomIn className="w-4 h-4 text-gray-700" />
                </button>
              </div>
            </div>
            
            <div className="flex items-center gap-1">
              {/* Download */}
              <button
                onClick={handleDownload}
                className="p-1.5 hover:bg-gray-200 rounded transition-colors"
                title="Download"
              >
                <Download className="w-4 h-4 text-gray-700" />
              </button>
              
              {/* Print */}
              <button
                onClick={handlePrint}
                className="p-1.5 hover:bg-gray-200 rounded transition-colors"
                title="Print"
              >
                <Printer className="w-4 h-4 text-gray-700" />
              </button>
              
              {/* Fullscreen */}
              <button
                onClick={handleToggleFullscreen}
                className="p-1.5 hover:bg-gray-200 rounded transition-colors"
                title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
              >
                {isFullscreen ? (
                  <Minimize2 className="w-4 h-4 text-gray-700" />
                ) : (
                  <Maximize2 className="w-4 h-4 text-gray-700" />
                )}
              </button>
            </div>
          </div>
          
          {/* Document Content */}
          <div 
            className="overflow-auto bg-white w-full flex-1 document-viewer-scroll" 
            style={{ minHeight: 0 }}
            ref={(el) => {
              // #region agent log
              if (el) {
                const hasClass = el.classList.contains('document-viewer-scroll');
                const computedStyle = window.getComputedStyle(el);
                const scrollbarWidth = computedStyle.getPropertyValue('scrollbar-width') || 'not-set';
                fetch('http://127.0.0.1:7242/ingest/5a0998ac-8afa-45a8-961d-0dd6f96371b5',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'DocumentViewer.tsx:436',message:'Document viewer scroll container mounted',data:{hasClass,scrollbarWidth,className:el.className,overflow:computedStyle.overflow},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
              }
              // #endregion
            }}
          >
            <div className="p-6 w-full">
              <div className="w-full">
                <pre 
                  className="whitespace-pre-wrap font-sans text-gray-900 leading-relaxed w-full"
                  style={{ 
                    fontSize: `${(textZoom / 100) * 14}px` // Base font size 14px, scaled by zoom
                  }}
                >
                  {extractedText}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )
    }

    // Default placeholder for unsupported types
    return (
      <div className="border border-gray-200 rounded-lg p-6 bg-gray-50">
        <p className="text-sm text-gray-600 mb-4">
          Document preview is not available for this file type ({fileType}).
        </p>
        <p className="text-xs text-gray-500">
          Supported preview types: PDF, TXT, DOCX, DOC
        </p>
      </div>
    )
  }

  return (
    <div className="h-full bg-white flex flex-col w-full">
      <div className="flex-1 flex flex-col min-w-0 w-full">
        {/* Document Header */}
        <div className="px-4 py-3 bg-white flex items-center justify-between h-[52px] flex-shrink-0">
          <div className="flex items-center gap-2">
            {/* Show Document List expand button if Document List is collapsed, otherwise show Viewer collapse button if Viewer is open */}
            {documentListCollapsed && onToggleDocumentList ? (
              <button
                onClick={onToggleDocumentList}
                className="p-1 hover:bg-gray-200 rounded transition-colors"
                title="Show document list"
              >
                <ChevronsLeft className="w-4 h-4 text-gray-600" />
              </button>
            ) : (
              onToggleCollapse && !isCollapsed && (
                <button
                  onClick={onToggleCollapse}
                  className="p-1 hover:bg-gray-200 rounded transition-colors"
                  title="Hide document viewer"
                >
                  <ChevronsRight className="w-4 h-4 text-gray-600" />
                </button>
              )
            )}
            <h2 className="text-base font-bold text-gray-900 leading-none">
              {document.original_filename}
            </h2>
          </div>
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
                        setShowArchiveModal(true)
                      }}
                    >
                      Archive Document
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
        {/* Document Metadata Bar */}
        <div className="px-4 py-2 bg-white flex-shrink-0">
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
        <div className="mt-6 flex-1 flex flex-col min-h-0 min-w-0">
          {renderDocumentContent()}
        </div>
      </div>

      {/* Archive Confirmation Modal */}
      {showArchiveModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900">Archive Document</h2>
              <button
                onClick={() => {
                  setShowArchiveModal(false)
                  setArchiveConfirmText('')
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <p className="text-sm text-gray-700 mb-4">
              This document will be archived. Archived documents are immutable and will be stored on the blockchain when implemented. The document will be removed from the active list but can be retrieved for audit purposes.
            </p>
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-3">
              <p className="text-sm font-semibold text-red-800 mb-1">
                ⚠️ This action is NOT reversible
              </p>
            </div>
            <p className="text-sm text-gray-700 mb-2 font-medium">
              Type <span className="font-mono bg-gray-100 px-2 py-1 rounded">archive</span> to confirm:
            </p>
            <input
              type="text"
              value={archiveConfirmText}
              onChange={(e) => setArchiveConfirmText(e.target.value)}
              placeholder="Type 'archive' to confirm"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-0 focus:border-gray-300 mb-4"
              autoFocus
            />
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => {
                  setShowArchiveModal(false)
                  setArchiveConfirmText('')
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700"
                disabled={isArchiving}
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  if (archiveConfirmText.toLowerCase() === 'archive') {
                    setIsArchiving(true)
                    try {
                      // Archive document via API (supports both UUID and numeric IDs)
                      const docId = document.id
                      await documentsApi.archive(docId)
                      
                      setShowArchiveModal(false)
                      setArchiveConfirmText('')
                      if (onDocumentDeleted) {
                        onDocumentDeleted()
                      }
                    } catch (error: any) {
                      console.error('Failed to archive document:', error)
                      // Extract error message properly
                      let errorMessage = 'Failed to archive document'
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
                      setIsArchiving(false)
                    }
                  }
                }}
                disabled={archiveConfirmText.toLowerCase() !== 'archive' || isArchiving}
                className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isArchiving ? 'Archiving...' : 'Archive Document'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}


