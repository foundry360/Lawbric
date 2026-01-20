import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9000'

// Create axios instance with default config
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  try {
    // Get Supabase session token
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
    if (token) {
      // Only send Supabase tokens (not dev tokens)
      // Supabase tokens are JWT tokens, not user IDs
      if (!token.startsWith('dev-token-') && token.length > 50) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
  } catch (e) {
    // localStorage might not be available
  }
  return config
})

// Handle token refresh on 401 errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    // If we get a 401 and haven't already tried refreshing, try to refresh the token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      try {
        // Try to refresh Supabase session
        const { supabase } = await import('./supabase')
        const { getSession } = await import('./supabase-auth')
        
        const session = await getSession()
        if (session?.access_token) {
          // Update token in localStorage
          if (typeof window !== 'undefined') {
            localStorage.setItem('token', session.access_token)
          }
          
          // Update the authorization header and retry the request
          originalRequest.headers.Authorization = `Bearer ${session.access_token}`
          return api(originalRequest)
        }
      } catch (refreshError) {
        // Token refresh failed - user needs to log in again
        console.warn('Failed to refresh session token:', refreshError)
      }
    }
    
    try {
      const devBypass = typeof window !== 'undefined' && localStorage.getItem('devBypass') === 'true'
      if (devBypass && (error.code === 'ECONNREFUSED' || error.message?.includes('Network Error') || !error.response)) {
        // Return mock data for development
        console.warn('Backend unavailable, using mock data')
        // Mark error as dev bypass so components can handle it
        error.isDevBypass = true
      }
    } catch (e) {
      // localStorage might not be available
    }
    return Promise.reject(error)
  }
)

export default api

// Types
export interface Case {
  id: string | number  // UUID from Supabase (string) or legacy number
  name: string
  case_number?: string
  description?: string
  created_at: string
  updated_at?: string
  is_active: boolean
}

export interface Document {
  id: number | string  // Support both UUID (string) and integer IDs
  case_id: number | string
  filename: string
  original_filename: string
  file_type: string
  file_size: number
  status: string
  thumbnail_path?: string
  page_count?: number
  word_count?: number
  bates_number?: string
  custodian?: string
  author?: string
  requires_ocr?: boolean
  uploaded_at: string
  view_count?: number
  error_message?: string
  metadata?: {
    custodian?: string
    document_date?: string
    source?: string
    [key: string]: any
  }
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

export interface AppUser {
  id: string  // UUID from Supabase
  email: string
  full_name?: string
  role: string  // user or admin (permissions)
  title?: string  // attorney, paralegal, finance, etc. (job title)
  avatar_url?: string  // URL to profile avatar in Supabase storage
  is_active: boolean
}

export const usersApi = {
  list: () => api.get<AppUser[]>('/api/v1/users'),
  create: (data: { email: string; password: string; full_name?: string; role: string; title: string }) =>
    api.post<AppUser>('/api/v1/users', data),
  delete: (id: string) => api.delete(`/api/v1/users/${id}`),
  deactivate: (id: string) => api.patch<AppUser>(`/api/v1/users/${id}/deactivate`),
}

export interface GoogleDriveFile {
  id: string
  name: string
  mimeType: string
  size?: string
  modifiedTime?: string
  webViewLink?: string
  thumbnailLink?: string
  iconLink?: string
}

export interface IntegrationStatus {
  connected: boolean
}

export const integrationsApi = {
  google: {
    getAuthUrl: () => api.get<{ url: string }>('/api/v1/integrations/google/authorize'),
    getStatus: () => api.get<IntegrationStatus>('/api/v1/integrations/google/status'),
    getClientId: () => api.get<{ client_id: string }>('/api/v1/integrations/google/client-id'),
    getAccessToken: () => api.get<{ access_token: string }>('/api/v1/integrations/google/access-token'),
    disconnect: () => api.delete('/api/v1/integrations/google/disconnect'),
    callback: (code: string) => api.get<{ status: string; message: string }>('/api/v1/integrations/google/callback', {
      params: { code }
    }),
    listFiles: (folderId?: string, searchQuery?: string) => api.get<{ files: GoogleDriveFile[] }>('/api/v1/integrations/google/files', { 
      params: { 
        ...(folderId ? { folder_id: folderId } : {}),
        ...(searchQuery ? { search: searchQuery } : {})
      }
    }),
    listRecent: (searchQuery?: string) => api.get<{ files: GoogleDriveFile[] }>('/api/v1/integrations/google/files/recent', {
      params: searchQuery ? { search: searchQuery } : {}
    }),
    listShared: (searchQuery?: string) => api.get<{ files: GoogleDriveFile[] }>('/api/v1/integrations/google/files/shared', {
      params: searchQuery ? { search: searchQuery } : {}
    }),
    importFile: (caseId: string, fileId: string, metadata?: {
      bates_number?: string
      custodian?: string
      author?: string
      document_date?: string
      source?: string
    }) => api.post('/api/v1/integrations/google/import', null, {
      params: {
        case_id: caseId,
        file_id: fileId,
        ...(metadata || {})
      }
    }),
  }
}

