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

  if (processingDocuments.size === 0) {
    return null
  }
  return (
    <ProcessingStatusCard
      processingDocuments={processingDocuments}
      onStatusChange={handleStatusChange}
      onClose={handleClose}
    />
  )
}

