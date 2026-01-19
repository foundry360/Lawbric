'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { casesApi, documentsApi, queriesApi, Case, Document, Query } from '@/lib/api'
import ChatInterface from '@/components/ChatInterface'
import DocumentViewer from '@/components/DocumentViewer'
import DocumentList from '@/components/DocumentList'
import MindmapViewer from '@/components/MindmapViewer'
import { Upload, FileText, Share2 } from 'lucide-react'

export default function CasePage() {
  const params = useParams()
  const router = useRouter()
  const caseId = parseInt(params.id as string)
  
  const [caseData, setCaseData] = useState<Case | null>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null)
  const [queries, setQueries] = useState<Query[]>([])
  const [loading, setLoading] = useState(true)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [activeView, setActiveView] = useState<'documents' | 'mindmap' | 'summary'>('documents')

  useEffect(() => {
    loadCaseData()
    loadDocuments()
    loadQueries()
  }, [caseId])

  const loadCaseData = async () => {
    try {
      const response = await casesApi.get(caseId)
      if (response.data) {
        setCaseData(response.data)
      } else {
        // If no data returned, use mock data
        throw new Error('No data returned')
      }
    } catch (error: any) {
      console.error('Failed to load case:', error)
      // If backend is unavailable, use mock data (dev mode)
      const devBypass = typeof window !== 'undefined' && localStorage.getItem('devBypass') === 'true'
      if (error.code === 'ECONNREFUSED' || error.message?.includes('Network Error') || error.isDevBypass || devBypass || !error.response) {
        const mockCases: Record<number, Case> = {
          1: {
            id: 1,
            name: 'Adams v. New York State Department of Transportation and Infrastructure',
            case_number: 'NY459870',
            description: 'Sample case for development',
            created_at: new Date().toISOString(),
            is_active: true,
          },
          2: {
            id: 2,
            name: 'Smith v. Johnson Corporation',
            case_number: 'CA2024-1234',
            description: 'Sample case for development',
            created_at: new Date(Date.now() - 86400000).toISOString(),
            is_active: true,
          },
          3: {
            id: 3,
            name: 'Williams Estate v. Metropolitan Insurance',
            case_number: 'TX-789456',
            description: 'Sample case for development',
            created_at: new Date(Date.now() - 172800000).toISOString(),
            is_active: true,
          },
        }
        const mockCase = mockCases[caseId] || mockCases[1] // Default to case 1 if caseId not found
        setCaseData(mockCase)
        setLoading(false) // Set loading to false when using mock data
      }
    }
  }

  const loadDocuments = async () => {
    try {
      const response = await documentsApi.list(caseId)
      if (response.data && response.data.length > 0) {
        setDocuments(response.data)
      } else {
        // If no data returned, use mock data
        throw new Error('No data returned')
      }
    } catch (error: any) {
      console.error('Failed to load documents:', error)
      // If backend is unavailable, use mock data (dev mode)
      const devBypass = typeof window !== 'undefined' && localStorage.getItem('devBypass') === 'true'
      if (error.code === 'ECONNREFUSED' || error.message?.includes('Network Error') || error.isDevBypass || devBypass || !error.response || error.message === 'No data returned') {
        const mockDocuments: Document[] = [
          {
            id: 1,
            case_id: caseId,
            filename: 'deposition_transcript_john_smith_2024.pdf',
            original_filename: 'Deposition Transcript - John Smith - March 15, 2024.pdf',
            file_type: 'pdf',
            file_size: 2456789,
            status: 'processed',
            uploaded_at: new Date(Date.now() - 86400000).toISOString(),
            page_count: 45,
            bates_number: 'ADAMS-000001',
            author: 'Court Reporter Services',
            requires_ocr: false,
            view_count: 12,
            metadata: {
              custodian: 'John Smith',
              document_date: '2024-03-15',
              source: 'Deposition',
            },
          },
          {
            id: 2,
            case_id: caseId,
            filename: 'contract_agreement_2023.pdf',
            original_filename: 'Service Agreement Contract - 2023.pdf',
            file_type: 'pdf',
            file_size: 1234567,
            status: 'processed',
            uploaded_at: new Date(Date.now() - 172800000).toISOString(),
            page_count: 12,
            bates_number: 'ADAMS-000002',
            author: 'Legal Department',
            requires_ocr: false,
            view_count: 8,
            metadata: {
              custodian: 'Legal Department',
              document_date: '2023-06-20',
              source: 'Contract',
            },
          },
          {
            id: 3,
            case_id: caseId,
            filename: 'email_correspondence_chain.pdf',
            original_filename: 'Email Correspondence Chain - Q1 2024.pdf',
            file_type: 'pdf',
            file_size: 567890,
            status: 'processing',
            uploaded_at: new Date(Date.now() - 3600000).toISOString(),
            page_count: 8,
            bates_number: 'ADAMS-000003',
            author: 'Sarah Johnson',
            requires_ocr: true,
            view_count: 3,
            metadata: {
              custodian: 'Sarah Johnson',
              document_date: '2024-01-15',
              source: 'Email',
            },
          },
        ]
        setDocuments(mockDocuments)
      }
    } finally {
      setLoading(false)
    }
  }

  const loadQueries = async () => {
    try {
      const response = await queriesApi.list(caseId)
      setQueries(response.data)
    } catch (error) {
      console.error('Failed to load queries:', error)
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    try {
      await documentsApi.upload(caseId, file)
      loadDocuments()
      setShowUploadModal(false)
    } catch (error: any) {
      console.error('Failed to upload document:', error)
      alert(error.response?.data?.detail || 'Failed to upload document')
    } finally {
      setUploading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-lg">Loading case...</div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Case Header */}
      <div className="border-b border-gray-200 px-6 py-4 relative">
        <div className="flex items-center justify-between">
          {/* View Switcher Tabs */}
          <div className="flex items-center gap-1">
            <button
              onClick={() => setActiveView('documents')}
              className={`px-4 py-2 text-sm font-medium transition-colors relative ${
                activeView === 'documents'
                  ? 'text-gray-900'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Documents
              {activeView === 'documents' && (
                <div className="absolute bottom-0 left-0 right-0 h-[3px] bg-black"></div>
              )}
            </button>
            <button
              onClick={() => setActiveView('mindmap')}
              className={`px-4 py-2 text-sm font-medium transition-colors relative ${
                activeView === 'mindmap'
                  ? 'text-gray-900'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Mindmap
              {activeView === 'mindmap' && (
                <div className="absolute bottom-0 left-0 right-0 h-[3px] bg-black"></div>
              )}
            </button>
            <button
              onClick={() => setActiveView('summary')}
              className={`px-4 py-2 text-sm font-medium transition-colors relative ${
                activeView === 'summary'
                  ? 'text-gray-900'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Case Summary
              {activeView === 'summary' && (
                <div className="absolute bottom-0 left-0 right-0 h-[3px] bg-black"></div>
              )}
            </button>
          </div>
          
          {/* Case Name - Centered */}
          <div className="flex items-center gap-3 absolute left-1/2 transform -translate-x-1/2">
            <h1 className="text-[18px] font-bold text-gray-900">
              {caseData ? caseData.name : 'Loading...'}
            </h1>
            {caseData?.case_number && (
              <span className="text-sm text-gray-600">Case #: {caseData.case_number}</span>
            )}
          </div>
          
          {/* Toolbar - Right */}
          <div className="flex items-center gap-2">
            <button
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="Share"
            >
              <Share2 className="w-5 h-5 text-gray-600" />
            </button>
            <button
              onClick={() => setShowUploadModal(true)}
              className="bg-black text-white px-3 py-1.5 rounded-lg hover:bg-gray-800 flex items-center gap-2 text-sm"
            >
              <Upload className="w-4 h-4" />
              Upload Document
            </button>
          </div>
        </div>
      </div>

      {/* Main Content - Conditional based on activeView */}
      {activeView === 'documents' && (
        <div className="flex-1 flex overflow-hidden">
          {/* Left Panel - Chat */}
          <div className="border-r border-gray-200 flex flex-col" style={{ width: '30%' }}>
            <ChatInterface
              caseId={caseId}
              queries={queries}
              onQuerySubmit={loadQueries}
              selectedDocument={selectedDocument}
            />
          </div>

          {/* Right Panel - Documents */}
          <div className="flex flex-col" style={{ width: '70%' }}>
            <div className="flex-1 overflow-hidden flex">
              {/* Document List */}
              <div className="border-r border-gray-200 overflow-y-auto" style={{ width: '35.71%' }}>
                <DocumentList
                  documents={documents}
                  selectedDocument={selectedDocument}
                  onSelectDocument={setSelectedDocument}
                />
              </div>
              
              {/* Document Viewer */}
              <div className="overflow-y-auto" style={{ width: '64.29%' }}>
                {selectedDocument ? (
                  <DocumentViewer 
                    document={selectedDocument} 
                    onDocumentDeleted={() => {
                      setSelectedDocument(null)
                      loadDocuments()
                    }}
                  />
                ) : (
                  <div className="h-full flex items-center justify-center text-gray-500">
                    <div className="text-center">
                      <FileText className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                      <p>Select a document to view</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeView === 'mindmap' && (
        <div className="flex-1 overflow-hidden">
          <MindmapViewer
            caseData={caseData}
            documents={documents}
            queries={queries}
            onDocumentSelect={(documentId) => {
              const doc = documents.find(d => d.id === documentId)
              if (doc) {
                setSelectedDocument(doc)
                setActiveView('documents')
              }
            }}
            onQuerySelect={(queryId) => {
              // Could scroll to query in documents view if needed
              console.log('Selected query:', queryId)
            }}
          />
        </div>
      )}

      {activeView === 'summary' && (
        <div className="flex-1 overflow-hidden">
          {/* Case Summary component will go here */}
          <div className="h-full flex items-center justify-center text-gray-500">
            <div className="text-center">
              <p className="text-lg mb-2">Case Summary View</p>
              <p className="text-sm">Coming soon...</p>
            </div>
          </div>
        </div>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-2xl font-bold mb-4">Upload Document</h2>
            <input
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={handleFileUpload}
              disabled={uploading}
              className="w-full mb-4"
            />
            {uploading && (
              <p className="text-sm text-gray-600">Uploading and processing document...</p>
            )}
            <button
              onClick={() => setShowUploadModal(false)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
              disabled={uploading}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

