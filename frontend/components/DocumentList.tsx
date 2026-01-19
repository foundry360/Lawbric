'use client'

import { useState, useEffect, useRef } from 'react'
import { Document } from '@/lib/api'
import { FileText, CheckCircle, Clock, AlertCircle } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

interface DocumentListProps {
  documents: Document[]
  selectedDocument: Document | null
  onSelectDocument: (doc: Document) => void
}

export default function DocumentList({
  documents,
  selectedDocument,
  onSelectDocument,
}: DocumentListProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [showUploadDate, setShowUploadDate] = useState(true)

  useEffect(() => {
    const checkWidth = () => {
      if (containerRef.current) {
        const width = containerRef.current.offsetWidth
        // Hide uploaded date if panel is narrower than 280px
        setShowUploadDate(width >= 280)
      }
    }

    checkWidth()
    const resizeObserver = new ResizeObserver(checkWidth)
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current)
    }

    return () => {
      resizeObserver.disconnect()
    }
  }, [])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'processed':
        return <CheckCircle className="w-4 h-4 text-green-600" />
      case 'processing':
        return <Clock className="w-4 h-4 text-yellow-600" />
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-600" />
      default:
        return <Clock className="w-4 h-4 text-gray-400" />
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  return (
    <div ref={containerRef} className="h-full bg-gray-50">
      <div className="px-4 py-3 border-b border-gray-200 bg-white">
        <h3 className="text-sm font-semibold text-gray-900">Documents</h3>
        <p className="text-xs text-gray-600">{documents.length} files</p>
      </div>
      <div className="overflow-y-auto">
        {documents.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
                    <FileText className="w-12 h-12 mx-auto mb-2 text-gray-600" />
            <p className="text-sm">No documents yet</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {documents.map((doc) => (
              <button
                key={doc.id}
                onClick={() => onSelectDocument(doc)}
                className={`w-full text-left p-4 hover:bg-gray-200 transition-colors ${
                  selectedDocument?.id === doc.id ? 'bg-gray-200 border-l-4 border-[#000000]' : ''
                }`}
              >
                <div className="flex items-start gap-3">
                  <FileText className="w-5 h-5 mt-0.5 flex-shrink-0 text-gray-600" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 min-w-0">
                      <p className="text-xs font-medium text-gray-900 truncate flex-1 min-w-0">
                        {doc.original_filename}
                      </p>
                      <div className="flex-shrink-0">
                        {getStatusIcon(doc.status)}
                      </div>
                    </div>
                    <div className="text-[11px] text-gray-500">
                      <p className="mb-0">
                        {formatFileSize(doc.file_size)} • {doc.file_type.toUpperCase()}
                        {doc.page_count && ` • ${doc.page_count} pages`}
                        {doc.bates_number && ` • Bates: ${doc.bates_number}`}
                      </p>
                      {showUploadDate && (
                        <p className="mb-0 mt-0.5">
                          Uploaded {formatDistanceToNow(new Date(doc.uploaded_at), { addSuffix: true })}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

