'use client'

import { useState, useEffect } from 'react'
import { integrationsApi, GoogleDriveFile } from '@/lib/api'
import { Folder, File, ChevronRight, Loader2, AlertCircle } from 'lucide-react'

interface GoogleDriveBrowserProps {
  onFileSelect: (fileIds: string[]) => void
  selectedFileIds: string[]
}

export default function GoogleDriveBrowser({ onFileSelect, selectedFileIds }: GoogleDriveBrowserProps) {
  const [files, setFiles] = useState<GoogleDriveFile[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentFolderId, setCurrentFolderId] = useState<string | undefined>(undefined)
  const [folderStack, setFolderStack] = useState<Array<{ id: string | undefined; name: string }>>([
    { id: undefined, name: 'My Drive' }
  ])

  useEffect(() => {
    loadFiles()
  }, [currentFolderId])

  const loadFiles = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await integrationsApi.google.listFiles(currentFolderId)
      setFiles(response.data.files || [])
    } catch (err: any) {
      console.error('Error loading Google Drive files:', err)
      setError(err.response?.data?.detail || 'Failed to load files from Google Drive')
    } finally {
      setLoading(false)
    }
  }

  const handleFolderClick = (folder: GoogleDriveFile) => {
    if (folder.mimeType === 'application/vnd.google-apps.folder') {
      setCurrentFolderId(folder.id)
      setFolderStack([...folderStack, { id: folder.id, name: folder.name }])
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

  return (
    <div className="flex flex-col h-full">
      {/* Breadcrumbs */}
      <div className="flex items-center gap-1 px-4 py-2 border-b border-gray-200 text-sm text-gray-600 flex-shrink-0">
        {folderStack.map((folder, index) => (
          <div key={index} className="flex items-center gap-1">
            {index > 0 && <ChevronRight className="w-4 h-4" />}
            <button
              onClick={() => handleBreadcrumbClick(index)}
              className={`hover:text-gray-900 ${index === folderStack.length - 1 ? 'font-semibold text-gray-900' : ''}`}
            >
              {folder.name}
            </button>
          </div>
        ))}
      </div>

      {/* File List */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
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
        ) : (
          <div className="divide-y divide-gray-200">
            {files.map((file) => {
              const isSelected = selectedFileIds.includes(file.id)
              const canSelect = isSelectable(file.mimeType)
              
              return (
                <div
                  key={file.id}
                  className={`flex items-center gap-3 px-4 py-3 hover:bg-gray-50 ${
                    isFolder(file.mimeType) ? 'cursor-pointer' : ''
                  } ${isSelected ? 'bg-blue-50' : ''}`}
                  onClick={() => {
                    if (isFolder(file.mimeType)) {
                      handleFolderClick(file)
                    } else if (canSelect) {
                      handleFileToggle(file.id)
                    }
                  }}
                >
                  {isFolder(file.mimeType) ? (
                    <Folder className="w-5 h-5 text-blue-500 flex-shrink-0" />
                  ) : (
                    <File className="w-5 h-5 text-gray-500 flex-shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
                    {file.size && (
                      <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                    )}
                  </div>
                  {canSelect && (
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleFileToggle(file.id)}
                      onClick={(e) => e.stopPropagation()}
                      className="w-4 h-4 text-black border-gray-300 rounded focus:ring-black"
                    />
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Selected Files Count */}
      {selectedFileIds.length > 0 && (
        <div className="px-4 py-2 border-t border-gray-200 bg-gray-50 text-sm text-gray-600 flex-shrink-0">
          {selectedFileIds.length} file{selectedFileIds.length !== 1 ? 's' : ''} selected
        </div>
      )}
    </div>
  )
}


