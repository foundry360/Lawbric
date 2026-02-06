'use client'

import { useState, useEffect } from 'react'
import { caseNotesApi, CaseNote, CaseNoteVersion } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { FileText, Plus, Edit, Trash2, Calendar, Search, X, User, File, Shield, AlertCircle, CheckCircle, MoreVertical, ChevronDown, ChevronUp, Clock, StickyNote } from 'lucide-react'
import { format } from 'date-fns'
import ReactMarkdown from 'react-markdown'
import RichTextEditor from './RichTextEditor'

interface CaseNotesViewerProps {
  caseId: number
  caseData: any
}

interface SourceDocumentLink {
  document_id: number
  document_name: string
  page_number?: number
  page_range?: string
}

export default function CaseNotesViewer({ caseId, caseData }: CaseNotesViewerProps) {
  const { user } = useAuth()
  const [notes, setNotes] = useState<CaseNote[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedNote, setSelectedNote] = useState<CaseNote | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [editContent, setEditContent] = useState('')
  const [editTitle, setEditTitle] = useState('')
  const [editPrivilegeTag, setEditPrivilegeTag] = useState('')
  const [editIsNonAuthoritative, setEditIsNonAuthoritative] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [showNewNoteModal, setShowNewNoteModal] = useState(false)
  const [newNoteTitle, setNewNoteTitle] = useState('')
  const [newNoteContent, setNewNoteContent] = useState('')
  const [newNotePrivilegeTag, setNewNotePrivilegeTag] = useState('')
  const [newNoteIsNonAuthoritative, setNewNoteIsNonAuthoritative] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [showMenu, setShowMenu] = useState(false)
  const [showArchiveModal, setShowArchiveModal] = useState(false)
  const [archiveConfirmText, setArchiveConfirmText] = useState('')
  const [isArchiving, setIsArchiving] = useState(false)
  const [showVersionHistory, setShowVersionHistory] = useState(false)
  const [versions, setVersions] = useState<CaseNoteVersion[]>([])
  const [loadingVersions, setLoadingVersions] = useState(false)
  const [showDetails, setShowDetails] = useState(true) // Default expanded
  const [showAudit, setShowAudit] = useState(false)

  useEffect(() => {
    loadNotes()
    // Reset selected note when case changes
    setSelectedNote(null)
  }, [caseId])

  // Auto-select first note when notes are loaded and no note is selected
  useEffect(() => {
    if (notes.length > 0 && !selectedNote && !loading) {
      const firstNote = notes[0]
      setSelectedNote(firstNote)
      setEditContent(firstNote.content)
      setEditTitle(firstNote.title || '')
      setEditPrivilegeTag(firstNote.privilege_tag || '')
      setEditIsNonAuthoritative(firstNote.is_non_authoritative || false)
    }
  }, [notes, selectedNote, loading])

  // Load version history when a note is selected
  useEffect(() => {
    if (selectedNote) {
      loadVersions(selectedNote.id)
      setShowVersionHistory(false) // Collapse accordion when switching notes
      setShowDetails(true) // Expand Details accordion by default
      setShowAudit(false) // Collapse Audit accordion by default
    } else {
      setVersions([])
    }
  }, [selectedNote?.id])

  // Listen for custom event to open new note modal from parent
  useEffect(() => {
    const handleOpenModal = () => {
      setShowNewNoteModal(true)
    }
    window.addEventListener('openNewNoteModal', handleOpenModal)
    return () => {
      window.removeEventListener('openNewNoteModal', handleOpenModal)
    }
  }, [])

  const loadNotes = async () => {
    try {
      setLoading(true)
      const response = await caseNotesApi.list(caseId)
      setNotes(response.data || [])
    } catch (error) {
      console.error('Failed to load case notes:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadVersions = async (noteId: number) => {
    try {
      setLoadingVersions(true)
      const response = await caseNotesApi.getVersions(caseId, noteId)
      setVersions(response.data || [])
    } catch (error) {
      console.error('Failed to load version history:', error)
      setVersions([])
    } finally {
      setLoadingVersions(false)
    }
  }

  const handleSaveNote = async () => {
    if (!selectedNote) return
    
    setIsSaving(true)
    try {
      await caseNotesApi.update(caseId, selectedNote.id, {
        title: editTitle || undefined,
        content: editContent,
        privilege_tag: editPrivilegeTag || undefined,
        is_non_authoritative: editIsNonAuthoritative
      })
      await loadNotes()
      // Reload the selected note
      const updatedNotes = await caseNotesApi.list(caseId)
      const updatedNote = updatedNotes.data.find((n: CaseNote) => n.id === selectedNote.id)
      if (updatedNote) {
        setSelectedNote(updatedNote)
        setEditPrivilegeTag(updatedNote.privilege_tag || '')
        setEditIsNonAuthoritative(updatedNote.is_non_authoritative || false)
      }
      setIsEditing(false)
    } catch (error) {
      console.error('Failed to save note:', error)
      alert('Failed to save note')
    } finally {
      setIsSaving(false)
    }
  }

  const handleArchiveNote = async () => {
    if (!selectedNote) return
    
    if (archiveConfirmText.toLowerCase() === 'archive') {
      setIsArchiving(true)
      try {
        await caseNotesApi.archive(caseId, selectedNote.id)
        setSelectedNote(null)
        setShowArchiveModal(false)
        setArchiveConfirmText('')
        await loadNotes()
      } catch (error: any) {
        console.error('Failed to archive note:', error)
        let errorMessage = 'Failed to archive note'
        if (error?.response?.data?.detail) {
          errorMessage = typeof error.response.data.detail === 'string' 
            ? error.response.data.detail 
            : JSON.stringify(error.response.data.detail)
        } else if (error?.message) {
          errorMessage = error.message
        }
        alert(errorMessage)
      } finally {
        setIsArchiving(false)
      }
    }
  }

  const handleCreateNote = async () => {
    if (!newNoteTitle.trim()) {
      alert('Please enter a note title')
      return
    }
    if (!newNoteContent.trim()) {
      alert('Please enter note content')
      return
    }
    
    setIsCreating(true)
    try {
      await caseNotesApi.create(caseId, {
        title: newNoteTitle.trim(),
        content: newNoteContent,
        note_type: 'manual',
        privilege_tag: newNotePrivilegeTag || undefined,
        is_non_authoritative: newNoteIsNonAuthoritative
      })
      setShowNewNoteModal(false)
      setNewNoteTitle('')
      setNewNoteContent('')
      setNewNotePrivilegeTag('')
      setNewNoteIsNonAuthoritative(false)
      await loadNotes()
    } catch (error) {
      console.error('Failed to create note:', error)
      alert('Failed to create note')
    } finally {
      setIsCreating(false)
    }
  }

  const filteredNotes = notes.filter(note => {
    if (!searchQuery.trim()) return true
    const query = searchQuery.toLowerCase()
    return (
      note.title?.toLowerCase().includes(query) ||
      note.content.toLowerCase().includes(query)
    )
  })

  const parseSourceDocumentLinks = (linksJson?: string): SourceDocumentLink[] | null => {
    if (!linksJson) return null
    try {
      return JSON.parse(linksJson)
    } catch {
      return null
    }
  }

  const isEditableByCurrentUser = (note: CaseNote): boolean => {
    return !!(user && note.user_id === user.id)
  }

  // Helper function to detect if content is HTML
  const isHTML = (str: string): boolean => {
    return /<[a-z][\s\S]*>/i.test(str)
  }

  const stripHTML = (html: string): string => {
    if (typeof window === 'undefined') {
      // Server-side: simple regex approach
      return html.replace(/<[^>]*>/g, '').replace(/&nbsp;/g, ' ').trim()
    }
    // Client-side: use DOM to parse and extract text
    const tmp = document.createElement('div')
    tmp.innerHTML = html
    return tmp.textContent || tmp.innerText || ''
  }


  return (
    <div className="h-full flex flex-col bg-white">
      {/* Three Column Layout: Notes List | Content | Metadata */}
      <div className="flex-1 flex overflow-hidden">
        {/* Notes List - Narrower */}
        <div className="w-1/4 border-r border-gray-200 flex flex-col bg-white">
          {/* Search Box */}
          <div className="p-4 border-b border-gray-200">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search notes..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black"
              />
            </div>
          </div>
          
          {/* Notes List Content */}
          <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="p-4 text-center text-gray-500">Loading notes...</div>
          ) : filteredNotes.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <FileText className="w-12 h-12 mx-auto mb-2 text-gray-400" />
              <p className="text-sm">
                {searchQuery ? 'No notes found' : 'No notes yet'}
              </p>
            </div>
          ) : (
            <div>
              {filteredNotes.map((note, index) => {
                const isSelected = selectedNote?.id === note.id
                return (
                  <div key={note.id} className={index > 0 ? 'border-t border-gray-300' : ''}>
                    <button
                      onClick={() => {
                        setSelectedNote(note)
                        setIsEditing(false)
                        setEditContent(note.content)
                        setEditTitle(note.title || '')
                        setEditPrivilegeTag(note.privilege_tag || '')
                        setEditIsNonAuthoritative(note.is_non_authoritative || false)
                      }}
                      className={`w-full text-left px-6 py-5 hover:bg-gray-50 transition-colors ${
                        isSelected ? 'bg-gray-100' : 'bg-white'
                      }`}
                    style={{
                      borderTopWidth: isSelected ? '2px' : '0px',
                      borderTopStyle: 'solid',
                      borderTopColor: isSelected ? '#0284c7' : 'transparent'
                    }}
                  >
                    <div className="flex items-start gap-3">
                      <StickyNote className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-gray-900 truncate text-sm">
                          {note.title}
                        </h3>
                        <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                          {isHTML(note.content) ? stripHTML(note.content) : note.content}
                        </p>
                        <div className="flex items-center gap-2 mt-2 text-xs text-gray-400">
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {format(new Date(note.created_at), 'MMM d')}
                          </span>
                          {note.note_type === 'ai_generated' && (
                            <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">
                              AI
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </button>
                  </div>
                )
              })}
            </div>
          )}
          </div>
        </div>

        {/* Note Content View - Middle Column */}
        <div className="w-1/2 border-r border-gray-200 overflow-y-auto p-6 bg-gray-50">
          {selectedNote ? (
            <div className="max-w-3xl mx-auto bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  {isEditing ? (
                    <input
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      placeholder="Note title..."
                      className="text-xl font-bold text-gray-900 w-full border-b border-gray-300 focus:outline-none focus:border-black pb-2 bg-white"
                    />
                  ) : (
                    <h2 className="text-xl font-bold text-gray-900">
                      {selectedNote.title}
                    </h2>
                  )}
                  <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                    <span>{format(new Date(selectedNote.created_at), 'MMMM d, yyyy')}</span>
                    {selectedNote.note_type === 'ai_generated' && (
                      <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded">
                        AI Generated
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                </div>
              </div>

              {isEditing ? (
                <div className="flex flex-col">
                  <div className="flex-1">
                  <RichTextEditor
                    value={editContent}
                    onChange={setEditContent}
                    placeholder="Note content..."
                  />
                  </div>
                  <div className="flex gap-2 justify-end pt-4 border-t border-gray-200 mt-4">
                    <button
                      onClick={() => {
                        setIsEditing(false)
                        setEditContent(selectedNote.content)
                        setEditTitle(selectedNote.title || '')
                        setEditPrivilegeTag(selectedNote.privilege_tag || '')
                        setEditIsNonAuthoritative(selectedNote.is_non_authoritative || false)
                      }}
                      className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-black text-sm"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSaveNote}
                      disabled={isSaving}
                      className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                    >
                      {isSaving ? 'Saving...' : 'Save'}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="prose prose-sm max-w-none prose-gray text-gray-900 text-sm">
                  {isHTML(selectedNote.content) ? (
                    <div 
                      className="text-sm note-content-display" 
                      dangerouslySetInnerHTML={{ __html: selectedNote.content }} 
                    />
                  ) : (
                    <div className="text-sm">
                      <ReactMarkdown>{selectedNote.content}</ReactMarkdown>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-500">
              <div className="text-center">
                <FileText className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                <p>Select a note to view</p>
              </div>
            </div>
          )}
        </div>

        {/* Metadata Column - Right Side */}
        <div className="w-1/4 overflow-y-auto p-6 bg-white">
          {selectedNote ? (
            <div className="space-y-6">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-gray-900">Note Provenance</h3>
                  {isEditableByCurrentUser(selectedNote) && (
                    <div className="relative">
                      <button
                        onClick={() => setShowMenu(!showMenu)}
                        className="p-1 hover:bg-gray-200 rounded transition-colors"
                      >
                        <MoreVertical className="w-4 h-4 text-gray-600" />
                      </button>
                      {showMenu && (
                        <>
                          <div
                            className="fixed inset-0 z-40"
                            onClick={() => setShowMenu(false)}
                          />
                          <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
                            <div className="py-1">
                              {isEditableByCurrentUser(selectedNote) && (
                                <button
                                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                  onClick={() => {
                                    setShowMenu(false)
                                    setIsEditing(true)
                                    setEditContent(selectedNote.content)
                                    setEditTitle(selectedNote.title || '')
                                    setEditPrivilegeTag(selectedNote.privilege_tag || '')
                                    setEditIsNonAuthoritative(selectedNote.is_non_authoritative || false)
                                  }}
                                >
                                  Edit Note
                                </button>
                              )}
                              {isEditableByCurrentUser(selectedNote) && (
                                <button
                                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                  onClick={() => {
                                    setShowMenu(false)
                                    setShowArchiveModal(true)
                                  }}
                                >
                                  Archive Note
                                </button>
                              )}
                            </div>
                          </div>
                        </>
                      )}
                    </div>
                  )}
                </div>

                {/* Details Accordion */}
                <div className="border-t border-gray-200">
                  <button
                    onClick={() => setShowDetails(!showDetails)}
                    className="w-full flex items-center justify-between py-4 hover:bg-gray-50 transition-colors"
                  >
                    <span className="text-xs font-bold text-gray-700">Details</span>
                    {showDetails ? (
                      <ChevronUp className="w-4 h-4 text-gray-500" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-gray-500" />
                    )}
                  </button>

                  {showDetails && (
                    <div className="pb-4 space-y-0">
                      {/* Case Association */}
                      <div className="py-4 border-b border-gray-200">
                        <div className="mb-2">
                          <span className="text-xs font-bold text-gray-700">Case Association</span>
                        </div>
                        <p className="text-xs text-gray-600">
                          {caseData?.name || `Case ID: ${selectedNote.case_id}`}
                        </p>
                      </div>

                      {/* Source Document Links */}
                      <div className="py-4 border-b border-gray-200">
                        <div className="mb-2">
                          <span className="text-xs font-bold text-gray-700">Source Document</span>
                        </div>
                        {selectedNote.source_document_links ? (
                          <div className="space-y-1">
                            {parseSourceDocumentLinks(selectedNote.source_document_links)?.map((link, idx) => (
                              <div key={idx} className="text-xs text-gray-600">
                                <div className="font-medium">{link.document_name}</div>
                                {link.page_number && (
                                  <div className="text-gray-500">Page {link.page_number}</div>
                                )}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-xs text-gray-500">No source documents linked</p>
                        )}
                      </div>

                      {/* Author / Editor Info */}
                      <div className="py-4">
                        <div className="mb-2">
                          <span className="text-xs font-bold text-gray-700">Author / Editor</span>
                        </div>
                        <p className="text-xs text-gray-600">
                          {user?.full_name || user?.email || `User ID: ${selectedNote.user_id}`}
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Audit Accordion */}
                <div className="border-t border-gray-200">
                  <button
                    onClick={() => setShowAudit(!showAudit)}
                    className="w-full flex items-center justify-between py-4 hover:bg-gray-50 transition-colors"
                  >
                    <span className="text-xs font-bold text-gray-700">Audit</span>
                    {showAudit ? (
                      <ChevronUp className="w-4 h-4 text-gray-500" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-gray-500" />
                    )}
                  </button>

                  {showAudit && (
                    <div className="pb-4 space-y-0">
                      {/* AI-Assisted Flag */}
                      <div className="py-4 border-b border-gray-200">
                        <div className="mb-2">
                          <span className="text-xs font-bold text-gray-700">AI-Assisted Flag</span>
                        </div>
                        <p className="text-xs text-gray-600">
                          {selectedNote.note_type === 'ai_generated' ? 'Yes' : 'No'}
                        </p>
                      </div>

                      {/* Created / Updated Timestamps */}
                      <div className="py-4 border-b border-gray-200">
                        <div className="mb-2">
                          <span className="text-xs font-bold text-gray-700">Timestamps</span>
                        </div>
                        <div className="space-y-1 text-xs text-gray-600">
                          <div>
                            <span className="font-medium">Created:</span>{' '}
                            {format(new Date(selectedNote.created_at), 'MMM d, yyyy HH:mm')}
                          </div>
                          {selectedNote.updated_at && (
                            <div>
                              <span className="font-medium">Updated:</span>{' '}
                              {format(new Date(selectedNote.updated_at), 'MMM d, yyyy HH:mm')}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Privilege / Sensitivity Tag */}
                      <div className="py-4 border-b border-gray-200">
                        <div className="mb-2">
                          <span className="text-xs font-bold text-gray-700">Privileged</span>
                        </div>
                        {isEditing ? (
                          <select
                            value={editPrivilegeTag}
                            onChange={(e) => setEditPrivilegeTag(e.target.value)}
                            className="w-full text-xs border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-black"
                          >
                            <option value="">None</option>
                            <option value="Public">Public</option>
                            <option value="Confidential">Confidential</option>
                            <option value="Attorney-Client">Attorney-Client</option>
                          </select>
                        ) : (
                          <p className="text-xs text-gray-600">
                            {selectedNote.privilege_tag || 'Not set'}
                          </p>
                        )}
                      </div>

                      {/* Editable by Author */}
                      <div className="py-4 border-b border-gray-200">
                        <div className="mb-2">
                          <span className="text-xs font-bold text-gray-700">Editable by Author</span>
                        </div>
                        <p className="text-xs text-gray-600">
                          {isEditableByCurrentUser(selectedNote) ? 'Yes' : 'No'}
                        </p>
                      </div>

                      {/* Non-Authoritative Marker */}
                      <div className="py-4">
                        <div className="mb-2">
                          <span className="text-xs font-bold text-gray-700">Non-Authoritative</span>
                        </div>
                        {isEditing ? (
                          <label className="flex items-center gap-2">
                            <input
                              type="checkbox"
                              checked={editIsNonAuthoritative}
                              onChange={(e) => setEditIsNonAuthoritative(e.target.checked)}
                              className="rounded border-gray-300"
                            />
                            <span className="text-xs text-gray-600">Working notes, not evidence</span>
                          </label>
                        ) : (
                          <p className="text-xs text-gray-600">
                            {selectedNote.is_non_authoritative ? 'Yes - Working notes' : 'No - Authoritative'}
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {/* Version History Accordion */}
                <div className="mt-6 border-t border-gray-200">
                  <button
                    onClick={() => setShowVersionHistory(!showVersionHistory)}
                    className="w-full flex items-center justify-between py-4 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-gray-700">Version History</span>
                      {versions.length > 0 && (
                        <span className="text-xs text-gray-500">({versions.length})</span>
                      )}
                    </div>
                    {showVersionHistory ? (
                      <ChevronUp className="w-4 h-4 text-gray-500" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-gray-500" />
                    )}
                  </button>

                  {showVersionHistory && (
                    <div className="pb-4 space-y-3">
                      {loadingVersions ? (
                        <div className="text-center py-4">
                          <p className="text-xs text-gray-500">Loading versions...</p>
                        </div>
                      ) : versions.length === 0 ? (
                        <div className="text-center py-4">
                          <p className="text-xs text-gray-500">No previous versions</p>
                        </div>
                      ) : (
                        versions.map((version) => (
                          <div 
                            key={version.id} 
                            className="bg-gray-50 rounded-lg p-3 border border-gray-200"
                          >
                            <div className="flex items-start justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-semibold text-gray-900">
                                  Version {version.version_number}
                                </span>
                                {version.is_non_authoritative && (
                                  <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded">
                                    Non-Auth
                                  </span>
                                )}
                              </div>
                              <span className="text-xs text-gray-500">
                                {format(new Date(version.created_at), 'MMM d, yyyy HH:mm')}
                              </span>
                            </div>
                            
                            <div className="space-y-2">
                              <div>
                                <p className="text-xs font-bold text-gray-700">Title:</p>
                                <p className="text-xs text-gray-600 mt-0.5">{version.title}</p>
                              </div>
                              
                              {version.change_summary && (
                                <div>
                                  <p className="text-xs font-bold text-gray-700">Changes:</p>
                                  <p className="text-xs text-gray-600 mt-0.5">{version.change_summary}</p>
                                </div>
                              )}
                              
                              {version.privilege_tag && (
                                <div>
                                  <p className="text-xs font-bold text-gray-700">Privilege:</p>
                                  <p className="text-xs text-gray-600 mt-0.5">{version.privilege_tag}</p>
                                </div>
                              )}
                              
                              <div className="pt-2 border-t border-gray-300">
                                <p className="text-xs font-bold text-gray-700 mb-1">Content Preview:</p>
                                <div className="text-xs text-gray-600 line-clamp-3">
                                  {(() => {
                                    const textContent = isHTML(version.content) 
                                      ? stripHTML(version.content) 
                                      : version.content
                                    return textContent.length > 150 
                                      ? textContent.substring(0, 150) + '...'
                                      : textContent
                                  })()}
                                </div>
                              </div>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-500 mt-8">
              <p className="text-sm">Select a note to view metadata</p>
            </div>
          )}
        </div>
      </div>

      {/* New Note Modal */}
      {showNewNoteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 bg-white">New Case Note</h3>
              <button
                onClick={() => {
                  setShowNewNoteModal(false)
                  setNewNoteTitle('')
                  setNewNoteContent('')
                  setNewNotePrivilegeTag('')
                  setNewNoteIsNonAuthoritative(false)
                }}
                className="text-gray-500 hover:text-gray-900"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto">
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Title *
                </label>
                <input
                  type="text"
                  value={newNoteTitle}
                  onChange={(e) => setNewNoteTitle(e.target.value)}
                  placeholder="Note title..."
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black bg-white text-gray-900"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Content *
                </label>
                <RichTextEditor
                  value={newNoteContent}
                  onChange={setNewNoteContent}
                  placeholder="Enter your note content..."
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Privilege Tag
                </label>
                <select
                  value={newNotePrivilegeTag}
                  onChange={(e) => setNewNotePrivilegeTag(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black bg-white text-gray-900"
                >
                  <option value="">None</option>
                  <option value="Public">Public</option>
                  <option value="Confidential">Confidential</option>
                  <option value="Attorney-Client">Attorney-Client</option>
                </select>
              </div>
              <div className="mb-4">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={newNoteIsNonAuthoritative}
                    onChange={(e) => setNewNoteIsNonAuthoritative(e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm text-gray-700">Mark as non-authoritative (working notes)</span>
                </label>
              </div>
            </div>
            <div className="flex gap-2 justify-end pt-4 border-t border-gray-200">
              <button
                onClick={() => {
                  setShowNewNoteModal(false)
                  setNewNoteTitle('')
                  setNewNoteContent('')
                  setNewNotePrivilegeTag('')
                  setNewNoteIsNonAuthoritative(false)
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-black"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateNote}
                disabled={isCreating || !newNoteTitle.trim() || !newNoteContent.trim()}
                className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isCreating ? 'Creating...' : 'Create Note'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Archive Confirmation Modal */}
      {showArchiveModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900">Archive Note</h2>
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
            <div className="mb-4">
              <p className="text-sm font-semibold text-gray-900 mb-2">
                This note is being archived.
              </p>
              <p className="text-sm text-gray-600 mb-3">
                Archived notes are immutable and will be stored on the blockchain when implemented. The note will be removed from the active list but can be retrieved for audit purposes.
              </p>
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-3">
                <p className="text-sm font-semibold text-red-800 mb-1">
                  ⚠️ This action is NOT reversible
                </p>
                <p className="text-xs text-red-700">
                  Once archived, this note cannot be unarchived or modified. Please confirm you want to proceed.
                </p>
              </div>
            </div>
            <p className="text-sm text-gray-700 mb-2 font-medium">
              Type <span className="font-mono bg-gray-100 px-2 py-1 rounded">archive</span> to confirm:
            </p>
            <input
              type="text"
              value={archiveConfirmText}
              onChange={(e) => setArchiveConfirmText(e.target.value)}
              placeholder="Type 'archive' to confirm"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black mb-4"
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
                onClick={handleArchiveNote}
                disabled={archiveConfirmText.toLowerCase() !== 'archive' || isArchiving}
                className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isArchiving ? 'Archiving...' : 'Archive Note'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
