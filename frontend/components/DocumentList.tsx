'use client'

import { useState, useEffect, useRef } from 'react'
import { Document, documentsApi } from '@/lib/api'
import { FileText, CheckCircle, Clock, AlertCircle, Search } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9000'

const getThumbnailUrl = (document: Document): string | null => {
  if (!document.thumbnail_path) return null
  return `${API_URL}/api/v1/documents/${document.id}/thumbnail`
}

// Component to display thumbnail with fallback
function ThumbnailImage({ src, alt, fallback }: { src: string; alt: string; fallback: React.ReactNode }) {
  const [imgSrc, setImgSrc] = useState<string | null>(null)
  const [imgError, setImgError] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Fetch image with authentication token since img src can't send headers
    let currentObjectUrl: string | null = null
    
    const fetchThumbnail = async () => {
      try {
        const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
        if (!token || token.startsWith('dev-token-') || token.length <= 50) {
          // No valid token, skip thumbnail
          setImgError(true)
          setIsLoading(false)
          return
        }

        // Add timeout to prevent infinite loading
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 10000) // 10 second timeout

        const response = await fetch(src, {
          headers: {
            'Authorization': `Bearer ${token}`
          },
          signal: controller.signal
        })

        clearTimeout(timeoutId)

        if (!response.ok) {
          console.error(`Thumbnail fetch failed: ${response.status} ${response.statusText}`)
          throw new Error(`Failed to fetch thumbnail: ${response.status}`)
        }

        const blob = await response.blob()
        if (blob.size === 0) {
          throw new Error('Thumbnail is empty')
        }

        currentObjectUrl = URL.createObjectURL(blob)
        setImgSrc(currentObjectUrl)
        setIsLoading(false)
      } catch (error: any) {
        // Handle timeout
        if (error.name === 'AbortError') {
          console.error('Thumbnail fetch timeout:', src)
        } else {
          console.error('Error loading thumbnail:', error)
        }
        setImgError(true)
        setIsLoading(false)
      }
    }

    fetchThumbnail()

    // Cleanup object URL on unmount or when src changes
    return () => {
      if (currentObjectUrl) {
        URL.revokeObjectURL(currentObjectUrl)
      }
      // Also clean up previous imgSrc if it exists
      setImgSrc((prev) => {
        if (prev) {
          URL.revokeObjectURL(prev)
        }
        return null
      })
    }
  }, [src])

  if (imgError || !imgSrc) {
    return <div className="mt-0.5 flex-shrink-0">{fallback}</div>
  }

  return (
    <div className="relative w-12 h-12 mt-0.5 flex-shrink-0 rounded border border-gray-200 bg-gray-50 overflow-hidden">
      <img
        src={imgSrc}
        alt={alt}
        className="w-full h-full object-cover"
        onError={() => {
          setIsLoading(false)
          setImgError(true)
        }}
        style={{ display: isLoading ? 'none' : 'block' }}
      />
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-4 h-4 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
        </div>
      )}
    </div>
  )
}

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
  const [searchQuery, setSearchQuery] = useState('')

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

  // Filter and sort documents based on search query
  const filteredAndSortedDocuments = documents
    .filter((doc) => {
      if (!searchQuery.trim()) return true
      
      const query = searchQuery.toLowerCase().trim()
      const filename = doc.original_filename?.toLowerCase() || ''
      const batesNumber = doc.bates_number?.toLowerCase() || ''
      const custodian = doc.custodian?.toLowerCase() || ''
      const author = doc.author?.toLowerCase() || ''
      const fileType = doc.file_type?.toLowerCase() || ''
      
      // Check if any field contains the search query
      return (
        filename.includes(query) ||
        batesNumber.includes(query) ||
        custodian.includes(query) ||
        author.includes(query) ||
        fileType.includes(query)
      )
    })
    .sort((a, b) => {
      if (!searchQuery.trim()) return 0
      
      const query = searchQuery.toLowerCase().trim()
      
      // Calculate relevance score for each document
      const getRelevanceScore = (doc: Document): number => {
        let score = 0
        const filename = doc.original_filename?.toLowerCase() || ''
        const batesNumber = doc.bates_number?.toLowerCase() || ''
        const custodian = doc.custodian?.toLowerCase() || ''
        const author = doc.author?.toLowerCase() || ''
        
        // Higher score for matches in filename (most important)
        if (filename.includes(query)) {
          score += 10
          // Even higher if it starts with the query
          if (filename.startsWith(query)) score += 5
        }
        
        // Medium score for bates number match
        if (batesNumber.includes(query)) score += 5
        
        // Lower score for custodian/author match
        if (custodian.includes(query)) score += 3
        if (author.includes(query)) score += 3
        
        return score
      }
      
      const scoreA = getRelevanceScore(a)
      const scoreB = getRelevanceScore(b)
      
      // Sort by relevance score (descending), then by filename alphabetically
      if (scoreB !== scoreA) {
        return scoreB - scoreA
      }
      return (a.original_filename || '').localeCompare(b.original_filename || '')
    })

  return (
    <div ref={containerRef} className="h-full bg-gray-50 flex flex-col">
      {/* Documents Header */}
      <div className="px-4 py-3 border-b border-gray-200 bg-white">
        <h3 className="text-sm font-semibold text-gray-900">Documents</h3>
        <p className="text-xs text-gray-600">
          {searchQuery.trim() 
            ? `${filteredAndSortedDocuments.length} of ${documents.length} files`
            : `${documents.length} files`
          }
        </p>
      </div>
      
      {/* Search Box */}
      <div className="px-4 py-3 border-b border-gray-200 bg-white">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search Documents"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
          />
        </div>
      </div>
      
      {/* Documents List */}
      <div className="flex-1 overflow-y-auto">
        {documents.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <FileText className="w-12 h-12 mx-auto mb-2 text-gray-600" />
            <p className="text-sm">No documents yet</p>
          </div>
        ) : filteredAndSortedDocuments.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <FileText className="w-12 h-12 mx-auto mb-2 text-gray-600" />
            <p className="text-sm">No documents found</p>
            <p className="text-xs text-gray-400 mt-1">Try a different search term</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredAndSortedDocuments.map((doc) => (
              <button
                key={doc.id}
                onClick={() => onSelectDocument(doc)}
                className={`w-full text-left p-4 hover:bg-gray-200 transition-colors ${
                  selectedDocument?.id === doc.id ? 'bg-gray-200 border-l-4 border-[#000000]' : ''
                }`}
              >
                <div className="flex items-start gap-3">
                  {(() => {
                    const thumbnailUrl = getThumbnailUrl(doc)
                    if (thumbnailUrl) {
                      return (
                        <ThumbnailImage
                          src={thumbnailUrl}
                          alt={doc.original_filename}
                          fallback={<FileText className="w-5 h-5 text-gray-600" />}
                        />
                      )
                    }
                    return <FileText className="w-5 h-5 mt-0.5 flex-shrink-0 text-gray-600" />
                  })()}
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

