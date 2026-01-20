'use client'

import { useState, useEffect } from 'react'
import { integrationsApi, GoogleDriveFile } from '@/lib/api'
import Image from 'next/image'
import { 
  Folder, 
  File, 
  FileText, 
  FileSpreadsheet, 
  Presentation, 
  Image as ImageIcon,
  FileCode,
  FileVideo,
  FileAudio,
  Archive,
  ChevronRight, 
  Loader2, 
  AlertCircle, 
  Grid, 
  List as ListIcon 
} from 'lucide-react'

interface GoogleDrivePickerProps {
  onFileSelect: (fileIds: string[]) => void
  selectedFileIds: string[]
  onInsert: () => void
  searchQuery?: string
}

export default function GoogleDrivePicker({ onFileSelect, selectedFileIds, onInsert, searchQuery = '' }: GoogleDrivePickerProps) {
  const [files, setFiles] = useState<GoogleDriveFile[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isInitialLoad, setIsInitialLoad] = useState(true)
  const [currentFolderId, setCurrentFolderId] = useState<string | undefined>(undefined)
  const [folderStack, setFolderStack] = useState<Array<{ id: string | undefined; name: string }>>([
    { id: undefined, name: 'My Drive' }
  ])
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [activeTab, setActiveTab] = useState<'myDrive' | 'recent' | 'shared'>('myDrive')

  useEffect(() => {
    loadFiles()
  }, [currentFolderId, activeTab, searchQuery])

  const loadFiles = async () => {
    // Clear error first, then set loading to prevent flash of error message
    setError(null)
    setFiles([]) // Clear files immediately to show loading state
    setLoading(true)
    
    try {
      let response
      if (activeTab === 'myDrive') {
        response = await integrationsApi.google.listFiles(currentFolderId, searchQuery)
      } else if (activeTab === 'recent') {
        response = await integrationsApi.google.listRecent(searchQuery)
      } else if (activeTab === 'shared') {
        response = await integrationsApi.google.listShared(searchQuery)
      } else {
        response = await integrationsApi.google.listFiles(currentFolderId, searchQuery)
      }
      
      const files = response.data.files || []
      setFiles(files)
      setIsInitialLoad(false)
    } catch (err: any) {
      console.error('Error loading Google Drive files:', err)
      // Add a small delay before showing error to prevent flash
      // This ensures loading state is shown first
      await new Promise(resolve => setTimeout(resolve, 100))
      setError(err.response?.data?.detail || 'Failed to load files from Google Drive')
      setIsInitialLoad(false)
    } finally {
      setLoading(false)
    }
  }

  const handleTabChange = (tab: 'myDrive' | 'recent' | 'shared') => {
    setActiveTab(tab)
    setCurrentFolderId(undefined)
    setFolderStack([{ id: undefined, name: tab === 'myDrive' ? 'My Drive' : tab === 'recent' ? 'Recent' : 'Shared with me' }])
  }

  const handleFolderClick = (folder: GoogleDriveFile) => {
    if (folder.mimeType === 'application/vnd.google-apps.folder') {
      // Only allow folder navigation in My Drive tab
      if (activeTab === 'myDrive') {
        setCurrentFolderId(folder.id)
        setFolderStack([...folderStack, { id: folder.id, name: folder.name }])
      }
    }
  }

  const handleBreadcrumbClick = (index: number) => {
    const newStack = folderStack.slice(0, index + 1)
    setFolderStack(newStack)
    const targetFolder = newStack[newStack.length - 1]
    setCurrentFolderId(targetFolder.id)
  }

  const handleFileToggle = (fileId: string) => {
    if (selectedFileIds.includes(fileId)) {
      onFileSelect(selectedFileIds.filter(id => id !== fileId))
    } else {
      onFileSelect([...selectedFileIds, fileId])
    }
  }

  const isFolder = (mimeType: string) => mimeType === 'application/vnd.google-apps.folder'
  const isSelectable = (mimeType: string) => {
    // Only allow files, not folders
    return !isFolder(mimeType)
  }

  const formatFileSize = (size?: string) => {
    if (!size) return ''
    const bytes = parseInt(size)
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  // Get appropriate icon for file type based on mime type
  const getFileIcon = (mimeType: string, className?: string) => {
    const baseClass = className || 'w-12 h-12'
    const lightGray = 'text-gray-400'
    const cardIconColor = '#d9d9d9' // Light gray for document card icons
    
    if (isFolder(mimeType)) {
      return <Folder className={`${baseClass} ${lightGray}`} style={{ color: cardIconColor }} />
    }

    // Google Workspace files
    if (mimeType === 'application/vnd.google-apps.document') {
      return <FileText className={`${baseClass} ${lightGray}`} style={{ color: cardIconColor }} />
    }
    if (mimeType === 'application/vnd.google-apps.spreadsheet') {
      return <FileSpreadsheet className={`${baseClass} ${lightGray}`} style={{ color: cardIconColor }} />
    }
    if (mimeType === 'application/vnd.google-apps.presentation') {
      return <Presentation className={`${baseClass} ${lightGray}`} style={{ color: cardIconColor }} />
    }
    if (mimeType === 'application/vnd.google-apps.form') {
      return <FileText className={`${baseClass} ${lightGray}`} style={{ color: cardIconColor }} />
    }
    if (mimeType === 'application/vnd.google-apps.drawing') {
      return <ImageIcon className={`${baseClass} ${lightGray}`} style={{ color: cardIconColor }} />
    }

    // Microsoft Office files
    if (mimeType.includes('wordprocessingml') || mimeType === 'application/msword') {
      return <FileText className={`${baseClass} ${lightGray}`} style={{ color: cardIconColor }} />
    }
    if (mimeType.includes('spreadsheetml') || mimeType === 'application/vnd.ms-excel') {
      return <FileSpreadsheet className={`${baseClass} ${lightGray}`} style={{ color: cardIconColor }} />
    }
    if (mimeType.includes('presentationml') || mimeType === 'application/vnd.ms-powerpoint') {
      return <Presentation className={`${baseClass} ${lightGray}`} style={{ color: cardIconColor }} />
    }

    // PDF
    if (mimeType === 'application/pdf') {
      return <FileText className={`${baseClass} ${lightGray}`} style={{ color: cardIconColor }} />
    }

    // Images
    if (mimeType.startsWith('image/')) {
      return <ImageIcon className={`${baseClass} ${lightGray}`} style={{ color: cardIconColor }} />
    }

    // Video
    if (mimeType.startsWith('video/')) {
      return <FileVideo className={`${baseClass} ${lightGray}`} style={{ color: cardIconColor }} />
    }

    // Audio
    if (mimeType.startsWith('audio/')) {
      return <FileAudio className={`${baseClass} ${lightGray}`} style={{ color: cardIconColor }} />
    }

    // Archives
    if (mimeType === 'application/zip' || 
        mimeType === 'application/x-zip-compressed' ||
        mimeType === 'application/x-rar-compressed' ||
        mimeType === 'application/x-7z-compressed' ||
        mimeType === 'application/x-tar' ||
        mimeType === 'application/gzip') {
      return <Archive className={`${baseClass} ${lightGray}`} style={{ color: cardIconColor }} />
    }

    // Code files
    if (mimeType.startsWith('text/') || 
        mimeType.includes('javascript') ||
        mimeType.includes('json') ||
        mimeType.includes('xml') ||
        mimeType.includes('html') ||
        mimeType.includes('css')) {
      return <FileCode className={`${baseClass} ${lightGray}`} style={{ color: cardIconColor }} />
    }

    // Default file icon - use light gray
    return <File className={`${baseClass} ${lightGray}`} style={{ color: cardIconColor }} />
  }

  // Get document type icon path for small icons in card footer
  const getDocumentTypeIcon = (mimeType: string): string | null => {
    // Google Docs
    if (mimeType === 'application/vnd.google-apps.document') {
      return '/docs.png'
    }
    // Google Sheets
    if (mimeType === 'application/vnd.google-apps.spreadsheet') {
      return '/sheets.png'
    }
    // Google Slides
    if (mimeType === 'application/vnd.google-apps.presentation') {
      return '/slides.png'
    }
    // PDFs
    if (mimeType === 'application/pdf') {
      return '/file.png'
    }
    // Images
    if (mimeType.startsWith('image/')) {
      return '/png.png'
    }
    // Default icon for all other file types
    return '/default.png'
  }
  
  // Debug: log mimeTypes to see what we're getting
  useEffect(() => {
    if (files.length > 0) {
      console.log('Google Drive file mimeTypes:', files.map(f => ({ name: f.name, mimeType: f.mimeType })))
    }
  }, [files])

  return (
    <div className="flex flex-col h-full min-h-0 relative">
      {/* Tabs */}
      <div className="flex gap-2 px-4 py-2 border-b border-gray-200 flex-shrink-0">
        <button
          onClick={() => handleTabChange('myDrive')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'myDrive'
              ? 'border-black text-black'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          My Drive
        </button>
        <button
          onClick={() => handleTabChange('recent')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'recent'
              ? 'border-black text-black'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Recent
        </button>
        <button
          onClick={() => handleTabChange('shared')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'shared'
              ? 'border-black text-black'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Shared with me
        </button>
      </div>

      {/* Header with breadcrumbs and view toggle */}
      {activeTab === 'myDrive' && (
        <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 flex-shrink-0">
          <div className="flex items-center gap-1 text-sm text-gray-600 flex-1 min-w-0">
            {folderStack.map((folder, index) => (
              <div key={index} className="flex items-center gap-1">
                {index > 0 && <ChevronRight className="w-4 h-4 flex-shrink-0" />}
                <button
                  onClick={() => handleBreadcrumbClick(index)}
                  className={`hover:text-gray-900 truncate ${index === folderStack.length - 1 ? 'font-semibold text-gray-900' : ''}`}
                >
                  {folder.name}
                </button>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-1 border border-gray-300 rounded-lg p-1 ml-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded transition-colors ${
                viewMode === 'grid'
                  ? 'bg-gray-200 text-gray-900'
                  : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
              }`}
              title="Grid View"
            >
              <Grid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded transition-colors ${
                viewMode === 'list'
                  ? 'bg-gray-200 text-gray-900'
                  : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
              }`}
              title="List View"
            >
              <ListIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
      {activeTab !== 'myDrive' && (
        <div className="flex items-center justify-end px-4 py-2 border-b border-gray-200 flex-shrink-0">
          <div className="flex items-center gap-1 border border-gray-300 rounded-lg p-1">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded transition-colors ${
                viewMode === 'grid'
                  ? 'bg-gray-200 text-gray-900'
                  : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
              }`}
              title="Grid View"
            >
              <Grid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded transition-colors ${
                viewMode === 'list'
                  ? 'bg-gray-200 text-gray-900'
                  : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
              }`}
              title="List View"
            >
              <ListIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* File Content */}
      <div className="flex-1 overflow-y-auto relative min-h-0">
        {loading ? (
          <div className="flex flex-col items-center justify-center h-full min-h-[400px] gap-4">
            <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
            <div className="text-center">
              <p className="text-sm font-medium text-gray-900 mb-1">Loading Google Drive</p>
              <p className="text-xs text-gray-500">Fetching your files and folders...</p>
            </div>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-full p-4">
            <AlertCircle className="w-8 h-8 text-red-500 mb-2" />
            <p className="text-sm text-red-600 text-center">{error}</p>
            <button
              onClick={loadFiles}
              className="mt-4 px-4 py-2 text-sm bg-black text-white rounded-lg hover:bg-gray-900"
            >
              Retry
            </button>
          </div>
        ) : files.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full p-4 text-gray-500">
            <Folder className="w-12 h-12 mb-2 text-gray-400" />
            <p className="text-sm">This folder is empty</p>
          </div>
        ) : viewMode === 'grid' ? (
          <div className="flex flex-col min-h-[400px] overflow-y-auto p-4">
            {/* Folders Section - At the top */}
            {files.some(f => isFolder(f.mimeType)) && (
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Folders</h3>
                <div className="grid grid-cols-6 gap-3">
                  {files
                    .filter(file => isFolder(file.mimeType))
                    .map((folder) => (
                      <div
                        key={folder.id}
                        className="border border-gray-200 rounded-lg cursor-pointer transition-all hover:shadow-md bg-white px-4 py-3 flex items-center gap-3"
                        onClick={() => handleFolderClick(folder)}
                      >
                        <Folder className="w-6 h-6 flex-shrink-0" style={{ color: '#0584c7', fill: '#0584c7' }} />
                        <p className="text-sm font-medium text-gray-900 truncate flex-1" title={folder.name}>
                          {folder.name}
                        </p>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* Documents Section - Below folders, 6 across with icons */}
            {files.some(f => !isFolder(f.mimeType)) && (
              <div>
                {files.some(f => isFolder(f.mimeType)) && (
                  <h3 className="text-sm font-semibold text-gray-900 mb-3">Documents</h3>
                )}
                <div className="grid grid-cols-6 gap-4">
                  {files
                    .filter(file => !isFolder(file.mimeType))
                    .map((file) => {
                      const isSelected = selectedFileIds.includes(file.id)
                      const canSelect = isSelectable(file.mimeType)
                      
                      return (
                        <div
                          key={file.id}
                          className={`relative border rounded-lg overflow-hidden cursor-pointer transition-all ${
                            isSelected ? 'border-2 border-black' : 'border border-gray-200 hover:border-gray-300'
                          }`}
                          onClick={() => {
                            if (canSelect) {
                              handleFileToggle(file.id)
                            }
                          }}
                        >
                          {/* File Icon */}
                          <div className="aspect-square bg-white flex items-center justify-center relative overflow-hidden border-b border-gray-200">
                            {getFileIcon(file.mimeType, 'w-16 h-16')}
                          </div>
                          {/* File Name */}
                          <div className="p-2 bg-white">
                            <p className="text-xs font-medium text-gray-900 truncate" title={file.name}>
                              {file.name}
                            </p>
                            <div className="flex items-center justify-between mt-0.5 min-h-[20px]">
                              {file.size ? (
                                <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                              ) : (
                                <span></span>
                              )}
                              {(() => {
                                const iconPath = getDocumentTypeIcon(file.mimeType)
                                
                                if (iconPath) {
                                  return (
                                    <img
                                      src={iconPath}
                                      alt="Document type"
                                      width={20}
                                      height={20}
                                      className="object-contain flex-shrink-0 ml-2"
                                      style={{ display: 'block', minWidth: '20px', minHeight: '20px' }}
                                      onError={(e) => {
                                        console.error('Failed to load document type icon:', iconPath)
                                        console.error('File mimeType:', file.mimeType, 'File name:', file.name)
                                      }}
                                      onLoad={() => {
                                        console.log('Successfully loaded icon for:', file.name, 'mimeType:', file.mimeType, 'path:', iconPath)
                                      }}
                                    />
                                  )
                                }
                                return null
                              })()}
                            </div>
                          </div>
                        </div>
                      )
                    })}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {[...files].sort((a, b) => {
              // Folders first, then documents
              const aIsFolder = isFolder(a.mimeType)
              const bIsFolder = isFolder(b.mimeType)
              if (aIsFolder && !bIsFolder) return -1
              if (!aIsFolder && bIsFolder) return 1
              return 0
            }).map((file) => {
              const isSelected = selectedFileIds.includes(file.id)
              const canSelect = isSelectable(file.mimeType)
              
              return (
                <div
                  key={file.id}
                  className={`flex items-center gap-3 px-4 py-3 hover:bg-gray-50 ${
                    isFolder(file.mimeType) ? 'cursor-pointer' : ''
                  } ${isSelected ? 'bg-blue-50 border-l-2 border-black' : ''}`}
                  onClick={() => {
                    if (isFolder(file.mimeType)) {
                      handleFolderClick(file)
                    } else if (canSelect) {
                      handleFileToggle(file.id)
                    }
                  }}
                >
                  {/* File Icon */}
                  <div className="w-10 h-10 flex-shrink-0 bg-white rounded flex items-center justify-center overflow-hidden relative">
                    {isFolder(file.mimeType) ? (
                      <Folder className="w-6 h-6" style={{ color: '#0584c7', fill: '#0584c7' }} />
                    ) : getDocumentTypeIcon(file.mimeType) ? (
                      <img
                        src={getDocumentTypeIcon(file.mimeType)!}
                        alt="Document type"
                        width={24}
                        height={24}
                        className="object-contain"
                      />
                    ) : (
                      getFileIcon(file.mimeType, 'w-6 h-6')
                    )}
                  </div>
                  {/* File Info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
                    {file.size && (
                      <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

    </div>
  )
}
