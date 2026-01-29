import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9001'

// Create axios instance with default config
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout for all requests
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  try {
    // Get JWT token from localStorage
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
    if (token) {
      // Send JWT token in Authorization header
      config.headers.Authorization = `Bearer ${token}`
    }
  } catch (e) {
    // localStorage might not be available
  }
  return config
})

// Retry logic for network errors
const isNetworkError = (error: any): boolean => {
  return (
    !error?.response &&
    (error?.code === 'ERR_NETWORK' ||
      error?.code === 'ECONNABORTED' ||
      error?.code === 'ETIMEDOUT' ||
      error?.message === 'Network Error' ||
      error?.message?.includes('ERR_EMPTY_RESPONSE'))
  )
}

// Handle 401 errors - redirect to login
// Add retry logic for network errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error?.config

    // Retry logic for network errors (not 401/403/404)
    if (isNetworkError(error) && originalRequest) {
      const retryCount = originalRequest._retryCount || 0
      if (retryCount < 3) {
        originalRequest._retryCount = retryCount + 1

        // Exponential backoff: 1s, 2s, 4s
        const delay = Math.pow(2, originalRequest._retryCount - 1) * 1000
        await new Promise((resolve) => setTimeout(resolve, delay))

        return api(originalRequest)
      }
    }

    // If we get a 401, token is invalid - clear it
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token')
        // Redirect to login (root path) if we're not already there
        const currentPath = window.location.pathname
        if (currentPath !== '/' && currentPath !== '/login') {
          window.location.href = '/'
        }
      }
    }
    
    return Promise.reject(error)
  }
)

export default api

// Types
export interface Case {
  id: string | number  // UUID (string) or numeric ID
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
  created_at?: string
  view_count?: number
  error_message?: string
  extracted_text?: string
  is_archived?: boolean
  archived_at?: string
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

export interface CaseNote {
  id: number
  case_id: number
  user_id: number
  title: string
  content: string
  source_query_id?: number
  note_type: string
  privilege_tag?: string
  is_non_authoritative: boolean
  source_document_links?: string
  is_archived?: boolean
  archived_at?: string
  created_at: string
  updated_at?: string
}

export interface CaseNoteVersion {
  id: number
  note_id: number
  version_number: number
  title: string
  content: string
  privilege_tag?: string
  is_non_authoritative: boolean
  edited_by: number
  change_summary?: string
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

export const caseNotesApi = {
  list: (caseId: number) => api.get<CaseNote[]>(`/api/v1/cases/${caseId}/notes`),
  get: (caseId: number, noteId: number) => api.get<CaseNote>(`/api/v1/cases/${caseId}/notes/${noteId}`),
  create: (caseId: number, data: { title: string; content: string; source_query_id?: number; note_type?: string; privilege_tag?: string; is_non_authoritative?: boolean; source_document_links?: string }) =>
    api.post<CaseNote>(`/api/v1/cases/${caseId}/notes`, data),
  update: (caseId: number, noteId: number, data: { title?: string; content?: string; privilege_tag?: string; is_non_authoritative?: boolean; source_document_links?: string; change_summary?: string }) =>
    api.put<CaseNote>(`/api/v1/cases/${caseId}/notes/${noteId}`, data),
  archive: (caseId: number, noteId: number) =>
    api.post<CaseNote>(`/api/v1/cases/${caseId}/notes/${noteId}/archive`),
  getVersions: (caseId: number, noteId: number) =>
    api.get<CaseNoteVersion[]>(`/api/v1/cases/${caseId}/notes/${noteId}/versions`),
}

export const documentsApi = {
  list: (caseId: string | number) => api.get<Document[]>(`/api/v1/documents?case_id=${caseId}`),
  get: (id: string | number) => api.get<Document>(`/api/v1/documents/${id}`),
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
  delete: (id: string | number) => api.delete(`/api/v1/documents/${id}`),
  archive: (id: string | number) => api.post<Document>(`/api/v1/documents/${id}/archive`),
}

export const queriesApi = {
  create: (data: { question: string; case_id: number; query_type?: string; max_citations?: number }) =>
    api.post<Query>('/api/v1/queries', data),
  list: (caseId: number) => api.get<Query[]>(`/api/v1/queries?case_id=${caseId}`),
  get: (id: number) => api.get<Query>(`/api/v1/queries/${id}`),
}

export interface AppUser {
  id: number  // User ID (integer from PostgreSQL)
  email: string
  full_name?: string
  role: string  // super_admin, admin, attorney, paralegal
  title: string  // attorney, paralegal, finance, etc. (job title - required for access control)
  avatar_url?: string  // URL to profile avatar
  is_active: boolean
  tenant_id?: number
}

export const usersApi = {
  list: () => api.get<AppUser[]>('/api/v1/users'),
  create: (data: { email: string; password: string; full_name?: string; role: string; title: string }) =>
    api.post<AppUser>('/api/v1/users', data),
  update: (id: number, data: { full_name?: string; role?: string; title?: string; is_active?: boolean }) =>
    api.patch<AppUser>(`/api/v1/users/${id}`, data),
  delete: (id: number) => api.delete(`/api/v1/users/${id}`),
  deactivate: (id: number) => api.patch<AppUser>(`/api/v1/users/${id}/deactivate`),
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


