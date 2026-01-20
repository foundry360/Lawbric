'use client'

import { useState, useRef, useEffect } from 'react'
import { queriesApi, Query, Citation } from '@/lib/api'
import ReactMarkdown from 'react-markdown'
import { Send, FileText, MessageSquare } from 'lucide-react'

interface ChatInterfaceProps {
  caseId: number
  queries: Query[]
  onQuerySubmit: () => void
  selectedDocument: any
}

export default function ChatInterface({
  caseId,
  queries,
  onQuerySubmit,
  selectedDocument,
}: ChatInterfaceProps) {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [queries])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim() || loading) return

    setLoading(true)
    try {
      await queriesApi.create({
        question: question.trim(),
        case_id: caseId,
        max_citations: 5,
      })
      setQuestion('')
      onQuerySubmit()
    } catch (error: any) {
      console.error('Failed to submit query:', error)
      alert(error.response?.data?.detail || 'Failed to submit query')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Chat Header */}
      <div className="px-4 py-3">
        <h2 className="text-lg font-semibold">AI Assistant</h2>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {queries.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p className="mb-2">No queries yet</p>
            <p className="text-sm">Ask a question to get started</p>
          </div>
        ) : (
          queries.map((query) => (
            <div key={query.id} className="space-y-3">
              {/* Question */}
              <div className="bg-primary-50 rounded-lg p-3">
                <p className="font-medium text-gray-900">{query.question}</p>
              </div>

              {/* Answer */}
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown>{query.answer}</ReactMarkdown>
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

                {/* Confidence Score */}
                {query.confidence_score && (
                  <div className="mt-3 text-xs text-gray-500">
                    Confidence: {Math.round(query.confidence_score.overall * 100)}% • 
                    Sources: {query.confidence_score.num_sources}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about the documents..."
            className="flex-1 px-4 py-2 border border-gray-200 rounded-lg focus:ring-0 focus:outline-none focus:border-gray-200 text-sm placeholder:text-xs"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
              loading || !question.trim()
                ? 'bg-transparent text-gray-400 border border-gray-300 cursor-not-allowed'
                : 'bg-black text-white hover:bg-gray-800 border border-black'
            }`}
          >
            <Send className="w-5 h-5" />
            {loading ? 'Sending...' : 'Send'}
          </button>
        </form>
        <p className="text-xs text-gray-500 mt-2">
          Example: "What did the witness say about the incident on March 15th?"
        </p>
      </div>
    </div>
  )
}

