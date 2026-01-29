'use client'

import { useRef, useEffect, useState } from 'react'
import { 
  Bold, 
  Italic, 
  Underline, 
  List, 
  ListOrdered, 
  Heading1, 
  Heading2, 
  Heading3,
  Undo,
  Redo
} from 'lucide-react'

interface RichTextEditorProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

export default function RichTextEditor({ 
  value, 
  onChange, 
  placeholder = 'Enter your note content...'
}: RichTextEditorProps) {
  const editorRef = useRef<HTMLDivElement>(null)
  const [isFocused, setIsFocused] = useState(false)

  // Update editor content when value prop changes
  useEffect(() => {
    if (editorRef.current && editorRef.current.innerHTML !== value) {
      editorRef.current.innerHTML = value || ''
    }
  }, [value])

  const handleInput = () => {
    if (editorRef.current) {
      onChange(editorRef.current.innerHTML)
    }
  }

  const execCommand = (command: string, value: string | null = null) => {
    document.execCommand(command, false, value || undefined)
    editorRef.current?.focus()
    handleInput()
  }

  const formatBlock = (tag: string) => {
    document.execCommand('formatBlock', false, tag)
    editorRef.current?.focus()
    handleInput()
  }

  const canUndo = () => {
    return document.queryCommandEnabled('undo')
  }

  const canRedo = () => {
    return document.queryCommandEnabled('redo')
  }

  const isActive = (command: string) => {
    return document.queryCommandState(command)
  }

  return (
    <div className="border border-gray-300 rounded-lg overflow-hidden bg-white">
      {/* Toolbar */}
      <div className="border-b border-gray-300 bg-gray-50 p-2 flex flex-wrap gap-1">
        <button
          type="button"
          onClick={() => execCommand('bold')}
          className={`px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-200 text-gray-900 bg-white ${
            isActive('bold') ? 'bg-gray-200' : ''
          }`}
          title="Bold"
        >
          <Bold className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={() => execCommand('italic')}
          className={`px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-200 text-gray-900 bg-white ${
            isActive('italic') ? 'bg-gray-200' : ''
          }`}
          title="Italic"
        >
          <Italic className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={() => execCommand('underline')}
          className={`px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-200 text-gray-900 bg-white ${
            isActive('underline') ? 'bg-gray-200' : ''
          }`}
          title="Underline"
        >
          <Underline className="w-4 h-4" />
        </button>
        <div className="w-px bg-gray-300 mx-1" />
        <button
          type="button"
          onClick={() => execCommand('insertUnorderedList')}
          className={`px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-200 text-gray-900 bg-white ${
            isActive('insertUnorderedList') ? 'bg-gray-200' : ''
          }`}
          title="Bullet List"
        >
          <List className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={() => execCommand('insertOrderedList')}
          className={`px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-200 text-gray-900 bg-white ${
            isActive('insertOrderedList') ? 'bg-gray-200' : ''
          }`}
          title="Numbered List"
        >
          <ListOrdered className="w-4 h-4" />
        </button>
        <div className="w-px bg-gray-300 mx-1" />
        <button
          type="button"
          onClick={() => formatBlock('h1')}
          className={`px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-200 text-gray-900 bg-white`}
          title="Heading 1"
        >
          <Heading1 className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={() => formatBlock('h2')}
          className={`px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-200 text-gray-900 bg-white`}
          title="Heading 2"
        >
          <Heading2 className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={() => formatBlock('h3')}
          className={`px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-200 text-gray-900 bg-white`}
          title="Heading 3"
        >
          <Heading3 className="w-4 h-4" />
        </button>
        <div className="w-px bg-gray-300 mx-1" />
        <button
          type="button"
          onClick={() => execCommand('undo')}
          disabled={!canUndo()}
          className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-200 text-gray-900 bg-white disabled:opacity-50"
          title="Undo"
        >
          <Undo className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={() => execCommand('redo')}
          disabled={!canRedo()}
          className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-200 text-gray-900 bg-white disabled:opacity-50"
          title="Redo"
        >
          <Redo className="w-4 h-4" />
        </button>
      </div>

      {/* Editor */}
      <div
        ref={editorRef}
        contentEditable
        onInput={handleInput}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        className={`min-h-[350px] max-h-[350px] overflow-y-auto p-4 text-gray-900 focus:outline-none ${
          isFocused ? 'ring-2 ring-black' : ''
        }`}
        style={{
          whiteSpace: 'pre-wrap',
          wordWrap: 'break-word',
        }}
        data-placeholder={placeholder}
        suppressContentEditableWarning
      />
    </div>
  )
}
