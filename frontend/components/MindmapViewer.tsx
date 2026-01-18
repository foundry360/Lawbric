'use client'

import { useMemo, useState, useEffect } from 'react'
import ReactFlow, { Node, Edge, Background, Controls, MiniMap, Position, Handle } from 'reactflow'
import 'reactflow/dist/style.css'
import { Document, Query, Case } from '@/lib/api'
import { FileText, MessageSquare, Briefcase, ChevronDown, ChevronRight, Plus, Minus, Folder } from 'lucide-react'

interface MindmapViewerProps {
  caseData: Case | null
  documents: Document[]
  queries: Query[]
  onDocumentSelect?: (documentId: number) => void
  onQuerySelect?: (queryId: number) => void
}

export default function MindmapViewer({
  caseData,
  documents,
  queries,
  onDocumentSelect,
  onQuerySelect,
}: MindmapViewerProps) {
  // Track document type visibility (collapsed by default)
  const [documentTypesVisible, setDocumentTypesVisible] = useState(false)
  // Track which document types are expanded (all collapsed by default)
  const [expandedDocumentTypes, setExpandedDocumentTypes] = useState<Set<string>>(new Set())
  // Track which documents have their queries expanded (all collapsed by default)
  const [expandedDocuments, setExpandedDocuments] = useState<Set<number>>(new Set())

  const toggleDocumentTypes = () => {
    setDocumentTypesVisible(prev => !prev)
  }

  const toggleDocumentType = (docType: string) => {
    setExpandedDocumentTypes(prev => {
      const newSet = new Set(prev)
      if (newSet.has(docType)) {
        newSet.delete(docType)
      } else {
        newSet.add(docType)
      }
      return newSet
    })
  }

  const toggleDocumentQueries = (docId: number) => {
    setExpandedDocuments(prev => {
      const newSet = new Set(prev)
      if (newSet.has(docId)) {
        newSet.delete(docId)
      } else {
        newSet.add(docId)
      }
      return newSet
    })
  }

  // Helper function to normalize file types to document type categories
  // Maps file types and metadata to semantic categories: Contract, Correspondence, Transcript
  const getDocumentTypeCategory = (fileType: string, filename?: string): string => {
    const lowerType = fileType.toLowerCase()
    const lowerFilename = (filename || '').toLowerCase()
    
    // Check filename patterns first for better categorization
    if (lowerFilename.includes('contract') || lowerFilename.includes('agreement') || lowerFilename.includes('lease')) {
      return 'Contract'
    }
    if (lowerFilename.includes('transcript') || lowerFilename.includes('deposition') || lowerFilename.includes('testimony')) {
      return 'Transcript'
    }
    if (lowerFilename.includes('email') || lowerFilename.includes('correspondence') || lowerFilename.includes('letter') || 
        lowerFilename.includes('memo') || lowerFilename.includes('message') || lowerType === 'msg' || lowerType === 'eml') {
      return 'Correspondence'
    }
    
    // Fallback to file type mapping
    const typeMap: Record<string, string> = {
      'email': 'Correspondence',
      'msg': 'Correspondence',
      'eml': 'Correspondence',
      'contract': 'Contract',
      'transcript': 'Transcript',
      'deposition': 'Transcript',
    }
    
    return typeMap[lowerType] || 'Correspondence' // Default to Correspondence for unknown types
  }

  // Group documents by type
  const documentsByType = useMemo(() => {
    const grouped: Record<string, Document[]> = {}
    documents.forEach(doc => {
      const type = getDocumentTypeCategory(doc.file_type, doc.original_filename)
      if (!grouped[type]) {
        grouped[type] = []
      }
      grouped[type].push(doc)
    })
    return grouped
  }, [documents])

  // Generate nodes and edges from documents and queries
  const { nodes, edges } = useMemo(() => {
    const nodeList: Node[] = []
    const edgeList: Edge[] = []
    
    // Early return if no case data
    if (!caseData) {
      return { nodes: nodeList, edges: edgeList }
    }

    // Calculate consistent spacing for nodes (center-to-center)
    const nodeSpacing = 120 // Consistent spacing between node centers
    const startY = 200
    
    // Standard node heights for center alignment calculations
    // Height accounts for: 16px padding (8px top + 8px bottom) + 2 lines of 10px text + icon + button
    const STANDARD_NODE_HEIGHT = 70 // Fixed height for all nodes to ensure center alignment
    
    // Calculate case node Y position - will be calculated after we know type positions
    let caseY = 400

    // Create primary case node on the far left (always expanded) - will be positioned after types are calculated
    if (caseData) {
      const textLength = caseData.name.length
      const estimatedWidth = Math.min(Math.max(textLength * 4, 120), 250)
      
      nodeList.push({
        id: 'case',
        type: 'default',
        position: { x: 50, y: caseY - STANDARD_NODE_HEIGHT / 2 }, // Position from center
        data: {
          label: (
            <div 
              className="flex items-start gap-1 p-2 relative justify-start cursor-pointer" 
              style={{ width: `${estimatedWidth + 32}px` }}
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                toggleDocumentTypes()
              }}
            >
              <Handle type="target" position={Position.Left} id="left" style={{ visibility: 'hidden' }} />
              <Briefcase className="w-4 h-4 text-white flex-shrink-0 mt-0.5" />
              <span className="text-[10px] font-bold text-white break-words leading-tight text-left flex-1" style={{ width: 'calc(100% - 56px)' }}>
                {caseData.name}
              </span>
              <div className="flex-shrink-0 p-0.5 bg-white rounded-full flex items-center justify-center self-center pointer-events-none" style={{ padding: '2px', margin: 0, width: '16px', height: '16px' }}>
                {documentTypesVisible ? (
                  <Minus className="w-3 h-3 text-black" />
                ) : (
                  <Plus className="w-3 h-3 text-black" />
                )}
              </div>
              <Handle type="source" position={Position.Right} id="right" style={{ visibility: 'hidden' }} />
            </div>
          ),
        },
          style: {
            background: '#000000',
            border: '2px solid #000000',
            borderRadius: '8px',
            padding: 0,
            width: `${estimatedWidth + 32}px`,
            height: `${STANDARD_NODE_HEIGHT}px`,
            minHeight: `${STANDARD_NODE_HEIGHT}px`,
            display: 'flex',
            alignItems: 'center',
          },
      })
    }

    // Create document type nodes (Level 2) - only if documentTypesVisible is true
    if (documentTypesVisible) {
      const documentTypes = Object.keys(documentsByType).sort()
      
      // First pass: Calculate center Y positions for all types and documents to ensure alignment
      // Each document type center aligns exactly with its first document center
      let currentCenterY = startY
      const typeCenterPositions = new Map<string, number>()
      
      documentTypes.forEach((docType) => {
        const typeDocuments = documentsByType[docType]
        const isTypeExpanded = expandedDocumentTypes.has(docType)
        
        // Type node center Y position - this will be the same as its first document center
        typeCenterPositions.set(docType, currentCenterY)
        
        // If expanded, additional documents space below the first one (which aligns with type)
        // So we need to account for that space when calculating next type's position
        if (isTypeExpanded && typeDocuments.length > 1) {
          // Space for additional documents beyond the first (which aligns with type)
          currentCenterY += (typeDocuments.length - 1) * 100
        }
        
        // Advance to next type center position (minimum spacing between type groups)
        currentCenterY += nodeSpacing
      })
      
      // Recalculate case node center Y to align with document types now that we have positions
      if (documentTypes.length > 0) {
        const firstTypeCenterY = typeCenterPositions.get(documentTypes[0]) || startY
        const lastTypeCenterY = typeCenterPositions.get(documentTypes[documentTypes.length - 1]) || startY
        caseY = (firstTypeCenterY + lastTypeCenterY) / 2
        
        // Update case node position (convert center to top-left)
        const caseNode = nodeList.find(n => n.id === 'case')
        if (caseNode) {
          caseNode.position.y = caseY - STANDARD_NODE_HEIGHT / 2
        }
      }
      
      documentTypes.forEach((docType, typeIndex) => {
        const typeDocuments = documentsByType[docType]
        const isTypeExpanded = expandedDocumentTypes.has(docType)
        const typeNodeId = `type-${docType}`
        const typeCenterY = typeCenterPositions.get(docType) || startY
        
        // Create document type node (convert center Y to top-left position)
        nodeList.push({
          id: typeNodeId,
          type: 'default',
          position: {
            x: 400,
            y: typeCenterY - STANDARD_NODE_HEIGHT / 2
          },
          data: {
            label: (
              <div 
                className="flex items-start gap-1 p-2 relative justify-start cursor-pointer"
                style={{ width: '180px' }}
                onClick={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  toggleDocumentType(docType)
                }}
              >
                <Handle type="target" position={Position.Left} id="left" style={{ visibility: 'hidden' }} />
                <Handle type="target" position={Position.Top} id="top" style={{ visibility: 'hidden' }} />
                <Folder className="w-3 h-3 text-gray-600 flex-shrink-0 mt-0.5" />
                <span className="text-[10px] font-semibold text-gray-900 break-words leading-tight text-left flex-1" style={{ width: 'calc(100% - 52px)' }}>
                  {docType}
                </span>
                <div className="flex-shrink-0 p-0.5 bg-white rounded-full flex items-center justify-center self-center pointer-events-none" style={{ padding: '2px', margin: 0, width: '16px', height: '16px' }}>
                  {isTypeExpanded ? (
                    <Minus className="w-3 h-3 text-black" />
                  ) : (
                    <Plus className="w-3 h-3 text-black" />
                  )}
                </div>
                <Handle type="source" position={Position.Right} id="right" style={{ visibility: 'hidden' }} />
                <Handle type="target" position={Position.Bottom} id="bottom" style={{ visibility: 'hidden' }} />
              </div>
            ),
          },
          style: {
            background: '#f9fafb',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            padding: 0,
            width: '180px',
            height: `${STANDARD_NODE_HEIGHT}px`,
            minHeight: `${STANDARD_NODE_HEIGHT}px`,
            display: 'flex',
            alignItems: 'center',
          },
        })

        // Create edge from case to document type
        edgeList.push({
          id: `edge-case-type-${docType}`,
          source: 'case',
          target: typeNodeId,
          sourceHandle: 'right',
          targetHandle: 'left',
          type: 'smoothstep',
          style: { stroke: '#d1d5db', strokeWidth: 1.5 },
        })

        // Create document nodes (Level 3) for this type - only if type is expanded
        if (isTypeExpanded) {
          const documentSpacing = 100 // Spacing between document centers within a type
          
          // First document center aligns with type node center, subsequent documents space below
          const firstDocCenterY = typeCenterY
          
          typeDocuments.forEach((doc, docIndex) => {
            const nodeId = `doc-${doc.id}`
            const isDocExpanded = expandedDocuments.has(doc.id)
            const textLength = doc.original_filename.length
            const estimatedWidth = Math.min(Math.max(textLength * 4, 100), 200)
            // Get queries that cite this document
            const docQueries = queries.filter(q => 
              q.citations && Array.isArray(q.citations) && 
              q.citations.some((c: any) => c.document_id === doc.id)
            )
            const hasQueries = docQueries.length > 0
            // First document center aligns with type center (same center Y), others space below
            const docCenterY = firstDocCenterY + docIndex * documentSpacing
            const docY = docCenterY - STANDARD_NODE_HEIGHT / 2 // Convert center to top-left
            
            nodeList.push({
              id: nodeId,
              type: 'default',
              position: { 
                x: 700, 
                y: docY
              },
          data: {
            label: (
              <div 
                className="flex items-start gap-1 p-2 relative justify-start cursor-pointer"
                style={{ width: `${estimatedWidth + 32}px` }}
                onClick={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  toggleDocumentQueries(doc.id)
                }}
              >
                <Handle type="target" position={Position.Left} id="left" style={{ visibility: 'hidden' }} />
                <Handle type="target" position={Position.Top} id="top" style={{ visibility: 'hidden' }} />
                <FileText className="w-3 h-3 text-gray-600 flex-shrink-0 mt-0.5" />
                <span className="text-[10px] font-medium text-gray-900 break-words leading-tight text-left flex-1" style={{ width: 'calc(100% - 52px)' }}>
                  {doc.original_filename}
                </span>
                <div className="flex-shrink-0 p-0.5 bg-white rounded-full flex items-center justify-center self-center pointer-events-none" style={{ padding: '2px', margin: 0, width: '16px', height: '16px' }}>
                  {isDocExpanded ? (
                    <Minus className="w-3 h-3 text-black" />
                  ) : (
                    <Plus className="w-3 h-3 text-black" />
                  )}
                </div>
                <Handle type="source" position={Position.Right} id="right" style={{ visibility: 'hidden' }} />
                <Handle type="target" position={Position.Bottom} id="bottom" style={{ visibility: 'hidden' }} />
              </div>
            ),
          },
          style: {
            background: '#ffffff',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            padding: 0,
            width: `${estimatedWidth + 32}px`,
            height: `${STANDARD_NODE_HEIGHT}px`,
            minHeight: `${STANDARD_NODE_HEIGHT}px`,
            display: 'flex',
            alignItems: 'center',
          },
        })

            // Create query nodes for this document (only if document is expanded)
            if (isDocExpanded && hasQueries) {
              docQueries.forEach((query, qIndex) => {
                const queryNodeId = `query-${query.id}`
                const textLength = query.question.length
                const estimatedQueryWidth = Math.min(Math.max(textLength * 4, 150), 250)
                
                // Query nodes position relative to document center
                const queryCenterY = docCenterY + Math.floor(qIndex / 3) * 100
                
                nodeList.push({
                  id: queryNodeId,
                  type: 'default',
                  position: { 
                    x: 1000 + (qIndex % 3) * 260, 
                    y: queryCenterY - STANDARD_NODE_HEIGHT / 2 // Convert center to top-left
                  },
              data: {
                label: (
                  <div className="flex items-start gap-1 p-2 relative justify-start" style={{ width: `${estimatedQueryWidth}px` }}>
                    <Handle type="source" position={Position.Left} id="left" style={{ visibility: 'hidden' }} />
                    <Handle type="source" position={Position.Top} id="top" style={{ visibility: 'hidden' }} />
                    <MessageSquare className="w-3 h-3 text-gray-600 flex-shrink-0 mt-0.5" />
                    <span className="text-[10px] font-medium text-gray-900 break-words text-left leading-tight" style={{ width: 'calc(100% - 16px)' }}>
                      {query.question}
                    </span>
                    <Handle type="source" position={Position.Right} id="right" style={{ visibility: 'hidden' }} />
                    <Handle type="source" position={Position.Bottom} id="bottom" style={{ visibility: 'hidden' }} />
                  </div>
                ),
              },
              style: {
                background: '#f3f4f6',
                border: '1px solid #d1d5db',
                borderRadius: '8px',
                padding: 0,
                width: `${estimatedQueryWidth}px`,
                height: `${STANDARD_NODE_HEIGHT}px`,
                minHeight: `${STANDARD_NODE_HEIGHT}px`,
                display: 'flex',
                alignItems: 'center',
              },
            })

            // Create edge from query to document
            edgeList.push({
              id: `edge-${query.id}-${doc.id}`,
              source: queryNodeId,
              target: nodeId,
              sourceHandle: 'top',
              targetHandle: 'bottom',
              type: 'smoothstep',
              animated: true,
              style: { stroke: '#6b7280', strokeWidth: 2 },
              label: query.citations?.find((c: any) => c.document_id === doc.id)?.page_number 
                ? `Page ${query.citations?.find((c: any) => c.document_id === doc.id)?.page_number}` 
                : undefined,
            })
          })
        }

            // Create edge from document type to document
            edgeList.push({
              id: `edge-type-${docType}-doc-${doc.id}`,
              source: typeNodeId,
              target: nodeId,
              sourceHandle: 'right',
              targetHandle: 'left',
              type: 'smoothstep',
              style: { stroke: '#e5e7eb', strokeWidth: 1.5 },
            })
          })
        }
      })
    }

    return { nodes: nodeList, edges: edgeList }
  }, [
    caseData, 
    documents, 
    queries, 
    documentTypesVisible, 
    Array.from(expandedDocumentTypes).sort().join(','), 
    Array.from(expandedDocuments).sort().join(','), 
    documentsByType
  ])

  const handleNodeClick = (event: React.MouseEvent, node: Node) => {
    if (node.id.startsWith('doc-')) {
      const docId = parseInt(node.id.replace('doc-', ''))
      if (onDocumentSelect) {
        onDocumentSelect(docId)
      }
    } else if (node.id.startsWith('query-')) {
      const queryId = parseInt(node.id.replace('query-', ''))
      if (onQuerySelect) {
        onQuerySelect(queryId)
      }
    }
  }

  return (
    <div className="h-full w-full relative">
      <style dangerouslySetInnerHTML={{
        __html: `
          .react-flow__handle {
            visibility: hidden !important;
            opacity: 0 !important;
            width: 0px !important;
            height: 0px !important;
          }
        `
      }} />
      <ReactFlow
        nodes={nodes || []}
        edges={edges || []}
        onNodeClick={handleNodeClick}
        fitView
        fitViewOptions={{ padding: 0.1, maxZoom: 0.9 }}
        defaultViewport={{ x: 0, y: 0, zoom: 0.9 }}
        attributionPosition="bottom-left"
      >
        <Background color="#f3f4f6" gap={16} />
        <Controls />
        <MiniMap 
          nodeColor={(node) => {
            if (node.id.startsWith('doc-')) return '#ffffff'
            return '#f3f4f6'
          }}
          maskColor="rgba(0, 0, 0, 0.1)"
        />
      </ReactFlow>
    </div>
  )
}

