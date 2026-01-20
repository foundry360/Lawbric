'use client'

import { useEffect, useState } from 'react'
import { Document, documentsApi } from '@/lib/api'
import { X, Loader2, CheckCircle2, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { supabase } from '@/lib/supabase'

interface ProcessingDocument {
  id: string | number
  document: Document | { id: string | number; status?: string; original_filename?: string; [key: string]: any }
  caseId: string | number
  progress?: number
  stage?: string
}

interface ProcessingStatusCardProps {
  processingDocuments: Map<string | number, ProcessingDocument>
  onStatusChange?: (documentId: string | number, status: string) => void
  onClose: () => void
}

export default function ProcessingStatusCard({
  processingDocuments,
  onStatusChange,
  onClose
}: ProcessingStatusCardProps) {
  const [documents, setDocuments] = useState<ProcessingDocument[]>([])
  const [documentStatuses, setDocumentStatuses] = useState<Map<string | number, string>>(new Map())
  const [isExpanded, setIsExpanded] = useState(false)

  // Convert Map to array
  useEffect(() => {
    console.log('ProcessingStatusCard: processingDocuments changed, size:', processingDocuments.size)
    const docsArray = Array.from(processingDocuments.values())
    console.log('ProcessingStatusCard: documents array:', docsArray)
    setDocuments(docsArray)
    // Initialize statuses
    const statusMap = new Map<string | number, string>()
    processingDocuments.forEach((item, id) => {
      statusMap.set(id, item.document.status || 'processing')
    })
    setDocumentStatuses(statusMap)
    console.log('ProcessingStatusCard: initialized with', docsArray.length, 'documents')
  }, [processingDocuments])

  // Poll all processing documents every 2 seconds
  useEffect(() => {
    if (documents.length === 0) return

    const pollInterval = setInterval(async () => {
      for (const item of documents) {
        const currentStatus = documentStatuses.get(item.id)
        
        // Only poll if still processing
        if (currentStatus === 'processing') {
          try {
            const docId = item.document.id
            let updatedDoc: Document | null = null

            if (typeof docId === 'string' && docId.includes('-')) {
              // UUID - fetch from Supabase
              const { data, error } = await supabase
                .from('documents')
                .select('*')
                .eq('id', docId)
                .single()

              if (!error && data) {
                updatedDoc = {
                  id: data.id,
                  case_id: data.case_id,
                  filename: data.filename || '',
                  original_filename: data.original_filename || data.filename || '',
                  file_type: data.file_type || 'pdf',
                  file_size: data.file_size || 0,
                  status: data.status || 'pending',
                  uploaded_at: data.uploaded_at || data.created_at,
                  page_count: data.page_count || 0,
                  word_count: data.word_count || 0,
                  bates_number: data.bates_number || undefined,
                  author: data.author || undefined,
                  requires_ocr: data.requires_ocr || false,
                  view_count: data.view_count || 0,
                  metadata: data.metadata || {}
                }
              }
            } else {
              // Integer ID - fetch from backend API
              try {
                const response = await documentsApi.get(Number(docId))
                updatedDoc = response.data
              } catch (error) {
                console.error('Failed to fetch document status:', error)
              }
            }

            if (updatedDoc && updatedDoc.status !== currentStatus) {
              setDocumentStatuses((prev) => {
                const newMap = new Map(prev)
                newMap.set(item.id, updatedDoc!.status)
                return newMap
              })

              if (onStatusChange) {
                onStatusChange(item.id, updatedDoc.status)
              }
            }
          } catch (error) {
            console.error(`Error polling document ${item.id}:`, error)
          }
        }
      }
    }, 2000)

    return () => clearInterval(pollInterval)
  }, [documents, documentStatuses, onStatusChange])

  // Calculate aggregate progress
  const processingCount = Array.from(documentStatuses.values()).filter(
    status => status === 'processing'
  ).length
  const processedCount = Array.from(documentStatuses.values()).filter(
    status => status === 'processed'
  ).length
  const errorCount = Array.from(documentStatuses.values()).filter(
    status => status === 'error'
  ).length
  const totalCount = documents.length

  // Calculate overall progress percentage
  const overallProgress = totalCount > 0 
    ? Math.round((processedCount / totalCount) * 100)
    : 0

  // Auto-close if all documents are processed or have errors
  useEffect(() => {
    if (processingCount === 0 && totalCount > 0) {
      // All done - auto close after 2 seconds
      const timer = setTimeout(() => {
        onClose()
      }, 2000)
      return () => clearTimeout(timer)
    }
  }, [processingCount, totalCount, onClose])

  console.log('ProcessingStatusCard render: totalCount =', totalCount, 'processingCount =', processingCount)
  
  if (totalCount === 0) {
    console.log('ProcessingStatusCard: Returning null, no documents')
    return null
  }

  const hasErrors = errorCount > 0
  const isProcessing = processingCount > 0
  const getStatusColor = () => {
    if (hasErrors && !isProcessing) return 'bg-red-600'
    if (!isProcessing) return 'bg-green-600'
    return 'bg-blue-600'
  }

  const getStatusIcon = () => {
    if (!isProcessing && !hasErrors) {
      return <CheckCircle2 className="w-4 h-4 text-green-600" />
    }
    if (hasErrors) {
      return <AlertCircle className="w-4 h-4 text-red-600" />
    }
    return <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 animate-in slide-in-from-bottom-2 duration-300">
      <div className="bg-white rounded-lg shadow-xl border border-gray-200 p-4 w-80 max-w-[calc(100vw-2rem)]">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            {getStatusIcon()}
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-semibold text-gray-900">
                {isProcessing ? `Processing ${processingCount} document${processingCount !== 1 ? 's' : ''}` : 'Processing Complete'}
              </h3>
              <p className="text-xs text-gray-500 mt-0.5">
                {processedCount} of {totalCount} complete
                {errorCount > 0 && ` • ${errorCount} error${errorCount !== 1 ? 's' : ''}`}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors flex-shrink-0 ml-2"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Overall progress bar */}
        <div className="w-full bg-gray-200 rounded-full h-1.5 mb-3 overflow-hidden">
          <div
            className={`h-full ${getStatusColor()} transition-all duration-300 ease-out`}
            style={{ width: `${overallProgress}%` }}
          />
        </div>

        {/* Expandable document list */}
        {documents.length > 0 && (
          <div>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="w-full flex items-center justify-between text-xs text-gray-600 hover:text-gray-900 py-1"
            >
              <span>View documents</span>
              {isExpanded ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </button>

            {isExpanded && (
              <div className="mt-2 max-h-48 overflow-y-auto space-y-1 border-t border-gray-200 pt-2">
                {documents.map((item) => {
                  const status = documentStatuses.get(item.id) || item.document.status || 'processing'
                  const filename = item.document.original_filename || item.document.filename || 'Document'
                  
                  return (
                    <div key={item.id} className="flex items-center justify-between text-xs py-1">
                      <span className="text-gray-700 truncate flex-1 mr-2" title={filename}>
                        {filename}
                      </span>
                      <div className="flex items-center gap-1 flex-shrink-0">
                        {status === 'processed' && (
                          <CheckCircle2 className="w-3 h-3 text-green-600" />
                        )}
                        {status === 'error' && (
                          <AlertCircle className="w-3 h-3 text-red-600" />
                        )}
                        {status === 'processing' && (
                          <Loader2 className="w-3 h-3 text-blue-600 animate-spin" />
                        )}
                        <span className="text-gray-500 capitalize text-[10px]">
                          {status}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

