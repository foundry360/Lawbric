'use client'

import { useState, useRef, useEffect } from 'react'
import { queriesApi, caseNotesApi, ollamaApi, Query, Citation, OllamaQueryResponse } from '@/lib/api'
import ReactMarkdown from 'react-markdown'
import { Send, FileText, MessageSquare, Pin, MoreVertical, ChevronsLeft, ChevronsRight } from 'lucide-react'

interface ChatInterfaceProps {
  caseId: number
  queries: Query[]
  onQuerySubmit: () => void
  onClearChat?: () => void
  selectedDocument: any
  isCollapsed?: boolean
  onToggleCollapse?: () => void
}

export default function ChatInterface({
  caseId,
  queries,
  onQuerySubmit,
  onClearChat,
  selectedDocument,
  isCollapsed,
  onToggleCollapse,
}: ChatInterfaceProps) {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [showMenu, setShowMenu] = useState(false)
  const [pendingQuery, setPendingQuery] = useState<{ question: string; id: string } | null>(null)
  const [localQueries, setLocalQueries] = useState<Query[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const formRef = useRef<HTMLFormElement>(null)
  
  // Combine database queries with local queries (view-only responses)
  const displayQueries = [...queries, ...localQueries]

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [displayQueries, pendingQuery])

  // Auto-resize textarea height
  useEffect(() => {
    if (textareaRef.current) {
      const textarea = textareaRef.current
      // Reset height to auto to get accurate scrollHeight
      textarea.style.height = 'auto'
      // Set height based on content, with min and max constraints
      const newHeight = Math.max(48, Math.min(textarea.scrollHeight, 200))
      textarea.style.height = `${newHeight}px`
    }
  }, [question])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim() || loading) return

    const questionText = question.trim()
    const tempId = `pending-${Date.now()}`
    
    // Immediately show the question with loading state
    setPendingQuery({ question: questionText, id: tempId })
    setQuestion('')
    setLoading(true)
    
    try {
      // Submit query via main API endpoint
      // The backend will call LLaMA-3.1 8B via Ollama service
      // How the Query panel input is transformed into LLaMA input:
      // - User query text is tokenized (PII removed) on the backend
      // - Optional documents array: Document excerpts are formatted and appended
      // - Optional facts array: Facts are formatted and appended
      // - System instructions are prepended on the backend
      // - Total prompt is truncated to fit within 2048-token context window
      const response = await queriesApi.create({
        question: questionText,
        case_id: caseId,
        max_citations: 5,
        document_id: selectedDocument?.id, // Include selected document ID if available
      })
      
      // Check if we got a valid response
      if (response?.data) {
        // Add response to local queries for immediate display (view-only, not saved to DB)
        const queryResponse: Query = response.data
        setLocalQueries(prev => [...prev, queryResponse])
        // Clear pending query
        setPendingQuery(null)
        // Don't reload from database - just display the response
      } else {
        // No response data - show error
        console.error('No response data in query response:', response)
        throw new Error('No response received from server')
      }
    } catch (error: any) {
      console.error('Failed to submit query:', error)
      console.error('Error details:', {
        message: error?.message,
        response: error?.response,
        data: error?.response?.data,
        status: error?.response?.status
      })
      // Remove pending query on error
      setPendingQuery(null)
      // Extract error message properly
      let errorMessage = 'Failed to submit query'
      if (error?.response?.data?.detail) {
        errorMessage = typeof error.response.data.detail === 'string' 
          ? error.response.data.detail 
          : JSON.stringify(error.response.data.detail)
      } else if (error?.message) {
        errorMessage = error.message
      } else if (error?.code === 'ECONNABORTED' || error?.code === 'ETIMEDOUT') {
        errorMessage = 'Request timed out. The query is taking longer than expected. Please try again.'
      } else if (typeof error === 'string') {
        errorMessage = error
      }
      alert(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleClearChat = () => {
    setShowMenu(false)
    // Clear local queries (view-only responses)
    setLocalQueries([])
    if (onClearChat) {
      onClearChat()
    }
  }

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (showMenu && !(event.target as Element).closest('.chat-menu-container')) {
        setShowMenu(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showMenu])

  const handleSaveAsCaseNote = async (query: Query) => {
    try {
      // Extract source document links from citations
      let sourceDocumentLinks = null
      if (query.citations && query.citations.length > 0) {
        const links = query.citations.map(citation => ({
          document_id: citation.document_id,
          document_name: citation.document_name,
          page_number: citation.page_number,
          page_range: citation.page_number ? `${citation.page_number}` : null
        }))
        sourceDocumentLinks = JSON.stringify(links)
      }
      
      await caseNotesApi.create(caseId, {
        title: query.question,
        content: query.answer,
        source_query_id: query.id,
        note_type: 'ai_generated',
        is_non_authoritative: true, // AI-generated notes are working notes
        source_document_links: sourceDocumentLinks || undefined
      })
      alert('Case note saved successfully!')
    } catch (error: any) {
      console.error('Failed to save case note:', error)
      let errorMessage = 'Failed to save case note'
      if (error?.response?.data?.detail) {
        errorMessage = typeof error.response.data.detail === 'string' 
          ? error.response.data.detail 
          : JSON.stringify(error.response.data.detail)
      } else if (error?.message) {
        errorMessage = error.message
      }
      alert(errorMessage)
    }
  }

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Chat Header */}
      <div className="px-4 py-3 flex items-center justify-between h-[52px]">
        <div className="flex items-center gap-2">
          {onToggleCollapse && !isCollapsed && (
            <button
              onClick={onToggleCollapse}
              className="p-1 hover:bg-gray-200 rounded transition-colors"
              title="Hide chat panel"
            >
              <ChevronsLeft className="w-4 h-4 text-gray-600" />
            </button>
          )}
          <h2 className="text-base font-bold text-gray-900 leading-none">Chat</h2>
        </div>
        <div className="relative chat-menu-container">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-1 hover:bg-gray-200 rounded transition-colors"
            aria-label="Chat menu"
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
                    onClick={handleClearChat}
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    Clear Chat
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 chat-messages-scroll">
        {displayQueries.length === 0 && !pendingQuery ? (
          <div className="text-center text-gray-500 mt-8">
            <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p className="mb-2">No queries yet</p>
            <p className="text-sm">Ask a question to get started</p>
          </div>
        ) : (
          <>
            {/* Show completed queries (oldest to newest) */}
            {[...displayQueries].sort((a, b) => {
              // Sort by created_at if available, otherwise by id
              const aDate = a.created_at ? new Date(a.created_at).getTime() : a.id
              const bDate = b.created_at ? new Date(b.created_at).getTime() : b.id
              return aDate - bDate
            }).map((query) => (
              <div key={query.id} className="space-y-3">
                {/* Question */}
                <div className="bg-primary-50 rounded-lg p-3">
                  <p className="font-medium text-gray-900 text-xs">{query.question}</p>
                </div>

                {/* Answer */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="prose prose-sm max-w-none text-xs">
                    <div className="text-gray-900 text-xs">
                      <ReactMarkdown>{query.answer}</ReactMarkdown>
                    </div>
                  </div>

                {/* Save as Case Note Button */}
                <div className="mt-4 flex justify-start">
                  <button
                    onClick={() => handleSaveAsCaseNote(query)}
                    className="px-2 py-1 text-xs bg-transparent text-gray-600 border border-gray-300 rounded hover:text-gray-900 hover:bg-gray-100 hover:border-gray-400 flex items-center gap-1.5 transition-colors"
                  >
                    <Pin className="w-3.5 h-3.5" />
                    Save as Case Note
                  </button>
                </div>

                {/* Citations */}
                {query.citations && query.citations.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <p className="text-sm font-semibold text-gray-700 mb-2">Sources:</p>
                    <div className="space-y-2">
                      {query.citations.map((citation: Citation, idx: number) => (
                        <div
                          key={idx}
                          className="bg-white rounded p-2 text-sm border border-gray-200 hover:border-primary-300 cursor-pointer"
                        >
                          <div className="flex items-start gap-2">
                            <FileText className="w-4 h-4 text-primary-600 mt-0.5 flex-shrink-0" />
                            <div className="flex-1">
                              <p className="font-medium text-gray-900">
                                {citation.document_name}
                              </p>
                              {citation.page_number && (
                                <p className="text-xs text-gray-600">
                                  Page {citation.page_number}
                                </p>
                              )}
                              <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                                "{citation.quoted_text}"
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

              </div>
            </div>
            ))}
            {/* Show pending query at the bottom if exists */}
            {pendingQuery && (
              <div key={pendingQuery.id} className="space-y-3">
                {/* Question */}
                <div className="bg-primary-50 rounded-lg p-3">
                  <p className="font-medium text-gray-900 text-xs">{pendingQuery.question}</p>
                </div>
                {/* Loading Answer */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '300ms' }}></div>
                    </div>
                    <span className="text-xs text-gray-500">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4 w-full box-border">
        <form ref={formRef} onSubmit={handleSubmit} className="relative w-full">
          <div className="relative flex-1 min-w-0" style={{ minWidth: 0, maxWidth: '100%', width: '100%' }}>
            <textarea
              ref={textareaRef}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                // Submit on Ctrl+Enter or Cmd+Enter, Enter creates new line
                if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                  e.preventDefault()
                  if (!loading && question.trim()) {
                    handleSubmit(e as any)
                  }
                }
              }}
              placeholder="Ask a question about the documents..."
              className="px-4 pr-12 py-2 border border-gray-200 rounded-lg focus:ring-0 focus:outline-none focus:border-gray-200 text-sm placeholder:text-xs resize-none min-h-[48px] max-h-[200px] w-full [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]"
              style={{ 
                wordWrap: 'break-word', 
                overflowWrap: 'break-word',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                boxSizing: 'border-box',
                overflowX: 'hidden',
                overflowY: 'auto',
                width: '100%',
                maxWidth: '100%',
                minWidth: 0,
                scrollbarWidth: 'none',
                msOverflowStyle: 'none'
              } as React.CSSProperties}
              disabled={loading}
              rows={1}
              wrap="soft"
            />
            <button
              type="submit"
              disabled={loading || !question.trim()}
              className={`absolute right-2.5 bottom-3.5 p-1.5 rounded-full border transition-colors ${
                loading || !question.trim()
                  ? 'text-gray-400 border-gray-300 cursor-not-allowed bg-transparent'
                  : 'text-white border-gray-300 bg-black hover:bg-gray-800'
              }`}
              aria-label="Send message"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

