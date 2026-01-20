'use client'

import { useState, useEffect } from 'react'
import { Document } from '@/lib/api'
import ProcessingStatusCard from './ProcessingStatusCard'

interface ProcessingDocument {
  id: string | number
  document: Document | { id: string | number; status?: string; original_filename?: string; [key: string]: any }
  caseId: string | number
}

interface ProcessingStatusContainerProps {
  processingDocuments: Map<string | number, ProcessingDocument>
  onDocumentStatusChange?: (documentId: string | number, status: string) => void
}

export default function ProcessingStatusContainer({
  processingDocuments,
  onDocumentStatusChange
}: ProcessingStatusContainerProps) {
  useEffect(() => {
    console.log('ProcessingStatusContainer render, documents size:', processingDocuments.size)
    if (processingDocuments.size > 0) {
      console.log('Processing documents:', Array.from(processingDocuments.keys()))
    }
  }, [processingDocuments])
  
  const handleClose = () => {
    // Clear all processed/error documents, keep only processing ones
    processingDocuments.forEach((item, id) => {
      const status = item.document.status || 'processing'
      if (status === 'processed' || status === 'error') {
        if (onDocumentStatusChange) {
          onDocumentStatusChange(id, 'closed')
        }
      }
    })
  }

  const handleStatusChange = (documentId: string | number, status: string) => {
    if (onDocumentStatusChange) {
      onDocumentStatusChange(documentId, status)
    }
  }

  // Debug logging
  useEffect(() => {
    console.log('ProcessingStatusContainer: size check', processingDocuments.size)
    console.log('ProcessingStatusContainer: should render?', processingDocuments.size > 0)
  }, [processingDocuments])

  if (processingDocuments.size === 0) {
    console.log('ProcessingStatusContainer: Returning null (size is 0)')
    return null
  }

  console.log('ProcessingStatusContainer: Rendering ProcessingStatusCard')
  return (
    <ProcessingStatusCard
      processingDocuments={processingDocuments}
      onStatusChange={handleStatusChange}
      onClose={handleClose}
    />
  )
}

