'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { casesApi, documentsApi, queriesApi, integrationsApi, Case, Document, Query } from '@/lib/api'
import ChatInterface from '@/components/ChatInterface'
import DocumentViewer from '@/components/DocumentViewer'
import DocumentList from '@/components/DocumentList'
import MindmapViewer from '@/components/MindmapViewer'
import GoogleDrivePicker from '@/components/GoogleDrivePicker'
import { Upload, FileText, Share2, Loader2, AlertCircle, X, Search } from 'lucide-react'
import { supabase } from '@/lib/supabase'
import { useDashboard } from '@/lib/dashboard-context'
import Image from 'next/image'

export default function CasePage() {
  const params = useParams()
  const router = useRouter()
  const caseIdParam = params.id as string
  // Check if caseId is a UUID (contains dashes) or a number
  const isUuid = caseIdParam.includes('-')
  const caseId = isUuid ? caseIdParam : parseInt(caseIdParam, 10)
  
  const [caseData, setCaseData] = useState<Case | null>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null)
  const [queries, setQueries] = useState<Query[]>([])
  const [loading, setLoading] = useState(true)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [activeView, setActiveView] = useState<'documents' | 'mindmap' | 'summary'>('documents')
  const [uploadTab, setUploadTab] = useState<'computer' | 'drive'>('computer')
  const [googleDriveConnected, setGoogleDriveConnected] = useState(false)
  const [selectedDriveFiles, setSelectedDriveFiles] = useState<string[]>([])
  const [importingDriveFiles, setImportingDriveFiles] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [driveSearchQuery, setDriveSearchQuery] = useState('')
  const { refreshCases } = useDashboard()

  useEffect(() => {
    loadCaseData()
    loadDocuments()
    loadQueries()
  }, [caseIdParam])

  const loadCaseData = async () => {
    try {
      // If UUID, load from Supabase directly
      if (isUuid) {
        // Update the updated_at timestamp to mark this case as recently viewed
        await supabase
          .from('cases')
          .update({ updated_at: new Date().toISOString() })
          .eq('id', caseIdParam)
        
        // Load the case data
        const { data, error } = await supabase
          .from('cases')
          .select('*')
          .eq('id', caseIdParam)
          .single()
        
        if (error) throw error
        
        if (data) {
          setCaseData({
            id: data.id,
            name: data.name,
            case_number: data.case_number || undefined,
            description: data.description || undefined,
            created_at: data.created_at,
            updated_at: data.updated_at || undefined,
            is_active: data.is_active !== false
          })
          
          // Refresh the cases list in the sidebar to reflect the updated order
          refreshCases()
          
          setLoading(false)
          return
        }
      }
      
      // For numeric IDs, try backend API
      if (!isNaN(caseId as number)) {
        const response = await casesApi.get(caseId as number)
        if (response.data) {
          setCaseData(response.data)
          setLoading(false)
          return
        }
      }
      
      throw new Error('Case not found')
    } catch (error: any) {
      console.error('Failed to load case:', error)
      setLoading(false)
    }
  }

  const loadDocuments = async () => {
    try {
      // If UUID, load from Supabase directly
      if (isUuid) {
        const { data, error } = await supabase
          .from('documents')
          .select('*')
          .eq('case_id', caseIdParam)
          .order('uploaded_at', { ascending: false })
        
        if (error) throw error
        
        if (data) {
          setDocuments(data.map(doc => ({
            id: doc.id,
            case_id: doc.case_id,
            filename: doc.filename || '',
            original_filename: doc.original_filename || doc.filename || '',
            file_type: doc.file_type || 'pdf',
            file_size: doc.file_size || 0,
            status: doc.status || 'pending',
            uploaded_at: doc.uploaded_at || doc.created_at,
            page_count: doc.page_count || 0,
            bates_number: doc.bates_number || undefined,
            author: doc.author || undefined,
            requires_ocr: doc.requires_ocr || false,
            view_count: doc.view_count || 0,
            metadata: doc.metadata || {}
          })))
          setLoading(false)
          return
        }
      }
      
      // For numeric IDs, try backend API
      if (!isNaN(caseId as number)) {
        const response = await documentsApi.list(caseId as number)
        if (response.data) {
          setDocuments(response.data)
          setLoading(false)
          return
        }
      }
    } catch (error: any) {
      console.error('Failed to load documents:', error)
      setDocuments([])
    } finally {
      setLoading(false)
    }
  }

  const loadQueries = async () => {
    try {
      // Only load queries for numeric case IDs (backend doesn't support UUIDs yet)
      if (!isUuid && !isNaN(caseId as number)) {
        const response = await queriesApi.list(caseId as number)
        setQueries(response.data || [])
      } else {
        // For UUID cases, queries aren't supported yet
        setQueries([])
      }
    } catch (error) {
      console.error('Failed to load queries:', error)
      setQueries([])
    }
  }

  const handleFileUpload = async (file: File) => {
    if (!file) return

    setUploading(true)
    try {
      // Validate file type
      const fileExt = file.name.split('.').pop()?.toLowerCase()
      if (!fileExt || !['pdf', 'docx', 'txt'].includes(fileExt)) {
        alert('Invalid file type. Please upload a PDF, DOCX, or TXT file.')
        setUploading(false)
        return
      }

      // For UUID cases, upload directly to Supabase
      if (isUuid) {
        // TODO: Implement Supabase document upload
        console.warn('Document upload for UUID cases not yet implemented')
        alert('Document upload for this case type is not yet available')
      } else if (!isNaN(caseId as number)) {
        await documentsApi.upload(caseId as number, file)
        loadDocuments()
        setShowUploadModal(false)
      }
    } catch (error: any) {
      console.error('Failed to upload document:', error)
      alert(error.response?.data?.detail || 'Failed to upload document')
    } finally {
      setUploading(false)
    }
  }

  const handleFileInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      await handleFileUpload(file)
    }
    // Reset input so same file can be selected again
    e.target.value = ''
  }

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    if (!uploading) {
      setIsDragging(true)
    }
  }

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    if (uploading) return

    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      // Handle the first file (or you could handle multiple files)
      await handleFileUpload(files[0])
    }
  }

  const handleConnectGoogleDrive = async () => {
    try {
      const response = await integrationsApi.google.getAuthUrl()
      if (response.data?.url) {
        window.location.href = response.data.url
      }
    } catch (error: any) {
      console.error('Failed to connect Google Drive:', error)
      alert('Failed to connect Google Drive')
    }
  }


  const handleImportDriveFiles = async () => {
    if (selectedDriveFiles.length === 0) {
      alert('Please select files to import')
      return
    }

    setImportingDriveFiles(true)
    try {
      // Import files using backend API
      // Backend accepts UUID case IDs
      for (const fileId of selectedDriveFiles) {
        await integrationsApi.google.importFile(
          caseIdParam, // Use the string ID (UUID or number as string)
          fileId
        )
      }
      loadDocuments()
      setShowUploadModal(false)
      setSelectedDriveFiles([])
      setUploadTab('computer')
    } catch (error: any) {
      console.error('Failed to import files:', error)
      let errorMessage = 'Failed to import files from Google Drive'
      if (error?.response?.data) {
        if (typeof error.response.data === 'string') {
          errorMessage = error.response.data
        } else if (error.response.data.detail) {
          errorMessage = typeof error.response.data.detail === 'string' 
            ? error.response.data.detail 
            : JSON.stringify(error.response.data.detail)
        } else {
          errorMessage = JSON.stringify(error.response.data)
        }
      } else if (error?.message) {
        errorMessage = error.message
      }
      alert(errorMessage)
    } finally {
      setImportingDriveFiles(false)
    }
  }


  // Check Google Drive connection status when tab is active (in background)
  useEffect(() => {
    const checkDriveStatus = async () => {
      if (!showUploadModal || uploadTab !== 'drive') {
        // Debug logging disabled
        return
      }

      // Check in background without showing separate loading state
      try {
        // Debug logging disabled
        const response = await integrationsApi.google.getStatus()
        // Debug logging disabled
        const isConnected = response.data?.connected || false
        // Debug logging disabled
        setGoogleDriveConnected(isConnected)
      } catch (error: any) {
        // Debug logging disabled
        // If it's an auth error (401), the Supabase token might be expired, not necessarily disconnected
        // Don't change the connection state on auth errors - let the user refresh their session
        if (error?.response?.status !== 401) {
          // For network errors or other non-auth errors, don't change state either
          // Only change state if we get a successful response
        }
        // For all errors, keep existing state to avoid false negatives when token expires
      }
    }

    checkDriveStatus()
  }, [showUploadModal, uploadTab])

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
              caseId={isUuid ? 0 : (caseId as number)}
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
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
          <div className="bg-white rounded-lg p-6 w-full max-w-7xl max-h-[90vh] flex flex-col my-8 relative shadow-2xl">
            {/* Close Button - Top Right */}
            <button
              onClick={() => {
                setShowUploadModal(false)
                setSelectedDriveFiles([])
                setUploadTab('computer')
                setDriveSearchQuery('')
              }}
              className="absolute top-4 right-4 text-gray-500 hover:text-gray-900 transition-colors"
              disabled={uploading || importingDriveFiles}
            >
              <X className="w-6 h-6" />
            </button>
            <h2 className="text-2xl font-bold mb-4 text-gray-900 pr-8">Upload Document</h2>
            
            {/* Tab Switcher */}
            <div className="flex items-center justify-between gap-4 mb-4">
              <div className="flex gap-2">
                <button
                  onClick={() => setUploadTab('computer')}
                  className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                    uploadTab === 'computer'
                      ? 'border-black text-black'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <Upload className="w-4 h-4" />
                  Upload from Computer
                </button>
                <button
                  onClick={() => setUploadTab('drive')}
                  className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                    uploadTab === 'drive'
                      ? 'border-black text-black'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <Image
                    src="/Google_Drive_logo.png"
                    alt="Google Drive"
                    width={16}
                    height={16}
                    className="object-contain"
                  />
                  Import from Google Drive
                </button>
              </div>
              {uploadTab === 'drive' && (
                <div className="flex items-center gap-2">
                  <div className="relative w-64">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search Google Drive..."
                      value={driveSearchQuery}
                      onChange={(e) => setDriveSearchQuery(e.target.value)}
                      className="w-full pl-10 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-0 focus:border-gray-300"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-y-auto min-h-0 relative">
              {uploadTab === 'computer' ? (
                <div 
                  className={`flex flex-col items-center justify-center h-full px-8 py-12 transition-all ${
                    isDragging 
                      ? 'bg-gray-50 border-2 border-dashed border-black' 
                      : 'border-2 border-dashed border-gray-300'
                  } rounded-lg m-4`}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                >
                  <div className="text-center max-w-md">
                    <Upload className={`w-12 h-12 mx-auto mb-4 ${isDragging ? 'text-black' : 'text-gray-400'}`} />
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Upload Document</h3>
                    <p className="text-sm text-gray-600 mb-2">
                      {isDragging 
                        ? 'Drop your file here to upload' 
                        : 'Drag and drop a file here'}
                    </p>
                    <p className="text-xs text-gray-500 mb-6">
                      Supported formats: PDF, DOCX, and TXT files
                    </p>
                    <div className="relative">
                      <input
                        type="file"
                        accept=".pdf,.docx,.txt"
                        onChange={handleFileInputChange}
                        disabled={uploading}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                        id="file-upload"
                      />
                      <label
                        htmlFor="file-upload"
                        className={`inline-flex items-center justify-center px-6 py-3 bg-black text-white rounded-lg hover:bg-gray-900 transition-colors cursor-pointer ${
                          uploading ? 'opacity-50 cursor-not-allowed' : ''
                        }`}
                      >
                        {uploading ? (
                          <>
                            <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                            Uploading...
                          </>
                        ) : (
                          <>
                            <Upload className="w-5 h-5 mr-2" />
                            Choose File
                          </>
                        )}
                      </label>
                    </div>
                    {uploading && (
                      <p className="text-sm text-gray-600 mt-4">Uploading and processing document...</p>
                    )}
                  </div>
                </div>
              ) : (
                <div className="flex flex-col h-full relative min-h-[500px]">
                  {!googleDriveConnected ? (
                    <div className="flex flex-col items-center justify-center h-full min-h-[500px]">
                      <AlertCircle className="w-12 h-12 text-gray-400 mb-4" />
                      <p className="text-sm text-gray-600 mb-4">Connect your Google Drive account to import files</p>
                      <button
                        onClick={handleConnectGoogleDrive}
                        className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-900"
                      >
                        Connect Google Drive
                      </button>
                    </div>
                  ) : (
                    <div className="flex-1 min-h-[500px] border border-gray-200 rounded-lg relative">
                      <GoogleDrivePicker
                        onFileSelect={setSelectedDriveFiles}
                        selectedFileIds={selectedDriveFiles}
                        onInsert={handleImportDriveFiles}
                        searchQuery={driveSearchQuery}
                      />
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Insert Button - Bottom of modal, outside scroll */}
            {uploadTab === 'drive' && selectedDriveFiles.length > 0 && (
              <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 bg-white flex-shrink-0">
                <div className="text-sm text-gray-600">
                  {selectedDriveFiles.length} file{selectedDriveFiles.length !== 1 ? 's' : ''} selected
                </div>
                <button
                  onClick={handleImportDriveFiles}
                  disabled={importingDriveFiles}
                  className="px-6 py-2 bg-black text-white rounded-lg hover:bg-gray-900 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {importingDriveFiles ? 'Importing...' : 'Insert'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

