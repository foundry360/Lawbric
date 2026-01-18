import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Create axios instance with default config
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token && !token.startsWith('dev-token-')) {
    config.headers.Authorization = `Bearer ${token}`
  }
  // For dev bypass, don't send auth header
  return config
})

// Handle dev bypass - return mock data when backend is unavailable
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const devBypass = localStorage.getItem('devBypass') === 'true'
    if (devBypass && (error.code === 'ECONNREFUSED' || error.message?.includes('Network Error') || !error.response)) {
      // Return mock data for development
      console.warn('Backend unavailable, using mock data')
      // Mark error as dev bypass so components can handle it
      error.isDevBypass = true
    }
    return Promise.reject(error)
  }
)

export default api

// Types
export interface Case {
  id: number
  name: string
  case_number?: string
  description?: string
  created_at: string
  updated_at?: string
  is_active: boolean
}

export interface Document {
  id: number
  case_id: number
  filename: string
  original_filename: string
  file_type: string
  file_size: number
  status: string
  page_count?: number
  word_count?: number
  bates_number?: string
  custodian?: string
  author?: string
  requires_ocr?: boolean
  uploaded_at: string
  view_count?: number
}

export interface Citation {
  document_id: number
  document_name: string
  page_number?: number
  paragraph_number?: number
  chunk_id?: number
  quoted_text: string
  confidence?: number
}

export interface Query {
  id: number
  question: string
  answer: string
  citations: Citation[]
  confidence_score?: {
    overall: number
    top_score: number
    num_sources: number
  }
  query_type?: string
  created_at: string
}

// API functions
export const casesApi = {
  list: () => api.get<Case[]>('/api/v1/cases'),
  get: (id: number) => api.get<Case>(`/api/v1/cases/${id}`),
  create: (data: { name: string; case_number?: string; description?: string }) =>
    api.post<Case>('/api/v1/cases', data),
  update: (id: number, data: Partial<Case>) =>
    api.put<Case>(`/api/v1/cases/${id}`, data),
  delete: (id: number) => api.delete(`/api/v1/cases/${id}`),
}

export const documentsApi = {
  list: (caseId: number) => api.get<Document[]>(`/api/v1/documents?case_id=${caseId}`),
  get: (id: number) => api.get<Document>(`/api/v1/documents/${id}`),
  upload: (caseId: number, file: File, metadata?: {
    bates_number?: string
    custodian?: string
    author?: string
    document_date?: string
    source?: string
  }) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('case_id', caseId.toString())
    if (metadata) {
      Object.entries(metadata).forEach(([key, value]) => {
        if (value) formData.append(key, value)
      })
    }
    return api.post<Document>('/api/v1/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  delete: (id: number) => api.delete(`/api/v1/documents/${id}`),
}

export const queriesApi = {
  create: (data: { question: string; case_id: number; query_type?: string; max_citations?: number }) =>
    api.post<Query>('/api/v1/queries', data),
  list: (caseId: number) => api.get<Query[]>(`/api/v1/queries?case_id=${caseId}`),
  get: (id: number) => api.get<Query>(`/api/v1/queries/${id}`),
}

