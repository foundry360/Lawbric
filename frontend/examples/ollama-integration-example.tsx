/**
 * Example: How to integrate Ollama service with your query panel
 * 
 * This file shows example code for connecting your existing ChatInterface
 * component to the Ollama service. You can adapt this to your needs.
 * 
 * IMPORTANT: This is example code only. Do not use this file directly.
 * Instead, integrate the patterns into your existing ChatInterface.tsx
 */

'use client'

import { useState } from 'react'

// Example 1: Simple fetch function
async function queryOllama(prompt: string): Promise<string> {
  const response = await fetch('http://localhost:8002/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ prompt }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP error! status: ${response.status}`)
  }

  const data = await response.json()
  return data.response
}

// Example 2: Component using Ollama service
export function ExampleOllamaQueryPanel() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim() || loading) return

    setLoading(true)
    setError(null)
    setAnswer('')

    try {
      const response = await queryOllama(question.trim())
      setAnswer(response)
      // Optionally clear the question after successful query
      // setQuestion('')
    } catch (err: any) {
      console.error('Failed to query Ollama:', err)
      setError(err.message || 'Failed to get response from Ollama')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Query Input */}
      <div className="border-t border-gray-200 p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question..."
            className="flex-1 px-4 py-2 border border-gray-200 rounded-lg focus:ring-0 focus:outline-none focus:border-gray-200 text-sm"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className={`px-4 py-2 rounded-lg transition-colors ${
              loading || !question.trim()
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-black text-white hover:bg-gray-800'
            }`}
          >
            {loading ? 'Sending...' : 'Send'}
          </button>
        </form>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg m-4">
          <p className="font-semibold">Error:</p>
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Answer Display */}
      {answer && (
        <div className="flex-1 overflow-y-auto p-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-semibold mb-2">Question:</h3>
            <p className="text-sm text-gray-700 mb-4">{question}</p>
            <h3 className="font-semibold mb-2">Answer:</h3>
            <div className="prose prose-sm max-w-none">
              <p className="whitespace-pre-wrap">{answer}</p>
            </div>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-gray-500">Waiting for response...</p>
        </div>
      )}
    </div>
  )
}

// Example 3: Integration with existing ChatInterface pattern
// This shows how you might modify your existing handleSubmit function:

/*
// In your ChatInterface.tsx, you could add an option to use Ollama:

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault()
  if (!question.trim() || loading) return

  setLoading(true)
  try {
    // Option 1: Use existing backend (current behavior)
    await queriesApi.create({
      question: question.trim(),
      case_id: caseId,
      max_citations: 5,
    })
    
    // Option 2: Use Ollama service (for testing)
    // const ollamaResponse = await queryOllama(question.trim())
    // console.log('Ollama response:', ollamaResponse)
    // You would need to handle displaying this response differently
    
    setQuestion('')
    onQuerySubmit()
  } catch (error: any) {
    console.error('Failed to submit query:', error)
    alert(error.message || 'Failed to submit query')
  } finally {
    setLoading(false)
  }
}
*/

